import unittest

from sqlalchemy import select

from app import create_app, db
from app.models import Usuarios

# see https://docs.python.org/3/library/unittest.html for reference
# simple tests to check that the app is created correctly
# and that the database connection is working
# and that a simple query works
# more tests can be added later
class TestMyCode(unittest.TestCase):
    def test_app_creation(self):
        app = create_app('testing')
        self.assertTrue(app is not None)

    def test_app_is_flask_instance(self):
        app = create_app('test')
        self.assertEqual(app.name, 'test')
        self.assertTrue(hasattr(app, 'run'))

    def test_app_home_redirect_route(self):
        app = create_app('test_routes')
        client = app.test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_app_inexistant_route(self):
        app = create_app('test_routes')
        client = app.test_client()
        
        # Set the Accept header to trigger JSON response
        response = client.get('/nonexistent', headers={'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Not Found"})

    def test_database_connection(self):
        app = create_app('test_db')
        with app.app_context():
            db_instance = db
            self.assertIsNotNone(db_instance)
            self.assertTrue(hasattr(db_instance, 'session'))
            self.assertTrue(hasattr(db_instance, 'Model'))

    def test_database_read_user(self):
        app = create_app('test_db')
        with app.app_context():
            select_user = select(Usuarios)
            result = db.session.execute(select_user).scalars().all()
            self.assertIsInstance(result, list)
            if result:
                self.assertIsInstance(result[0], Usuarios)

if __name__ == '__main__':
    unittest.main()