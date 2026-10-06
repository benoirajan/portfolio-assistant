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
    Stage2Ranking,
    _build_stage1_prompt,
    _build_stage2_prompt,
    _build_stage3_prompt,
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



    def test_rule_based_recommendations(self):
        """Verify get_recommendations returns rule-based recommendations with custom caps."""
        # Test with max_single_stock_pct=25.0
        # RELIANCE is 25000 / 55000 = ~45.45%
        # INFY is 30000 / 55000 = ~54.54%
        result = get_recommendations(SAMPLE_HOLDINGS, max_single_stock_pct=25.0)
        self.assertIn("recommendations", result)
        self.assertEqual(result["source"], "rule_engine")
        self.assertTrue(len(result["recommendations"]) > 0)
        
        recs = result["recommendations"]
        rel_rec = next(r for r in recs if r["symbol"] == "RELIANCE")
        infy_rec = next(r for r in recs if r["symbol"] == "INFY")
        
        self.assertEqual(rel_rec["action"], "TRIM")
        self.assertEqual(rel_rec["target_allocation_pct"], 25.0)
        self.assertEqual(infy_rec["action"], "TRIM")
        self.assertEqual(infy_rec["target_allocation_pct"], 25.0)

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

    def test_prompt_rules(self):
        """Verify prompt strings contain INVESTMENT-THESIS RULES."""
        stage1 = _build_stage1_prompt([], [], "Goal", 1000, "News")
        self.assertIn("INVESTMENT-THESIS RULES:", stage1)
        self.assertIn("not short-term trading", stage1)

        s1_diag = Stage1Diagnosis.model_validate_json(STAGE1_JSON)
        stage2 = _build_stage2_prompt(s1_diag, [], "Goal", True)
        self.assertIn("INVESTMENT-THESIS RULES:", stage2)
        
        s2_rank = Stage2Ranking.model_validate_json(STAGE2_JSON)
        stage3 = _build_stage3_prompt(s1_diag, s2_rank, [], 1000, 1000, "Monthly", "Goal", {"TCS": 3500})
        self.assertIn("INVESTMENT-THESIS RULES:", stage3)

    @patch("src.services.llm_advisor.market_data_service.get_live_quote")
    def test_stage3_candidate_prices(self, mock_get_quote):
        """Verify candidate_prices are fetched and passed to Stage 3 prompt."""
        mock_get_quote.return_value = {"last_price": 4000.0}
        
        # We need to simulate stage2_data returning a non-existing holding candidate.
        s2_rank_json = '{"opportunity_summary": "Good", "existing_vs_new_recommendation": "Existing", "strongest_opportunity": "NEWSTOCK", "top_opportunities": [{"symbol": "NEWSTOCK", "sector": "IT", "is_existing_holding": false, "conviction_tier": "GOOD_OPPORTUNITY", "valuation_assessment": "Fair", "portfolio_fit_summary": "Good", "main_risk": "None", "rationale": "Growth"}], "sectors_to_prefer": [], "sectors_to_be_careful": [], "sectors_to_avoid": []}'

        with patch("src.core.config.settings.LLM_PROVIDER", "gemini"), \
             patch("src.core.config.settings.GEMINI_API_KEY", "test_key"), \
             patch("src.services.llm_advisor._call_gemini_schema", side_effect=[STAGE1_JSON, s2_rank_json, STAGE3_JSON]) as mock_call:
            
            # mock valid nse symbol so it doesn't get filtered out
            with patch("src.services.llm_advisor.market_data_service.is_valid_nse_symbol", return_value=True):
                get_multi_stage_advisory(SAMPLE_HOLDINGS, total_budget=5000.0)
            
            # check if get_live_quote was called with NEWSTOCK
            mock_get_quote.assert_called_with("NEWSTOCK")
            
            # check if stage3 call had NEWSTOCK price in the prompt
            stage3_call_args = mock_call.call_args_list[2]
            prompt = stage3_call_args[0][0]
            self.assertIn('"NEWSTOCK": 4000.0', prompt)


if __name__ == "__main__":
    unittest.main()
