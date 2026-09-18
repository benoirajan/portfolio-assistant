"""
Unit Tests for src.services.llm_advisor
Verifies DEBUG level prompt payload logging and google-genai SDK integration.
"""
import logging
import unittest
from unittest.mock import MagicMock, patch

from src.services.llm_advisor import (
    get_multi_stage_advisory,
    get_recommendations,
    _call_gemini_schema,
    Stage1Diagnosis,
)

SAMPLE_HOLDINGS = [
    {
        "tradingsymbol": "RELIANCE",
        "quantity": 10,
        "last_price": 2500.0,
        "sector": "Energy",
        "cap_category": "Large Cap",
        "pe_ratio": 25.0,
        "pb_ratio": 2.1,
        "roe": 14.5,
        "roce": 12.8,
        "div_yield": 0.5,
        "trend_200_sma": "Bullish",
    },
    {
        "tradingsymbol": "INFY",
        "quantity": 20,
        "last_price": 1500.0,
        "sector": "Information Technology",
        "cap_category": "Large Cap",
        "pe_ratio": 28.0,
        "pb_ratio": 7.5,
        "roe": 29.0,
        "roce": 34.0,
        "div_yield": 2.1,
        "trend_200_sma": "Bullish",
    }
]

STAGE1_JSON = '{"overall_quality": "High", "main_strength": "ROE", "main_weakness": "Concentration", "biggest_concentration_risk": "IT", "most_important_thing_to_monitor": "Valuation", "sector_analysis": [], "stock_analysis": [], "portfolio_risks": [], "portfolio_strengths": [], "future_capital_direction": []}'
STAGE2_JSON = '{"opportunity_summary": "Good", "existing_vs_new_recommendation": "Existing", "strongest_opportunity": "INFY", "top_opportunities": [], "sectors_to_prefer": [], "sectors_to_be_careful": [], "sectors_to_avoid": []}'
STAGE3_JSON = '{"action": "BUY", "allocated_amount": 5000.0, "cash_to_keep": 0.0, "purchases": [], "why_this_decision": [], "portfolio_impact": [], "why_not_others": "None", "risks_to_understand": [], "data_date_verified": "Today", "simple_action_recommendation": "Invest"}'


class TestLLMAdvisor(unittest.TestCase):

    def test_multi_stage_debug_logging(self):
        """Verify that multi-stage advisory logs prompt payloads at DEBUG level."""
        logger = logging.getLogger("portfolio_assistant.llm_advisor")
        logger.setLevel(logging.DEBUG)

        with self.assertLogs("portfolio_assistant.llm_advisor", level="DEBUG") as cm:
            with patch("src.core.config.settings.LLM_PROVIDER", "gemini"), \
                 patch("src.core.config.settings.GEMINI_API_KEY", "test_key"), \
                 patch("src.services.llm_advisor._call_gemini_schema", side_effect=[STAGE1_JSON, STAGE2_JSON, STAGE3_JSON]):

                result = get_multi_stage_advisory(SAMPLE_HOLDINGS, total_budget=5000.0)
                self.assertEqual(result["status"], "success")

            output = "\n".join(cm.output)
            self.assertIn("Gemini Stage 1 Prompt Payload:", output)
            self.assertIn("Gemini Stage 2 Prompt Payload:", output)
            self.assertIn("Gemini Stage 3 Prompt Payload:", output)

    def test_legacy_recommendations_debug_logging(self):
        """Verify legacy get_recommendations logs prompt payload at DEBUG level."""
        logger = logging.getLogger("portfolio_assistant.llm_advisor")
        logger.setLevel(logging.DEBUG)

        with self.assertLogs("portfolio_assistant.llm_advisor", level="DEBUG") as cm:
            with patch("src.core.config.settings.LLM_PROVIDER", "gemini"), \
                 patch("src.core.config.settings.GEMINI_API_KEY", "test_key"), \
                 patch("src.services.llm_advisor._call_gemini", return_value=None):

                result = get_recommendations(SAMPLE_HOLDINGS)
                self.assertIn("recommendations", result)

            output = "\n".join(cm.output)
            self.assertIn("Gemini Legacy Prompt Payload:", output)

    @patch("google.genai.Client")
    def test_call_gemini_schema_sdk_integration(self, mock_genai_client):
        """Verify _call_gemini_schema correctly invokes Client and logs payload and raw response."""
        logger = logging.getLogger("portfolio_assistant.llm_advisor")
        logger.setLevel(logging.DEBUG)

        mock_response = MagicMock()
        mock_response.text = STAGE1_JSON

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client_instance

        with self.assertLogs("portfolio_assistant.llm_advisor", level="DEBUG") as cm:
            with patch("src.core.config.settings.GEMINI_API_KEY", "dummy_key"):
                response_text = _call_gemini_schema("Test prompt payload", Stage1Diagnosis)
                self.assertEqual(response_text, mock_response.text)

            output = "\n".join(cm.output)
            self.assertIn("Gemini API request prompt payload (schema=Stage1Diagnosis):", output)
            self.assertIn("Gemini API raw response (schema=Stage1Diagnosis):", output)


if __name__ == "__main__":
    unittest.main()
