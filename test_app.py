import unittest

from main import app, init_db


class RestaurantAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        init_db()

    def test_homepage_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Restaurant Management Dashboard', response.data)

    def test_customer_can_be_added(self):
        response = self.client.post('/customers', data={
            'first_name': 'Test',
            'last_name': 'Customer',
            'email': 'test@example.com',
            'phone': '555-1234',
            'loyalty_points': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Customer', response.data)


if __name__ == '__main__':
    unittest.main()
