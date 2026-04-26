import json
import re
import unittest
from pathlib import Path

from trading_registry import (
    PAYLOAD_FORMATS,
    REGISTRY_KINDS,
    RegistryReader,
    SecretResolver,
    assert_payload_format,
    assert_registry_kind,
    get_secret_entry_from_registry,
    is_payload_format,
    is_registry_kind,
    map_registry_item_row,
    parse_registry,
)


def create_row(**overrides):
    row = {
        "id": "fld_A7K3P2Q9",
        "kind": "field",
        "key": "REGISTRY_ITEM_ID",
        "payload_format": "text",
        "payload": "id",
        "path": None,
        "applies_to": "trading_registry",
        "note": "canonical column name for trading_registry.id",
        "created_at": "2026-04-23T00:00:00.000Z",
        "updated_at": "2026-04-23T00:00:00.000Z",
    }
    row.update(overrides)
    return row


class RegistryHelperTests(unittest.TestCase):
    def test_registry_kinds_stay_fixed(self):
        self.assertEqual(
            REGISTRY_KINDS,
            (
                "field",
                "output",
                "repo",
                "config",
                "term",
                "script",
                "artifact_type",
                "manifest_type",
                "ready_signal_type",
                "request_type",
                "task_lifecycle_state",
                "review_readiness",
                "acceptance_outcome",
                "test_status",
                "maintenance_status",
                "docs_status",
            ),
        )
        self.assertTrue(is_registry_kind("repo"))
        self.assertFalse(is_registry_kind("unknown"))
        self.assertEqual(assert_registry_kind("config"), "config")
        with self.assertRaisesRegex(ValueError, "Invalid registry kind: unknown"):
            assert_registry_kind("unknown")

    def test_payload_formats_match_sql_constraint(self):
        migration = Path("registry/sql/schema_migrations/004_expand_payload_formats.sql").read_text()
        constraint = migration.split("CHECK (payload_format IN (", 1)[1].split("));", 1)[0]
        quoted_formats = re.findall(r"'([^']+)'", constraint)
        self.assertEqual(tuple(quoted_formats), PAYLOAD_FORMATS)

    def test_payload_formats_include_structured_values(self):
        self.assertIn("iso_time", PAYLOAD_FORMATS)
        self.assertIn("iso_datetime", PAYLOAD_FORMATS)
        self.assertIn("secret_alias", PAYLOAD_FORMATS)
        self.assertTrue(is_payload_format("field_name"))
        self.assertEqual(assert_payload_format("timezone"), "timezone")
        with self.assertRaisesRegex(ValueError, "Invalid registry payload_format: yaml"):
            assert_payload_format("yaml")

    def test_map_registry_item_row_rejects_invalid_payload_format(self):
        with self.assertRaisesRegex(ValueError, "Invalid registry payload_format: yaml"):
            map_registry_item_row(create_row(payload_format="yaml"))

    def test_map_registry_item_row(self):
        item = map_registry_item_row(create_row(payload_format="field_name"))
        self.assertEqual(item.id, "fld_A7K3P2Q9")
        self.assertEqual(item.payload_format, "field_name")
        self.assertEqual(item.applies_to, "trading_registry")
        self.assertIsNone(item.path)

    def test_id_only_registry_helpers_return_key_payload_and_path(self):
        calls = []

        def query(sql, params):
            calls.append((sql, params))
            if params[0] == "missing":
                return {"rows": []}
            return {
                "rows": [
                    create_row(
                        id="rep_H6S3V8LA",
                        kind="repo",
                        key="TRADING_MAIN_REPO",
                        payload_format="repo_name",
                        payload="trading-main",
                        path="/root/projects/trading-main",
                        applies_to=None,
                    )
                ]
            }

        reader = RegistryReader(query)
        self.assertEqual(reader.get_key_by_id("rep_H6S3V8LA"), "TRADING_MAIN_REPO")
        self.assertEqual(reader.get_payload_by_id("rep_H6S3V8LA"), "trading-main")
        self.assertEqual(reader.get_path_by_id("rep_H6S3V8LA"), "/root/projects/trading-main")
        self.assertIsNone(reader.get_key_by_id("missing"))
        self.assertIsNone(reader.get_payload_by_id("missing"))
        self.assertIsNone(reader.get_path_by_id("missing"))
        self.assertTrue(all("WHERE id = %s" in sql for sql, _ in calls))

    def test_require_item_by_id_throws_for_missing_item(self):
        reader = RegistryReader(lambda _sql, _params: {"rows": []})
        with self.assertRaisesRegex(KeyError, "Registry item not found for id: fld_missing"):
            reader.require_item_by_id("fld_missing")

    def test_id_lookup_rejects_blank_id_inputs(self):
        reader = RegistryReader(lambda _sql, _params: {"rows": []})
        with self.assertRaisesRegex(TypeError, "id must be a non-empty string"):
            reader.get_key_by_id("   ")

    def test_list_items_by_kind_validates_kind(self):
        def query(sql, params):
            self.assertIn("WHERE kind = %s", sql)
            self.assertIn("ORDER BY key ASC", sql)
            self.assertEqual(params, ["repo"])
            return [create_row(kind="repo", key="TRADING_MAIN_REPO", payload="trading-main")]

        reader = RegistryReader(query)
        items = reader.list_items_by_kind("repo")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, "repo")
        with self.assertRaisesRegex(ValueError, "Invalid registry kind: workflow"):
            reader.list_items_by_kind("workflow")

    def test_parse_registry_rejects_invalid_json_and_returns_objects(self):
        with self.assertRaisesRegex(ValueError, "is not valid JSON"):
            parse_registry("{", "/root/secrets/registry.json")
        parsed = parse_registry(
            json.dumps({"example-service": {"token": {"path": "/root/secrets/example-service/token"}}}),
            "/root/secrets/registry.json",
        )
        self.assertEqual(parsed["example-service"]["token"]["path"], "/root/secrets/example-service/token")

    def test_get_secret_entry_from_registry_resolves_aliases(self):
        entry = get_secret_entry_from_registry(
            {
                "github": {
                    "pat": {
                        "path": "/root/secrets/github/pat",
                        "kind": "token",
                        "use": "git https credential helper",
                    }
                }
            },
            "github/pat",
            "/root/secrets/registry.json",
        )
        self.assertEqual(entry["alias"], "github/pat")
        self.assertEqual(entry["path"], "/root/secrets/github/pat")
        self.assertEqual(entry["kind"], "token")

    def test_secret_resolver_loads_secret_text_by_config_id(self):
        reads = []

        def query(sql, params):
            self.assertIn("WHERE id = %s", sql)
            self.assertEqual(params, ["cfg_EXAMPLETOKEN"])
            return {
                "rows": [
                    create_row(
                        id="cfg_EXAMPLETOKEN",
                        kind="config",
                        key="EXAMPLE_SERVICE_TOKEN_SECRET_ALIAS",
                        payload_format="secret_alias",
                        payload="example-service/token",
                        applies_to=None,
                    )
                ]
            }

        def read_text(path):
            reads.append(path)
            if path == "/root/secrets/registry.json":
                return json.dumps(
                    {
                        "example-service": {
                            "token": {
                                "path": "/root/secrets/example-service/token",
                                "kind": "token",
                                "use": "example service bearer token",
                            }
                        }
                    }
                )
            if path == "/root/secrets/example-service/token":
                return "secret-value\n"
            raise AssertionError(f"unexpected read: {path}")

        resolver = SecretResolver(query, registry_path="/root/secrets/registry.json", read_text=read_text)
        self.assertEqual(resolver.load_secret_text_by_config_id("cfg_EXAMPLETOKEN"), "secret-value")
        self.assertEqual(reads[0], "/root/secrets/registry.json")

    def test_secret_resolver_rejects_non_config_items(self):
        resolver = SecretResolver(
            lambda _sql, _params: {"rows": [create_row(kind="term", payload="Project sentinel")]},
            read_text=lambda _path: "{}",
        )
        with self.assertRaisesRegex(ValueError, "must be kind=config"):
            resolver.load_secret_text_by_config_id("trm_OPENCLAW")


if __name__ == "__main__":
    unittest.main()
