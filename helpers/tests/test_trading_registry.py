import csv
import json
import re
import unittest
from pathlib import Path

from trading_registry import (
    RegistryReader,
    SecretResolver,
    get_secret_entry_from_registry,
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
    def test_registry_kind_files_match_sql_constraint_and_current_rows(self):
        constraint_blocks = []
        for migration in sorted(Path("registry/sql/schema_migrations").glob("*.sql")):
            text = migration.read_text()
            if "CHECK (kind IN (" in text:
                constraint_blocks.append(text.split("CHECK (kind IN (", 1)[1].split("));", 1)[0])
        self.assertTrue(constraint_blocks)
        constrained_kinds = sorted(re.findall(r"'([^']+)'", constraint_blocks[-1]))

        kind_files = sorted(
            path.stem
            for path in Path("registry/kinds").glob("*.md")
            if path.name != "README.md"
        )

        with Path("registry/current.csv").open(newline="") as csv_file:
            current_kinds = {row["kind"] for row in csv.DictReader(csv_file)}

        self.assertEqual(kind_files, constrained_kinds)
        self.assertLessEqual(current_kinds, set(constrained_kinds))
        self.assertIn("payload_format", constrained_kinds)

    def test_sec_company_financials_terms_are_registered(self):
        with Path("registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["SEC_EDGAR"]["kind"], "term")
        self.assertEqual(
            rows["SEC_EDGAR"]["path"],
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        )
        self.assertEqual(rows["SEC_COMPANY_FINANCIALS"]["kind"], "term")
        self.assertIn("sec_company_financials", rows["SEC_COMPANY_FINANCIALS"]["note"])

    def test_registered_payload_formats_match_sql_constraint(self):
        constraint_blocks = []
        for migration in sorted(Path("registry/sql/schema_migrations").glob("*.sql")):
            text = migration.read_text()
            if "CHECK (payload_format IN (" in text:
                constraint_blocks.append(text.split("CHECK (payload_format IN (", 1)[1].split("));", 1)[0])
        self.assertTrue(constraint_blocks)
        constrained_formats = tuple(re.findall(r"'([^']+)'", constraint_blocks[-1]))

        with Path("registry/current.csv").open(newline="") as csv_file:
            registered_formats = tuple(
                row["payload"]
                for row in csv.DictReader(csv_file)
                if row["kind"] == "payload_format"
            )

        self.assertEqual(sorted(registered_formats), sorted(constrained_formats))
        self.assertIn("iso_time", registered_formats)
        self.assertIn("iso_datetime", registered_formats)
        self.assertIn("secret_alias", registered_formats)


    def test_test_scripts_are_documented_and_not_registered_as_scripts(self):
        test_scripts = sorted(Path("helpers/tests").glob("test_*.py"))
        self.assertTrue(test_scripts)

        tests_readme = Path("helpers/tests/README.md").read_text()
        for script in test_scripts:
            self.assertIn(f"`{script.name}`", tests_readme)

        with Path("registry/current.csv").open(newline="") as csv_file:
            script_rows = [row for row in csv.DictReader(csv_file) if row["kind"] == "script"]

        for row in script_rows:
            normalized_path = (row["path"] or "").replace("\\", "/")
            self.assertNotIn("/tests/", normalized_path)
            self.assertFalse(Path(normalized_path).name.startswith("test_"), row["key"])

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

    def test_list_items_by_kind_filters_by_kind(self):
        def query(sql, params):
            self.assertIn("WHERE kind = %s", sql)
            self.assertIn("ORDER BY key ASC", sql)
            self.assertEqual(params, ["repo"])
            return [create_row(kind="repo", key="TRADING_MAIN_REPO", payload="trading-main")]

        reader = RegistryReader(query)
        items = reader.list_items_by_kind("repo")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, "repo")
        with self.assertRaisesRegex(TypeError, "kind must be a non-empty string"):
            reader.list_items_by_kind("   ")

    def test_parse_registry_rejects_invalid_json_and_returns_objects(self):
        with self.assertRaisesRegex(ValueError, "is not valid JSON"):
            parse_registry("{", "/root/secrets/registry.json")
        parsed = parse_registry(
            json.dumps({"example-service": {"path": "/root/secrets/example-service.json"}}),
            "/root/secrets/registry.json",
        )
        self.assertEqual(parsed["example-service"]["path"], "/root/secrets/example-service.json")

    def test_get_secret_entry_from_registry_resolves_source_json_aliases(self):
        entry = get_secret_entry_from_registry(
            {
                "github": {
                    "path": "/root/secrets/github.json",
                    "kind": "source_secret_json",
                    "use": "git operations",
                    "fields": {"pat": "GitHub personal access token"},
                }
            },
            "github",
            "/root/secrets/registry.json",
        )
        self.assertEqual(entry["alias"], "github")
        self.assertEqual(entry["path"], "/root/secrets/github.json")
        self.assertEqual(entry["kind"], "source_secret_json")

    def test_secret_resolver_loads_source_json_field_text_by_config_id(self):
        reads = []

        def query(sql, params):
            self.assertIn("WHERE id = %s", sql)
            self.assertEqual(params, ["cfg_EXAMPLESECRET"])
            return {
                "rows": [
                    create_row(
                        id="cfg_EXAMPLESECRET",
                        kind="config",
                        key="EXAMPLE_SERVICE_SECRET_ALIAS",
                        payload_format="secret_alias",
                        payload="example-service",
                        path="/root/secrets/example-service.json",
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
                            "path": "/root/secrets/example-service.json",
                            "kind": "source_secret_json",
                            "use": "example service credentials",
                            "fields": {
                                "allowed_ip_address": "example allowlisted IPv4 address",
                                "api_key": "example service API key",
                                "endpoint": "example service API endpoint",
                            },
                        }
                    }
                )
            if path == "/root/secrets/example-service.json":
                return json.dumps(
                    {
                        "allowed_ip_address": "203.0.113.10",
                        "api_key": "secret-value",
                        "endpoint": "https://example.test/v1",
                        "secret_key": "other-secret",
                    }
                )
            raise AssertionError(f"unexpected read: {path}")

        resolver = SecretResolver(query, registry_path="/root/secrets/registry.json", read_text=read_text)
        raw_secret_json = resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET")
        self.assertEqual(json.loads(raw_secret_json)["api_key"], "secret-value")
        self.assertEqual(
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "api_key"),
            "secret-value",
        )
        self.assertEqual(
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "allowed_ip_address"),
            "203.0.113.10",
        )
        self.assertEqual(
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "endpoint"),
            "https://example.test/v1",
        )
        with self.assertRaisesRegex(KeyError, "Secret JSON field not found"):
            resolver.load_secret_text_by_config_id("cfg_EXAMPLESECRET", "missing")
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
