"""Plan extraction route/provider tests. No live AI calls."""
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.schemas import PlanEstimate


PLAN = {
    "daily_calories": 2200,
    "daily_protein": 140.0,
    "weekly_calories": 15400,
    "weekly_protein": 980.0,
    "daily_calories_range": [2200, 2200],
    "daily_protein_range": [140.0, 140.0],
    "weekly_calories_range": [15400, 15400],
    "weekly_protein_range": [980.0, 980.0],
    "targets_are_estimated": False,
    "goal": "Support training",
    "meal_schedule": [{"label": "Lunch", "options": ["150g chicken with rice"]}],
    "hydration": "2-3L water",
    "weekly_rules": ["Fish twice a week"],
    "recipe_names": [],
    "summary": "Daily calorie and protein targets.",
    "assumptions": [],
}


class PlanAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(_env_file=None, openai_api_key="test-secret")
        app.dependency_overrides[get_settings] = lambda: self.settings
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def test_route_contract(self):
        result = PlanEstimate(**PLAN)
        with patch("app.main.analyze_plan", new=AsyncMock(return_value=result)) as provider:
            response = self.client.post("/v1/plans/analyze", json={
                "filename": "plan.txt", "content_type": "text/plain", "text": "2200 calories and 140g protein"
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), PLAN)
        self.assertEqual(provider.await_count, 1)

    def test_provider_uses_structured_output(self):
        async def post(client, url, **kwargs):
            self.assertEqual(url, "https://api.openai.com/v1/responses")
            self.assertEqual(kwargs["json"]["text"]["format"]["type"], "json_schema")
            self.assertFalse(kwargs["json"]["store"])
            return httpx.Response(200, json={"status": "completed", "output": [{"content": [{"type": "output_text", "text": json.dumps(PLAN)}]}]})

        with patch("app.services.openai_plan_analyzer.httpx.AsyncClient.post", post):
            response = self.client.post("/v1/plans/analyze", json={
                "filename": "plan.txt", "content_type": "text/plain", "text": "2200 calories and 140g protein"
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), PLAN)

    def test_invalid_inline_file_is_rejected_before_provider(self):
        with patch("app.services.openai_plan_analyzer.httpx.AsyncClient.post", new=AsyncMock()) as provider:
            response = self.client.post("/v1/plans/analyze", json={
                "filename": "plan.pdf",
                "content_type": "application/pdf",
                "file_data_url": "data:application/pdf;base64,!!!!",
            })
        self.assertEqual(response.status_code, 422)
        self.assertIn("valid PDF", response.json()["detail"])
        provider.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
