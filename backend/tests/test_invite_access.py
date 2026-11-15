"""Invite redemption and optional API enforcement tests. No live services."""
import hashlib
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.schemas import PhotoMealEstimate
from app.services.invite_access import verify_invite_token
from test_photo_analysis import ESTIMATE, PHOTO


VALID_CODE = "BITE-TEST-0001"
VALID_DIGEST = hashlib.sha256(VALID_CODE.encode("utf-8")).hexdigest()


class InviteAccessTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            _env_file=None,
            openai_api_key="test-secret",
            invite_code_hashes=f"tester-01:{VALID_DIGEST}",
            invite_token_secret="test-secret-that-is-at-least-32-bytes-long",
            invite_token_ttl_seconds=432000,
        )
        app.dependency_overrides[get_settings] = lambda: self.settings
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def redeem(self, code=VALID_CODE):
        return self.client.post("/v1/invites/redeem", json={"code": code})

    def test_redeems_case_insensitively_for_five_day_token(self):
        response = self.redeem("  bite-test-0001 ")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertEqual(body["expires_in_seconds"], 432000)
        self.assertEqual(body["invite_id"], "tester-01")
        self.assertEqual(verify_invite_token(body["access_token"], self.settings), "tester-01")

    def test_rejects_unknown_code_and_misconfiguration(self):
        self.assertEqual(self.redeem("BITE-WRONG-0000").status_code, 401)
        self.settings.invite_code_hashes = ""
        self.assertEqual(self.redeem().status_code, 503)
        self.settings.invite_code_hashes = f"tester-01:{VALID_DIGEST}"
        self.settings.invite_token_secret = "too-short"
        self.assertEqual(self.redeem().status_code, 503)

    def test_revokes_code_and_previously_issued_tokens(self):
        token = self.redeem().json()["access_token"]

        self.settings.invite_revoked_code_hashes = VALID_DIGEST
        self.assertEqual(self.redeem().status_code, 401)

        self.settings.invite_revoked_ids = "tester-01"
        with self.assertRaises(Exception) as revoked:
            verify_invite_token(token, self.settings)
        self.assertEqual(revoked.exception.status_code, 401)

    def test_enforcement_is_off_by_default_and_can_be_enabled(self):
        estimate = PhotoMealEstimate(**ESTIMATE)
        with patch("app.main.analyze_meal", new=AsyncMock(return_value=estimate)) as provider:
            response = self.client.post("/v1/meals/analyze-inline", json={"image_data_url": PHOTO})
        self.assertEqual(response.status_code, 200)
        provider.assert_awaited_once()

        self.settings.invite_enforcement_enabled = True
        with patch("app.main.analyze_meal", new=AsyncMock(return_value=estimate)) as provider:
            response = self.client.post("/v1/meals/analyze-inline", json={"image_data_url": PHOTO})
            self.assertEqual(response.status_code, 401)
            provider.assert_not_awaited()

            token = self.redeem().json()["access_token"]
            response = self.client.post(
                "/v1/meals/analyze-inline",
                json={"image_data_url": PHOTO},
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 200)
        provider.assert_awaited_once()

    def test_expired_and_tampered_tokens_are_rejected(self):
        from app.services.invite_access import redeem_invite_code

        token, _ = redeem_invite_code(VALID_CODE, self.settings, now=100)
        with self.assertRaises(Exception) as expired:
            verify_invite_token(token, self.settings, now=432101)
        self.assertEqual(expired.exception.status_code, 401)

        payload, signature = token.split(".", 1)
        with self.assertRaises(Exception) as tampered:
            verify_invite_token(payload + "." + signature[:-1] + "A", self.settings, now=101)
        self.assertEqual(tampered.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
