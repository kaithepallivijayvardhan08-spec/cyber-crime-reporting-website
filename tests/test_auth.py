import unittest
import json
from app import create_app
from database.db_connection import db

class AuthTestCase(unittest.TestCase):
    """Test cases for authentication endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Test user data
        self.test_user = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '9876543210',
            'password': 'Test@123'
        }
    
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
    
    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post('/api/auth/register', 
                                   json=self.test_user,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'User registered successfully')
    
    def test_register_missing_fields(self):
        """Test registration with missing fields"""
        user_data = {'full_name': 'Test User'}
        response = self.client.post('/api/auth/register', 
                                   json=user_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        user_data = self.test_user.copy()
        user_data['email'] = 'invalid-email'
        
        response = self.client.post('/api/auth/register', 
                                   json=user_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        # First registration
        self.client.post('/api/auth/register', 
                        json=self.test_user,
                        content_type='application/json')
        
        # Second registration with same email
        response = self.client.post('/api/auth/register', 
                                   json=self.test_user,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_login_success(self):
        """Test successful login"""
        # Register first
        self.client.post('/api/auth/register', 
                        json=self.test_user,
                        content_type='application/json')
        
        # Login
        response = self.client.post('/api/auth/login',
                                   json={
                                       'email': self.test_user['email'],
                                       'password': self.test_user['password']
                                   },
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/api/auth/login',
                                   json={
                                       'email': 'wrong@example.com',
                                       'password': 'wrongpass'
                                   },
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        response = self.client.post('/api/auth/login',
                                   json={},
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_profile_unauthorized(self):
        """Test profile access without token"""
        response = self.client.get('/api/auth/profile')
        self.assertEqual(response.status_code, 401)
    
    def test_get_profile_authorized(self):
        """Test profile access with valid token"""
        # Register and login
        self.client.post('/api/auth/register', 
                        json=self.test_user,
                        content_type='application/json')
        
        login_res = self.client.post('/api/auth/login',
                                    json={
                                        'email': self.test_user['email'],
                                        'password': self.test_user['password']
                                    },
                                    content_type='application/json')
        
        token = json.loads(login_res.data)['access_token']
        
        # Get profile
        response = self.client.get('/api/auth/profile',
                                  headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], self.test_user['email'])

if __name__ == '__main__':
    unittest.main()