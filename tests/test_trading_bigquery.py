import json
import unittest
from unittest.mock import patch

from trading_bigquery.client import BigQueryClient, _parse_query_result


class BigQueryHelperTests(unittest.TestCase):
    def test_parse_dry_run_bytes_metadata(self):
        result = _parse_query_result({
            "schema": {"fields": []},
            "rows": [],
            "totalBytesProcessed": "12345",
            "cacheHit": False,
            "dryRun": True,
        })
        self.assertEqual(result.total_bytes_processed, 12345)
        self.assertFalse(result.cache_hit)
        self.assertTrue(result.dry_run)

    def test_query_sends_maximum_bytes_billed(self):
        service_account = {
            "type": "service_account",
            "project_id": "project",
            "private_key": "unused",
            "client_email": "svc@example.com",
            "token_uri": "https://oauth2.example/token",
        }
        client = BigQueryClient(service_account=service_account)
        client._access_token = "token"
        client._token_expiry = 9999999999
        captured = {}

        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({"schema": {"fields": []}, "rows": []}).encode()

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode())
            return Response()

        with patch("urllib.request.urlopen", fake_urlopen):
            client.query("SELECT 1", maximum_bytes_billed=1024, dry_run=True)
        self.assertEqual(captured["payload"]["maximumBytesBilled"], "1024")
        self.assertTrue(captured["payload"]["dryRun"])


if __name__ == "__main__":
    unittest.main()
