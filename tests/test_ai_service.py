import unittest
from services.ai_service import AIService

class AIServiceTestCase(unittest.TestCase):
    """Test cases for AI service"""
    
    def setUp(self):
        """Set up test environment"""
        self.ai_service = AIService()
    
    def test_analyze_crime_with_fallback(self):
        """Test crime analysis with fallback mode"""
        analysis = AIService.analyze_crime(
            crime_type='Phishing Attack',
            description='I received an email asking for my password'
        )
        
        self.assertIsNotNone(analysis)
        self.assertIn('crime_category', analysis)
        self.assertIn('severity_score', analysis)
        self.assertIn('confidence_score', analysis)
        self.assertIn('suggested_actions', analysis)
    
    def test_analyze_crime_severity_detection(self):
        """Test severity detection for different crime types"""
        # Test high severity crime
        analysis_high = AIService.analyze_crime(
            crime_type='Ransomware Attack',
            description='Files encrypted, ransom demanded'
        )
        self.assertIn(analysis_high['severity_score'], ['High', 'Critical'])
        
        # Test medium severity crime
        analysis_medium = AIService.analyze_crime(
            crime_type='Cyber Bullying',
            description='Harassment on social media'
        )
        self.assertIn(analysis_medium['severity_score'], ['Medium', 'Low'])
    
    def test_fallback_analysis_structure(self):
        """Test fallback analysis structure"""
        analysis = AIService.get_fallback_analysis('Online Fraud', 'Test description')
        
        # Check all required keys
        required_keys = ['crime_category', 'severity_score', 'confidence_score', 
                        'suggested_actions', 'estimated_resolution_time']
        
        for key in required_keys:
            self.assertIn(key, analysis)
        
        # Check data types
        self.assertIsInstance(analysis['suggested_actions'], list)
        self.assertIsInstance(analysis['confidence_score'], (int, float))
    
    def test_get_complaint_insights(self):
        """Test complaint insights generation"""
        test_complaint = {
            'crime_type': 'Online Fraud',
            'priority': 'high',
            'status': 'under_review',
            'description': 'Financial fraud case involving bank transfer'
        }
        
        insights = AIService.get_complaint_insights(test_complaint)
        
        self.assertIn('summary', insights)
        self.assertIn('risk_factors', insights)
        self.assertIn('recommendations', insights)
        self.assertIsInstance(insights['risk_factors'], list)
    
    def test_analyze_trends(self):
        """Test trends analysis"""
        test_data = [
            {'crime_type': 'Phishing', 'month': '2024-01'},
            {'crime_type': 'Phishing', 'month': '2024-01'},
            {'crime_type': 'Online Fraud', 'month': '2024-02'},
            {'crime_type': 'Identity Theft', 'month': '2024-02'}
        ]
        
        trends = AIService.analyze_trends(test_data)
        
        self.assertIn('overall_trend', trends)
        self.assertIn('most_common_crime', trends)
        self.assertIn('monthly_data', trends)
    
    def test_get_predictions(self):
        """Test predictions generation"""
        predictions = AIService.get_predictions()
        
        self.assertIn('high_risk_areas', predictions)
        self.assertIn('expected_increase', predictions)
        self.assertIn('recommendation', predictions)
        self.assertIn('emerging_threats', predictions)
        self.assertIsInstance(predictions['emerging_threats'], list)
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        analysis = AIService.analyze_crime(
            crime_type='Credit Card Fraud',
            description='Unauthorized transaction on credit card. Amount: $5000. This is a detailed description with multiple sentences explaining the incident thoroughly.'
        )
        
        # Confidence should be reasonable
        self.assertGreaterEqual(analysis['confidence_score'], 50)
        self.assertLessEqual(analysis['confidence_score'], 98)
    
    def test_suggested_actions_count(self):
        """Test suggested actions count"""
        analysis = AIService.analyze_crime(
            crime_type='Data Breach',
            description='Company database hacked'
        )
        
        # Should have between 3-6 suggested actions
        actions_count = len(analysis['suggested_actions'])
        self.assertGreaterEqual(actions_count, 3)
        self.assertLessEqual(actions_count, 6)

if __name__ == '__main__':
    unittest.main()