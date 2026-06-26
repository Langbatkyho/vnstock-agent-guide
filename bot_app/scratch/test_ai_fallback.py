import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add bot_app to sys.path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(workspace_root, 'bot_app'))

import config
config.GEMINI_API_KEYS = "KEY1,KEY2,KEY3"
config.GEMINI_MODEL = "gemini-3.5-flash"

import ai_analyzer

class TestAIFallback(unittest.TestCase):
    def setUp(self):
        # Reset keys
        ai_analyzer._api_keys = ["KEY1", "KEY2", "KEY3"]
        ai_analyzer._current_key_idx = 0
        ai_analyzer._client = MagicMock()
        ai_analyzer._client_overall = MagicMock()

    @patch('time.sleep', return_value=None)
    def test_503_fallback(self, mock_sleep):
        mock_generate = MagicMock()
        mock_generate.side_effect = [
            Exception("503 Service Unavailable"),
            MagicMock(text="Success after 503")
        ]
        ai_analyzer._client.models.generate_content = mock_generate

        result = ai_analyzer.analyze_scorecards("VND", {"VND": {"price": 10}}, {"signal": "BUY", "details": []})
        self.assertEqual(result, "Success after 503")
        self.assertEqual(mock_generate.call_count, 2)
        
        # Check that it fell back to 2.5-flash
        mock_generate.assert_called_with(
            model="gemini-2.5-flash",
            contents=unittest.mock.ANY
        )

    @patch('ai_analyzer.genai.Client')
    @patch('time.sleep', return_value=None)
    def test_429_rotation(self, mock_sleep, mock_genai_client):
        # Mock genai.Client so rotation doesn't fail
        mock_genai_client.return_value = MagicMock()
        
        mock_generate = MagicMock()
        mock_generate.side_effect = [
            Exception("429 ResourceExhausted"),
            Exception("429 ResourceExhausted"),
            MagicMock(text="Success after 429")
        ]
        ai_analyzer._client.models.generate_content = mock_generate

        result = ai_analyzer.analyze_scorecards("HPG", {"HPG": {"price": 20}}, {"signal": "SELL", "details": []})
        self.assertEqual(result, "Success after 429")
        self.assertEqual(mock_generate.call_count, 3)
        self.assertEqual(ai_analyzer._current_key_idx, 2)

if __name__ == "__main__":
    unittest.main()
