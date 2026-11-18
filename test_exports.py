import unittest
import sys
import os
import csv
import io
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

class TestReportExports(unittest.TestCase):
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

    def test_01_export_sales_csv(self):
        self.login_admin()
        resp = self.client.get('/reports/export/sales-csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn('attachment;filename=sales_report_', resp.headers.get('Content-Disposition', ''))

        csv_text = resp.data.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)

        self.assertGreaterEqual(len(rows), 1, "CSV should contain at least headers")
        expected_headers = ['Sale ID', 'Date', 'Customer Name', 'Handled By', 'Payment Method', 'Payment Status', 'Total Amount (PHP)']
        self.assertEqual(rows[0], expected_headers)

        # Verify sample data rows if transactions exist
        if len(rows) > 1:
            first_data_row = rows[1]
            self.assertEqual(len(first_data_row), len(expected_headers))
            self.assertTrue(first_data_row[0].startswith('#'))

    def test_02_export_inventory_csv(self):
        self.login_admin()
        resp = self.client.get('/reports/export/inventory-csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn('attachment;filename=inventory_report_', resp.headers.get('Content-Disposition', ''))

        csv_text = resp.data.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)

        self.assertGreaterEqual(len(rows), 1, "CSV should contain at least headers")
        expected_headers = ['Inventory ID', 'Brand', 'Model', 'Reference Number', 'Selling Price (PHP)', 'Quantity in Stock', 'Location', 'Status', 'Date Added']
        self.assertEqual(rows[0], expected_headers)

        if len(rows) > 1:
            first_data_row = rows[1]
            self.assertEqual(len(first_data_row), len(expected_headers))
            self.assertTrue(first_data_row[0].startswith('#'))

    def test_03_export_services_csv(self):
        self.login_admin()
        resp = self.client.get('/reports/export/services-csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn('attachment;filename=services_report_', resp.headers.get('Content-Disposition', ''))

        csv_text = resp.data.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)

        self.assertGreaterEqual(len(rows), 1, "CSV should contain at least headers")
        expected_headers = ['Service ID', 'Timepiece', 'Customer', 'Service Type', 'Description', 'Date', 'Cost (PHP)', 'Status']
        self.assertEqual(rows[0], expected_headers)

        if len(rows) > 1:
            first_data_row = rows[1]
            self.assertEqual(len(first_data_row), len(expected_headers))
            self.assertTrue(first_data_row[0].startswith('#'))

if __name__ == '__main__':
    unittest.main()
