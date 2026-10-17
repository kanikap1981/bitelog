"""Run with: python -m unittest discover -s tests -v (no live AI calls)."""
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings, get_settings

# Valid 64x64 PNG: route fixture only, not a nutrition accuracy fixture.
PHOTO = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAeklEQVR4nO3PUQkAIBTAwBfVKEYxqiH8OITBAtxmn/V1wwUNaEEDWtCAFjSgBQ1oQQNa0IAWNKAFDWhBA1rQgBY0oAUNaEEDWtCAFjSgBQ1oQQNa0IAWNKAFDWhBA1rQgBY0oAUNaEEDWtCAFjSgBQ1oQQNa0IAWPHYBH1wBaXB16TcAAAAASUVORK5CYII='
ESTIMATE = dict(name='Eggs and toast', calories=420, protein=23.5,
                confidence=0.7, description='A small plate', assumptions=['Two eggs'])


class PhotoAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(_env_file=None, openai_api_key='test-secret')
        app.dependency_overrides[get_settings] = lambda: self.settings
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def post(self, data=PHOTO):
        return self.client.post('/v1/meals/analyze-inline', json={'image_data_url': data})

    def provider(self, payload=None, status=200, error=None):
        async def post(client, url, **kwargs):
            self.assertEqual(url, 'https://api.openai.com/v1/responses')
            body = kwargs['json']
            self.assertEqual(body['input'][0]['content'][1]['image_url'], PHOTO)
            self.assertEqual(body['input'][0]['content'][1]['detail'], 'low')
            self.assertEqual(body['text']['format']['type'], 'json_schema')
            self.assertTrue(body['text']['format']['strict'])
            self.assertFalse(body['store'])
            self.assertEqual(kwargs['headers']['Authorization'], 'Bearer test-secret')
            if error:
                raise error
            return httpx.Response(status, json=payload)
        return patch('app.services.openai_meal_analyzer.httpx.AsyncClient.post', post)

    def output(self, estimate=ESTIMATE):
        return {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(estimate)}]}]}

    def test_health_and_success_contract(self):
        self.assertEqual(self.client.get('/health').json()['status'], 'ok')
        with self.provider(self.output()):
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ESTIMATE)
        self.assertEqual(len(response.headers['X-Request-ID']), 32)

    def test_invalid_images_never_call_provider(self):
        with patch('app.main.analyze_meal') as provider:
            for value in ['data:image/gif;base64,' + 'a'*40, 'data:image/png;base64,' + '!'*40]:
                self.assertEqual(self.post(value).status_code, 400)
            self.settings.max_inline_image_bytes = 10
            self.assertEqual(self.post().status_code, 413)
            self.assertEqual(self.client.post('/v1/meals/analyze-inline', json={}).status_code, 422)
            provider.assert_not_called()

    def test_missing_key(self):
        self.settings.openai_api_key = ''
        self.assertEqual(self.post().status_code, 503)

    def test_timeouts_and_connection_errors(self):
        for error, code in [(httpx.ReadTimeout('private detail'), 504), (httpx.ConnectError('private detail'), 503)]:
            with self.provider(error=error):
                response = self.post()
            self.assertEqual(response.status_code, code)
            self.assertNotIn('private detail', response.text)

    def test_provider_errors_do_not_leak(self):
        for status in [400, 401, 403, 429, 500]:
            with self.provider({'error': {'message': 'test-secret'}}, status):
                response = self.post()
            self.assertGreaterEqual(response.status_code, 500)
            self.assertNotIn('test-secret', response.text)

    def test_invalid_incomplete_and_refused_responses(self):
        cases = [([], 502), ({'status':'incomplete'}, 502),
                 (self.output(dict(ESTIMATE, calories=-1)), 502),
                 (self.output(dict(ESTIMATE, name=' ')), 502),
                 ({'status':'completed','output':[{'content':[{'type':'refusal','refusal':'private'}]}]}, 422),
                 ({'status':'completed','output':[{'content':[{'type':'output_text','text':'not json'}]}]}, 502)]
        for payload, status in cases:
            with self.provider(payload):
                response = self.post()
            self.assertEqual(response.status_code, status)
            self.assertIsInstance(response.json()['detail'], str)

    def test_cors_from_bundled_webview(self):
        response = self.client.options('/v1/meals/analyze-inline', headers={
            'Origin':'null', 'Access-Control-Request-Method':'POST',
            'Access-Control-Request-Headers':'content-type'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], '*')


if __name__ == '__main__':
    unittest.main()
