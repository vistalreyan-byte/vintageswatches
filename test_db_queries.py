import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import database as db

class TestDatabaseQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def login_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['full_name'] = 'Reyan Vistal'
            sess['role'] = 'Administrator'

    # 1. Test database reads on all core tables
    def test_01_core_table_reads(self):
        tables = ['customer', 'inventory', 'investors', '`sale items`', 'sales', 'user', 'watch_services', 'watches']
        for tbl in tables:
            rows = db.fetch_all(f"SELECT * FROM {tbl} LIMIT 5")
            self.assertIsInstance(rows, list, f"Failed to fetch rows from {tbl}")

    # 2. Test Watches CRUD & Foreign Key Safeguards
    def test_02_watches_crud_and_safeguards(self):
        self.login_admin()

        # Create
        brand = "TestBrandOmega"
        model = "Speedmaster Prototype"
        ref = "TEST-REF-999"
        watch_id = db.execute_query("""
            INSERT INTO watches (brand, model, reference_number, watch_type, movement, 
                                 condition_status, purchase_price, selling_price, year_aquired, status, description)
            VALUES (%s, %s, %s, 'Chronograph', 'Manual Wind', 'Mint', 50000.00, 75000.00, '2026', 'Available', 'Test watch description')
        """, (brand, model, ref))
        self.assertTrue(watch_id, "Failed to insert test watch")

        # Read via API
        resp = self.client.get(f"/api/watch/{watch_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['brand'], brand)
        self.assertEqual(data['reference_number'], ref)

        # Edit via route
        edit_resp = self.client.post(f"/watches/edit/{watch_id}", data={
            'brand': brand,
            'model': 'Speedmaster Prototype Updated',
            'reference_number': ref,
            'watch_type': 'Chronograph',
            'movement': 'Manual Wind',
            'condition_status': 'Excellent',
            'purchase_price': 55000.00,
            'selling_price': 80000.00,
            'year_aquired': '2026',
            'status': 'Available',
            'description': 'Updated test description'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        updated_watch = db.fetch_one("SELECT * FROM watches WHERE watch_id = %s", (watch_id,))
        self.assertEqual(updated_watch['model'], 'Speedmaster Prototype Updated')
        self.assertEqual(float(updated_watch['selling_price']), 80000.00)

        # Safeguard test: simulate a sale item attached to watch
        # Create temp customer & sale
        cust_id = db.execute_query("INSERT INTO customer (full_name, contact_number, email, address, customer_type, date_registered) VALUES ('Test Buyer', '09111111111', 'temp_buyer@test.com', 'Cebu', 'Regular', CURDATE())")
        sale_id = db.execute_query("INSERT INTO sales (customer_id, user_id, sale_date, total_amount, paymaent_method, payment_status) VALUES (%s, 1, CURDATE(), 80000.00, 'Cash', 'Paid')", (cust_id,))
        sale_item_id = db.execute_query("INSERT INTO `sale items` (sale_id, watch_id, quantity, unit_price, subtotal) VALUES (%s, %s, 1, 80000.00, 80000.00)", (sale_id, watch_id))

        # Attempt delete - should safeguard and mark Discontinued instead of breaking foreign keys
        del_resp = self.client.post(f"/watches/delete/{watch_id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        safe_watch = db.fetch_one("SELECT status FROM watches WHERE watch_id = %s", (watch_id,))
        self.assertEqual(safe_watch['status'], 'Discontinued')

        # Cleanup safeguard test records
        db.execute_query("DELETE FROM `sale items` WHERE sale_item_id = %s", (sale_item_id,))
        db.execute_query("DELETE FROM sales WHERE sale_id = %s", (sale_id,))
        db.execute_query("DELETE FROM customer WHERE customer_id = %s", (cust_id,))
        db.execute_query("DELETE FROM watches WHERE watch_id = %s", (watch_id,))

        # Verify completely deleted
        deleted_check = db.fetch_one("SELECT * FROM watches WHERE watch_id = %s", (watch_id,))
        self.assertIsNone(deleted_check)

    # 3. Test Inventory CRUD
    def test_03_inventory_crud(self):
        self.login_admin()

        # Temporary watch for inventory lot
        w_id = db.execute_query("""
            INSERT INTO watches (brand, model, reference_number, watch_type, movement, 
                                 condition_status, purchase_price, selling_price, year_aquired, status)
            VALUES ('InvBrand', 'InvModel', 'INV-REF-001', 'Diver', 'Automatic', 'Mint', 10000.00, 15000.00, '2026', 'Available')
        """)

        # Add Inventory via route
        add_resp = self.client.post('/inventory/add', data={
            'watch_id': w_id,
            'quantity': 5,
            'location': 'Vault B-12'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        inv_record = db.fetch_one("SELECT * FROM inventory WHERE watch_id = %s", (w_id,))
        self.assertIsNotNone(inv_record)
        self.assertEqual(inv_record['quantity'], 5)
        self.assertEqual(inv_record['location'], 'Vault B-12')
        self.assertEqual(inv_record['inventory_status'], 'In Stock')
        inv_id = inv_record['inventory_id']

        # API fetch
        api_resp = self.client.get(f"/api/inventory/{inv_id}")
        self.assertEqual(api_resp.status_code, 200)
        self.assertEqual(api_resp.get_json()['quantity'], 5)

        # Edit Inventory via route
        edit_resp = self.client.post(f"/inventory/edit/{inv_id}", data={
            'quantity': 2,
            'location': 'Display Showcase 1',
            'inventory_status': 'In Stock'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        updated_inv = db.fetch_one("SELECT * FROM inventory WHERE inventory_id = %s", (inv_id,))
        self.assertEqual(updated_inv['quantity'], 2)
        self.assertEqual(updated_inv['location'], 'Display Showcase 1')

        # Delete Inventory
        del_resp = self.client.post(f"/inventory/delete/{inv_id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)

        # Cleanup
        db.execute_query("DELETE FROM inventory WHERE inventory_id = %s", (inv_id,))
        db.execute_query("DELETE FROM watches WHERE watch_id = %s", (w_id,))

    # 4. Test Customer CRUD & History
    def test_04_customers_crud(self):
        self.login_admin()

        test_email = "unique_tester_99@gmail.com"
        # Add customer
        add_resp = self.client.post('/customers/add', data={
            'full_name': 'Test Juan Luna',
            'contact_number': '09199998888',
            'email': test_email,
            'address': 'Davao City',
            'customer_type': 'VIP'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        cust = db.fetch_one("SELECT * FROM customer WHERE email = %s", (test_email,))
        self.assertIsNotNone(cust)
        cust_id = cust['customer_id']

        # Read via API (contains orders and services history)
        api_resp = self.client.get(f"/api/customer/{cust_id}")
        self.assertEqual(api_resp.status_code, 200)
        cust_json = api_resp.get_json()
        self.assertEqual(cust_json['full_name'], 'Test Juan Luna')
        self.assertIn('orders', cust_json)
        self.assertIn('services', cust_json)

        # Edit customer
        edit_resp = self.client.post(f"/customers/edit/{cust_id}", data={
            'full_name': 'Test Juan Luna Updated',
            'contact_number': '09199998888',
            'email': test_email,
            'address': 'Tagum City',
            'customer_type': 'VIP'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        # Delete customer
        del_resp = self.client.post(f"/customers/delete/{cust_id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)

        # Verify deletion
        self.assertIsNone(db.fetch_one("SELECT * FROM customer WHERE customer_id = %s", (cust_id,)))

    # 5. Test Users CRUD (Admin-only)
    def test_05_users_crud_and_security(self):
        self.login_admin()

        temp_uname = "test_staff_user_xyz"
        add_resp = self.client.post('/users/add', data={
            'full_name': 'Test Staff Member',
            'user_name': temp_uname,
            'password': 'Password123!',
            'role': 'Sales Staff',
            'email': 'staff_xyz@vintagewatches.com',
            'status': 'Active'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        user = db.fetch_one("SELECT * FROM user WHERE user_name = %s", (temp_uname,))
        self.assertIsNotNone(user)
        u_id = user['user_id']

        # Toggle status
        tog_resp = self.client.post(f"/users/toggle-status/{u_id}", follow_redirects=True)
        self.assertEqual(tog_resp.status_code, 200)
        user_inact = db.fetch_one("SELECT status FROM user WHERE user_id = %s", (u_id,))
        self.assertEqual(user_inact['status'], 'Inactive')

        # Edit user
        edit_resp = self.client.post(f"/users/edit/{u_id}", data={
            'full_name': 'Test Staff Member Renamed',
            'role': 'Sales Staff',
            'email': 'staff_xyz_new@vintagewatches.com',
            'status': 'Active',
            'password': ''
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        # Delete user
        del_resp = self.client.post(f"/users/delete/{u_id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(db.fetch_one("SELECT * FROM user WHERE user_id = %s", (u_id,)))

if __name__ == '__main__':
    unittest.main()
