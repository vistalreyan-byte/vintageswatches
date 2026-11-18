import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import database as db

class TestCartAndCheckoutFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        # Create a dedicated temporary watch with 2 units in stock for cart tests
        self.watch_id = db.execute_query("""
            INSERT INTO watches (brand, model, reference_number, watch_type, movement, 
                                 condition_status, purchase_price, selling_price, year_aquired, status, description)
            VALUES ('CartTestRolex', 'Daytona Black', 'REF-CART-888', 'Chronograph', 'Automatic', 
                    'Mint', 200000.00, 300000.00, '2026', 'Available', 'Cart Test Watch')
        """)
        self.inv_id = db.execute_query("""
            INSERT INTO inventory (watch_id, quantity, location, date_added, inventory_status)
            VALUES (%s, 2, 'Main Vault', CURDATE(), 'In Stock')
        """, (self.watch_id,))
        self.test_email = "shopper_test_2026@gmail.com"

    def tearDown(self):
        # Clean up any transactions or customers created during the test
        db.execute_query("DELETE FROM `sale items` WHERE watch_id = %s", (self.watch_id,))
        # Find any sales linked to test email
        cust = db.fetch_one("SELECT customer_id FROM customer WHERE email = %s", (self.test_email,))
        if cust:
            db.execute_query("DELETE FROM `sale items` WHERE sale_id IN (SELECT sale_id FROM sales WHERE customer_id = %s)", (cust['customer_id'],))
            db.execute_query("DELETE FROM sales WHERE customer_id = %s", (cust['customer_id'],))
            db.execute_query("DELETE FROM customer WHERE customer_id = %s", (cust['customer_id'],))

        db.execute_query("DELETE FROM inventory WHERE watch_id = %s", (self.watch_id,))
        db.execute_query("DELETE FROM watches WHERE watch_id = %s", (self.watch_id,))

    def test_01_add_to_cart_and_stock_limits(self):
        with self.client as c:
            # 1. Add 1 item
            resp = c.post(f"/cart/add/{self.watch_id}", data={'quantity': 1}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Check cart session
            with c.session_transaction() as sess:
                self.assertIn('cart', sess)
                self.assertEqual(sess['cart'].get(str(self.watch_id)), 1)

            # 2. Add 5 items (exceeds stock of 2) -> should clamp to 2
            resp2 = c.post(f"/cart/add/{self.watch_id}", data={'quantity': 5}, follow_redirects=True)
            self.assertEqual(resp2.status_code, 200)

            with c.session_transaction() as sess:
                self.assertEqual(sess['cart'].get(str(self.watch_id)), 2)

    def test_02_update_and_remove_cart_items(self):
        with self.client as c:
            # Add initial
            c.post(f"/cart/add/{self.watch_id}", data={'quantity': 2}, follow_redirects=True)

            # Update quantity to 1
            up_resp = c.post(f"/cart/update/{self.watch_id}", data={'quantity': 1}, follow_redirects=True)
            self.assertEqual(up_resp.status_code, 200)

            with c.session_transaction() as sess:
                self.assertEqual(sess['cart'].get(str(self.watch_id)), 1)

            # Remove item
            rem_resp = c.post(f"/cart/remove/{self.watch_id}", follow_redirects=True)
            self.assertEqual(rem_resp.status_code, 200)

            with c.session_transaction() as sess:
                self.assertNotIn(str(self.watch_id), sess.get('cart', {}))

    def test_03_checkout_validation_and_successful_transaction(self):
        with self.client as c:
            # Put 2 items in cart (all available stock)
            c.post(f"/cart/add/{self.watch_id}", data={'quantity': 2}, follow_redirects=True)

            # Test validation failure (missing required customer fields)
            bad_checkout = c.post('/checkout/process', data={
                'full_name': 'Test Shopper',
                'email': '',  # missing email
                'contact_number': '09123456789',
                'address': 'Manila',
                'payment_method': 'Bank Transfer'
            }, follow_redirects=True)
            self.assertEqual(bad_checkout.status_code, 200)
            # Ensure no sale was created yet
            self.assertIsNone(db.fetch_one("SELECT * FROM customer WHERE email = %s", (self.test_email,)))

            # Test successful checkout
            good_checkout = c.post('/checkout/process', data={
                'full_name': 'Test Certified Shopper',
                'email': self.test_email,
                'contact_number': '09187654321',
                'address': 'Bonifacio Global City, Taguig',
                'payment_method': 'Credit Card'
            }, follow_redirects=True)
            self.assertEqual(good_checkout.status_code, 200)

            # 1. Customer created
            cust = db.fetch_one("SELECT * FROM customer WHERE email = %s", (self.test_email,))
            self.assertIsNotNone(cust)
            cust_id = cust['customer_id']

            # 2. Sale created
            sale = db.fetch_one("SELECT * FROM sales WHERE customer_id = %s ORDER BY sale_id DESC LIMIT 1", (cust_id,))
            self.assertIsNotNone(sale)
            self.assertEqual(float(sale['total_amount']), 600000.00) # 2 * 300,000.00
            self.assertEqual(sale['paymaent_method'], 'Credit Card')
            self.assertEqual(sale['payment_status'], 'Paid')
            sale_id = sale['sale_id']

            # 3. Sale item record created
            sale_item = db.fetch_one("SELECT * FROM `sale items` WHERE sale_id = %s AND watch_id = %s", (sale_id, self.watch_id))
            self.assertIsNotNone(sale_item)
            self.assertEqual(sale_item['quantity'], 2)
            self.assertEqual(float(sale_item['unit_price']), 300000.00)
            self.assertEqual(float(sale_item['subtotal']), 600000.00)

            # 4. Inventory deducted to 0 & status updated
            inv = db.fetch_one("SELECT * FROM inventory WHERE watch_id = %s", (self.watch_id,))
            self.assertEqual(inv['quantity'], 0)
            self.assertEqual(inv['inventory_status'], 'Out of Stock')

            # 5. Watch marked Sold Out
            watch_after = db.fetch_one("SELECT status FROM watches WHERE watch_id = %s", (self.watch_id,))
            self.assertEqual(watch_after['status'], 'Sold Out')

            # 6. Cart is emptied after checkout
            with c.session_transaction() as sess:
                self.assertNotIn('cart', sess)

    def test_04_transaction_rollback_on_stock_error(self):
        # Test atomic rollback callback behavior
        def failing_transaction(cursor):
            cursor.execute("INSERT INTO customer (full_name, contact_number, email, address, customer_type, date_registered) VALUES ('Fail Tester', '09000000000', 'fail_roll@test.com', 'Nowhere', 'Regular', CURDATE())")
            # Trigger intentional error
            raise RuntimeError("Simulated database failure during order processing")

        result = db.execute_transaction(failing_transaction)
        self.assertFalse(result, "Transaction should fail and return False")

        # Verify customer was rolled back
        check_cust = db.fetch_one("SELECT * FROM customer WHERE email = 'fail_roll@test.com'")
        self.assertIsNone(check_cust, "Failed transaction changes must be rolled back completely")

if __name__ == '__main__':
    unittest.main()
