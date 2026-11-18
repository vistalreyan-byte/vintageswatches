import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import database as db

class TestServicesAndInvestors(unittest.TestCase):
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

    def test_01_services_crud_and_status_flow(self):
        self.login_admin()

        # 1. Create a service order
        add_resp = self.client.post('/services/add', data={
            'watch_id': 1,
            'customer_id': 1,
            'service_type': 'Restoration',
            'service_description': 'Full balance spring restoration and dial patina preservation',
            'service_date': '2026-03-01',
            'service_cost': 12500.00,
            'service_status': 'Pending'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        # Retrieve created service
        service = db.fetch_one("""
            SELECT * FROM watch_services 
            WHERE service_description LIKE '%Full balance spring restoration%'
            ORDER BY service_id DESC LIMIT 1
        """)
        self.assertIsNotNone(service)
        service_id = service['service_id']
        self.assertEqual(service['service_type'], 'Restoration')
        self.assertEqual(float(service['service_cost']), 12500.00)
        self.assertEqual(service['service_status'], 'Pending')

        # 2. Test API fetch
        api_resp = self.client.get(f"/api/service/{service_id}")
        self.assertEqual(api_resp.status_code, 200)
        s_data = api_resp.get_json()
        self.assertEqual(s_data['service_id'], service_id)
        self.assertEqual(s_data['service_cost'], 12500.00)

        # 3. Quick Status update
        st_resp = self.client.post(f"/services/status/{service_id}", data={
            'service_status': 'In Progress'
        }, follow_redirects=True)
        self.assertEqual(st_resp.status_code, 200)

        s_inprog = db.fetch_one("SELECT service_status FROM watch_services WHERE service_id = %s", (service_id,))
        self.assertEqual(s_inprog['service_status'], 'In Progress')

        # 4. Edit full service details
        edit_resp = self.client.post(f"/services/edit/{service_id}", data={
            'service_type': 'Restoration',
            'service_description': 'Completed balance spring restoration and casing polish',
            'service_date': '2026-03-05',
            'service_cost': 14000.00,
            'service_status': 'Completed'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        s_compl = db.fetch_one("SELECT * FROM watch_services WHERE service_id = %s", (service_id,))
        self.assertEqual(s_compl['service_status'], 'Completed')
        self.assertEqual(float(s_compl['service_cost']), 14000.00)

        # 5. Delete service
        del_resp = self.client.post(f"/services/delete/{service_id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)

        self.assertIsNone(db.fetch_one("SELECT * FROM watch_services WHERE service_id = %s", (service_id,)))

    def test_02_investors_crud_and_kpis(self):
        self.login_admin()

        # 1. Register new Investor
        add_resp = self.client.post('/investors/add', data={
            'investor_name': 'Alexander Sterling',
            'contact_number': '09175556677',
            'email': 'alexander.sterling@horologycapital.com',
            'investment_amount': 2500000.00,
            'investment_date': '2026-02-15',
            'investment_status': 'Active'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        # Retrieve created investor
        investor = db.fetch_one("SELECT * FROM investors WHERE email = 'alexander.sterling@horologycapital.com'")
        self.assertIsNotNone(investor)
        inv_id = investor['investor_id']
        self.assertEqual(float(investor['investment_amount']), 2500000.00)
        self.assertEqual(investor['investment_status'], 'Active')

        # 2. Test API fetch
        api_resp = self.client.get(f"/api/investor/{inv_id}")
        self.assertEqual(api_resp.status_code, 200)
        inv_json = api_resp.get_json()
        self.assertEqual(inv_json['investor_name'], 'Alexander Sterling')
        self.assertEqual(inv_json['investment_amount'], 2500000.00)

        # 3. Edit Investor
        edit_resp = self.client.post(f"/investors/edit/{inv_id}", data={
            'investor_name': 'Sir Alexander Sterling, Jr.',
            'contact_number': '09175556677',
            'email': 'alexander.sterling@horologycapital.com',
            'investment_amount': 3000000.00,
            'investment_date': '2026-02-15',
            'investment_status': 'Active'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        inv_updated = db.fetch_one("SELECT * FROM investors WHERE investor_id = %s", (inv_id,))
        self.assertEqual(inv_updated['investor_name'], 'Sir Alexander Sterling, Jr.')
        self.assertEqual(float(inv_updated['investment_amount']), 3000000.00)

        # 4. Verify Investors page KPI calculation
        page_resp = self.client.get('/investors')
        self.assertEqual(page_resp.status_code, 200)
        self.assertIn(b"Alexander Sterling", page_resp.data)

        # 5. Delete Investor
        del_resp = self.client.post(f"/investors/delete/{inv_id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)

        self.assertIsNone(db.fetch_one("SELECT * FROM investors WHERE investor_id = %s", (inv_id,)))

if __name__ == '__main__':
    unittest.main()
