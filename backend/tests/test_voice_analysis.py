"""Voice meal route/provider tests. No live AI calls."""
import base64
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.schemas import VoiceMealEstimate


AUDIO = "data:audio/mp4;base64," + base64.b64encode(b"short-audio-fixture" * 4).decode()
VOICE_ESTIMATE = dict(
    name="Eggs and toast",
    calories=420,
    protein=23.5,
    confidence=0.72,
    description="Two eggs with toast",
    assumptions=["Two eggs", "One slice of toast"],
    transcript="I had two eggs and a slice of toast",
)


class VoiceAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(_env_file=None, openai_api_key="test-secret")
        app.dependency_overrides[get_settings] = lambda: self.settings
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def post(self, data=AUDIO):
        return self.client.post("/v1/meals/analyze-voice", json={"audio_data_url": data})

    def test_route_contract_and_audio_validation(self):
        result = VoiceMealEstimate(**VOICE_ESTIMATE)
        with patch("app.main.analyze_voice_meal", new=AsyncMock(return_value=result)) as provider:
            response = self.post()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), VOICE_ESTIMATE)
            audio, content_type, extension, _ = provider.await_args.args
            self.assertEqual(audio, b"short-audio-fixture" * 4)
            self.assertEqual((content_type, extension), ("audio/mp4", "mp4"))

        with patch("app.main.analyze_voice_meal", new=AsyncMock()) as provider:
            for value in ["data:text/plain;base64," + "YQ==" * 10, "data:audio/mp4;base64,!!!!"]:
                self.assertIn(self.post(value).status_code, (400, 422))
            provider.assert_not_awaited()

    def provider(self, understood=True, transcript="I had two eggs and a slice of toast"):
        calls = []

        async def post(client, url, **kwargs):
            calls.append((url, kwargs))
            if url.endswith("/audio/transcriptions"):
                self.assertEqual(kwargs["data"]["model"], "gpt-4o-mini-transcribe")
                self.assertEqual(kwargs["data"]["response_format"], "json")
                self.assertEqual(kwargs["files"]["file"][2], "audio/mp4")
                return httpx.Response(200, json={"text": transcript})
            self.assertEqual(url, "https://api.openai.com/v1/responses")
            body = kwargs["json"]
            self.assertEqual(body["input"][0]["content"][0]["text"], transcript)
            self.assertEqual(body["text"]["format"]["type"], "json_schema")
            self.assertTrue(body["text"]["format"]["strict"])
            self.assertFalse(body["store"])
            estimate = dict(VOICE_ESTIMATE)
            estimate.pop("transcript")
            estimate["understood"] = understood
            if not understood:
                estimate.update(name="", calories=0, protein=0, confidence=0)
            return httpx.Response(200, json={"status": "completed", "output": [{"content": [{"type": "output_text", "text": json.dumps(estimate)}]}]})

        return patch("app.services.openai_voice_meal_analyzer.httpx.AsyncClient.post", post), calls

    def test_transcribes_then_estimates_meal(self):
        provider, calls = self.provider()
        with provider:
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), VOICE_ESTIMATE)
        self.assertEqual(len(calls), 2)

    def test_unclear_voice_is_not_saved(self):
        for understood, transcript in [(False, "meeting tomorrow"), (True, " ")]:
            provider, _ = self.provider(understood=understood, transcript=transcript)
            with provider:
                response = self.post()
            self.assertEqual(response.status_code, 422)
            self.assertIn("Nothing was saved", response.json()["detail"])

    def test_journal_route_only_transcribes(self):
        with patch("app.main.transcribe_audio", new=AsyncMock(return_value="Energy was low after training")) as provider:
            response = self.client.post("/v1/voice/transcribe", json={"audio_data_url": AUDIO})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"transcript": "Energy was low after training"})
        self.assertEqual(provider.await_count, 1)


if __name__ == "__main__":
    unittest.main()
