import unittest
import json
import io
from app import create_app
from database.db_connection import db

class CrimeReportTestCase(unittest.TestCase):
    """Test cases for crime reporting endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test user and get token
        self.test_user = {
            'full_name': 'Crime Test User',
            'email': 'crimetest@example.com',
            'phone': '9876543211',
            'password': 'Test@123'
        }
        
        # Register user
        self.client.post('/api/auth/register', 
                        json=self.test_user,
                        content_type='application/json')
        
        # Login and get token
        login_res = self.client.post('/api/auth/login',
                                    json={
                                        'email': self.test_user['email'],
                                        'password': self.test_user['password']
                                    },
                                    content_type='application/json')
        
        self.token = json.loads(login_res.data)['access_token']
        
        # Test complaint data
        self.test_complaint = {
            'crime_type': 'Phishing Attack',
            'description': 'I received a suspicious email asking for my bank details. The email looked like it was from my bank but had grammatical errors.',
            'incident_date': '2024-01-15',
            'incident_location': 'Mumbai, Maharashtra',
            'additional_info': 'The email came from suspicious@example.com'
        }
    
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
    
    def test_submit_complaint_success(self):
        """Test successful complaint submission"""
        response = self.client.post('/api/crime/report',
                                   data=self.test_complaint,
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('complaint_number', data)
        self.assertIn('message', data)
    
    def test_submit_complaint_with_file(self):
        """Test complaint submission with evidence file"""
        # Create test file
        test_file = (io.BytesIO(b'This is test evidence content'), 'evidence.txt')
        
        data = self.test_complaint.copy()
        data['evidence_files'] = test_file
        
        response = self.client.post('/api/crime/report',
                                   data=data,
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['uploaded_files'], 1)
    
    def test_submit_complaint_missing_fields(self):
        """Test complaint with missing required fields"""
        incomplete_data = {
            'crime_type': 'Phishing Attack'
        }
        
        response = self.client.post('/api/crime/report',
                                   data=incomplete_data,
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_submit_complaint_short_description(self):
        """Test complaint with description too short"""
        invalid_data = self.test_complaint.copy()
        invalid_data['description'] = 'Too short'
        
        response = self.client.post('/api/crime/report',
                                   data=invalid_data,
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_my_complaints(self):
        """Test getting user's complaints"""
        # Submit a complaint first
        self.client.post('/api/crime/report',
                        data=self.test_complaint,
                        headers={'Authorization': f'Bearer {self.token}'},
                        content_type='multipart/form-data')
        
        # Get complaints
        response = self.client.get('/api/crime/my-complaints',
                                  headers={'Authorization': f'Bearer {self.token}'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('complaints', data)
        self.assertIsInstance(data['complaints'], list)
    
    def test_get_complaint_details(self):
        """Test getting specific complaint details"""
        # Submit complaint
        submit_res = self.client.post('/api/crime/report',
                                     data=self.test_complaint,
                                     headers={'Authorization': f'Bearer {self.token}'},
                                     content_type='multipart/form-data')
        
        complaint_number = json.loads(submit_res.data)['complaint_number']
        
        # Get complaint details
        response = self.client.get(f'/api/crime/complaint/{complaint_number}',
                                  headers={'Authorization': f'Bearer {self.token}'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('complaint', data)
        self.assertEqual(data['complaint']['complaint_number'], complaint_number)
    
    def test_get_nonexistent_complaint(self):
        """Test getting non-existent complaint"""
        response = self.client.get('/api/crime/complaint/INVALID123',
                                  headers={'Authorization': f'Bearer {self.token}'})
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()