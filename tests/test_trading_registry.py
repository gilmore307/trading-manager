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
        "artifact_sync_policy": "sync_artifact",
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

    def test_data_bundle_and_data_source_rows_are_separated(self):
        with Path("registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["SEC_EDGAR"]["kind"], "term")
        self.assertEqual(
            rows["SEC_EDGAR"]["path"],
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        )
        expected_bundles = {
            "01_MARKET_REGIME_MODEL_INPUTS": "01_market_regime_model_inputs",
            "02_SECURITY_SELECTION_MODEL_INPUTS": "02_security_selection_model_inputs",
            "03_STRATEGY_SELECTION_MODEL_INPUTS": "03_strategy_selection_model_inputs",
            "04_TRADE_QUALITY_MODEL_INPUTS": "04_trade_quality_model_inputs",
            "05_OPTION_EXPRESSION_MODEL_INPUTS": "05_option_expression_model_inputs",
            "06_EVENT_OVERLAY_MODEL_INPUTS": "06_event_overlay_model_inputs",
            "07_PORTFOLIO_RISK_MODEL_INPUTS": "07_portfolio_risk_model_inputs",
        }
        expected_sources = {
            "ALPACA_BARS": "alpaca_bars",
            "ALPACA_LIQUIDITY": "alpaca_liquidity",
            "ALPACA_NEWS": "alpaca_news",
            "THETADATA_OPTION_PRIMARY_TRACKING": "thetadata_option_primary_tracking",
            "THETADATA_OPTION_EVENT_TIMELINE": "thetadata_option_event_timeline",
            "THETADATA_OPTION_SELECTION_SNAPSHOT": "thetadata_option_selection_snapshot",
            "OKX_CRYPTO_MARKET_DATA": "okx_crypto_market_data",
            "CALENDAR_DISCOVERY": "calendar_discovery",
            "ETF_HOLDINGS": "etf_holdings",
            "TRADING_ECONOMICS_CALENDAR_WEB": "trading_economics_calendar_web",
            "SEC_COMPANY_FINANCIALS": "sec_company_financials",
        }
        for key, payload in expected_bundles.items():
            self.assertEqual(rows[key]["kind"], "data_bundle")
            self.assertEqual(rows[key]["payload"], payload)
        for key, payload in expected_sources.items():
            self.assertEqual(rows[key]["kind"], "data_source")
            self.assertEqual(rows[key]["payload"], payload)
        self.assertNotIn("MACRO_DATA", rows)
        self.assertNotIn("STOCK_ETF_EXPOSURE_BUNDLE_DEPRECATED", rows)
        self.assertNotIn("EQUITY_ABNORMAL_ACTIVITY_BUNDLE", rows)
        self.assertNotIn("EQUITY_ABNORMAL_ACTIVITY_BUNDLE_CONFIG", rows)

    def test_initial_data_kinds_are_registered(self):
        with Path("registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        by_key = {row["key"]: row for row in rows}
        data_kinds = [row for row in rows if row["kind"] == "data_kind"]

        self.assertEqual(len(data_kinds), 18)
        for row in data_kinds:
            self.assertTrue(row["path"], row["key"])
            template_path = Path("/root/projects") / row["path"] if row["path"].startswith("trading-") else Path(row["path"])
            self.assertTrue(template_path.exists(), row["key"])
            self.assertGreater(template_path.stat().st_size, 0, row["key"])
        expected_payloads = {
            "MACRO_RELEASE_EVENT": "macro_release_event",
            "GDELT_ARTICLE": "gdelt_article",
            "TRADING_ECONOMICS_CALENDAR_EVENT": "trading_economics_calendar_event",
            "EQUITY_BAR": "equity_bar",
            "EQUITY_LIQUIDITY_BAR": "equity_liquidity_bar",
            "CRYPTO_BAR": "crypto_bar",
            "CRYPTO_LIQUIDITY_BAR": "crypto_liquidity_bar",
            "OPTION_ACTIVITY_EVENT": "option_activity_event",
            "OPTION_ACTIVITY_EVENT_DETAIL": "option_activity_event_detail",
            "OPTION_BAR": "option_bar",
            "OPTION_CHAIN_SNAPSHOT": "option_chain_snapshot",
            "ETF_HOLDINGS_SNAPSHOT": "etf_holdings_snapshot",
            "STOCK_ETF_EXPOSURE": "stock_etf_exposure",
            "EQUITY_ABNORMAL_ACTIVITY_EVENT": "equity_abnormal_activity_event",
            "TRADING_EVENT": "trading_event",
            "EVENT_FACTOR": "event_factor",
            "EVENT_ANALYSIS_REPORT": "event_analysis_report",
        }
        for key, payload in expected_payloads.items():
            self.assertEqual(by_key[key]["kind"], "data_kind")
            self.assertEqual(by_key[key]["payload"], payload)
        self.assertEqual(
            by_key["EQUITY_LIQUIDITY_BAR"]["path"],
            "trading-data/storage/templates/data_kinds/alpaca/equity_liquidity_bar.preview.csv",
        )
        self.assertEqual(
            by_key["CRYPTO_BAR"]["path"],
            "trading-data/storage/templates/data_kinds/okx/crypto_bar.preview.csv",
        )
        self.assertEqual(
            by_key["OPTION_ACTIVITY_EVENT_DETAIL"]["path"],
            "trading-data/storage/templates/data_kinds/thetadata/option_activity_event_detail.preview.csv",
        )
        self.assertEqual(
            by_key["MACRO_RELEASE_EVENT"]["path"],
            "trading-data/storage/templates/data_kinds/events/macro_release_event.preview.csv",
        )
        self.assertEqual(
            by_key["DATA_KIND_TEMPLATE_PREVIEW_FILE"]["path"],
            "trading-data/storage/templates/data_kinds/alpaca/README.md",
        )
        reclassified_data_kind_keys = {
            "ECONOMIC_RELEASE_EVENT",
            "EQUITY_EARNINGS_CALENDAR",
            "ETF_CONSTITUENT_WEIGHT",
            "ETF_FUND_METADATA",
            "FOMC_MINUTES",
            "FOMC_SEP",
            "FOMC_STATEMENT",
            "SEC_FILING_DOCUMENT",
            "CRYPTO_TRADE",
            "CRYPTO_QUOTE",
            "CRYPTO_ORDER_BOOK",
            "EQUITY_TRADE",
            "EQUITY_QUOTE",
            "EQUITY_SNAPSHOT",
            "OPTION_GREEKS_FIRST_ORDER",
            "OPTION_GREEKS_SECOND_ORDER",
            "OPTION_GREEKS_THIRD_ORDER",
            "OPTION_IMPLIED_VOLATILITY",
            "OPTION_TRADE_GREEKS",
            "OPTION_TRADE",
            "OPTION_QUOTE",
            "OPTION_NBBO",
            "SEC_COMPANY_FACT",
            "FOMC_MEETING", 
        }
        for key in reclassified_data_kind_keys:
            self.assertIn(key, by_key)
            self.assertNotEqual(by_key[key]["kind"], "data_kind")

        deleted_deprecated_macro_keys = {
            "MACRO_BEA_FIXED_ASSETS",
            "MACRO_ALFRED_VINTAGE",
            "MACRO_BEA_NIPA",
            "MACRO_BLS_CPI",
            "MACRO_BLS_ECI",
            "MACRO_FRED_NATIVE",
            "MACRO_RELEASE",
            "MACRO_TREASURY_DTS",
            "MACRO_TREASURY_MTS",
        }
        for key in deleted_deprecated_macro_keys:
            self.assertNotIn(key, by_key)

        expected_source_capabilities = {
            "CRYPTO_TRADE",
            "CRYPTO_QUOTE",
            "CRYPTO_ORDER_BOOK",
            "EQUITY_TRADE",
            "EQUITY_QUOTE",
            "EQUITY_SNAPSHOT",
            "OPTION_GREEKS_FIRST_ORDER",
            "OPTION_GREEKS_SECOND_ORDER",
            "OPTION_GREEKS_THIRD_ORDER",
            "OPTION_IMPLIED_VOLATILITY",
            "OPTION_TRADE_GREEKS",
            "OPTION_TRADE",
            "OPTION_QUOTE",
            "OPTION_NBBO",
            "SEC_COMPANY_FACT",
            "SEC_FILING_DOCUMENT",
            "FOMC_MEETING",
            "FOMC_MINUTES",
            "FOMC_SEP",
            "FOMC_STATEMENT",
            "EQUITY_EARNINGS_CALENDAR",
        }
        for key in expected_source_capabilities:
            self.assertEqual(by_key[key]["kind"], "source_capability")
        self.assertNotIn("MACRO_RELEASE", by_key)
        self.assertIn("must not duplicate official", by_key["FRED"]["note"])

    def test_market_etf_universe_shared_csv_columns_are_registered(self):
        shared_path = Path("storage/shared/market_etf_universe.csv")
        with shared_path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 61)
        self.assertEqual(
            list(rows[0].keys()),
            ["symbol", "universe_type", "exposure_type", "bar_grain", "fund_name", "issuer"],
        )
        self.assertEqual(rows[0]["symbol"], "AIQ")
        self.assertEqual(rows[-1]["symbol"], "VNQ")

        with Path("registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}
        self.assertEqual(registry["MARKET_ETF_UNIVERSE_SHARED_CSV"]["path"], "/root/projects/trading-main/storage/shared/market_etf_universe.csv")
        expected_fields = {
            "SYMBOL": "symbol",
            "UNIVERSE_TYPE": "universe_type",
            "EXPOSURE_TYPE": "exposure_type",
            "BAR_GRAIN": "bar_grain",
            "FUND_NAME": "fund_name",
            "ISSUER": "issuer",
        }
        classification_fields = {"UNIVERSE_TYPE", "EXPOSURE_TYPE"}
        for key, payload in expected_fields.items():
            expected_kind = "classification_field" if key in classification_fields else "field"
            self.assertEqual(registry[key]["kind"], expected_kind)
            self.assertEqual(registry[key]["payload"], payload)
            self.assertIn("market_etf_universe", registry[key]["applies_to"])
            if key not in {"SYMBOL", "ISSUER"}:
                self.assertEqual(registry[key]["path"], "storage/shared/market_etf_universe.csv")

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

    def test_status_like_rows_use_one_kind_with_domain_scope(self):
        old_status_kinds = {
            "task_lifecycle_status",
            "review_readiness",
            "acceptance_outcome",
            "test_status",
            "maintenance_status",
            "docs_status",
            "artifact_sync_policy",
        }
        expected_domains = old_status_kinds - {"artifact_sync_policy"}
        expected_domains.add("trading_registry.artifact_sync_policy")

        with Path("registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        self.assertFalse({row["kind"] for row in rows} & old_status_kinds)
        status_rows = [row for row in rows if row["kind"] == "status_value"]
        self.assertTrue(status_rows)
        domains = {
            domain
            for row in status_rows
            for domain in row["applies_to"].split(";")
            if domain
        }
        self.assertEqual(domains, expected_domains)
        payloads = [row["payload"] for row in status_rows]
        self.assertEqual(len(payloads), len(set(payloads)))
        self.assertEqual(
            next(row for row in status_rows if row["payload"] == "blocked")["key"],
            "STATUS_BLOCKED",
        )

    def test_temporal_fields_are_separate_and_iso_scoped(self):
        expected_temporal_keys = {
            "AS_OF_DATE",
            "CHECK_TIME",
            "DATA_TASK_RUN_COMPLETED_AT",
            "DATA_TASK_RUN_STARTED_AT",
            "DATA_TIMESTAMP",
            "EVENT_EFFECTIVE_TIME",
            "EVENT_FACTOR_AS_OF",
            "EVENT_TIME",
            "GDELT_ARTICLE_SEEN_AT",
            "GENERATED_AT",
            "INTERVAL_START",
            "OPTION_EXPIRATION",
            "REGISTRY_ITEM_CREATED_AT",
            "REGISTRY_ITEM_UPDATED_AT",
            "SNAPSHOT_TIME",
            "STOCK_ETF_AVAILABLE_TIME",
            "TRADE_TIMESTAMP",
            "UNDERLYING_TIMESTAMP",
            "WINDOW_END",
            "WINDOW_START",
        }
        with Path("registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_temporal_keys:
            self.assertEqual(rows[key]["kind"], "temporal_field")
            self.assertEqual(rows[key]["payload_format"], "field_name")
            self.assertIn("ISO 8601", rows[key]["note"])
            self.assertFalse(rows[key]["key"].endswith("_ET"))
            self.assertFalse(rows[key]["key"].endswith("_UTC"))
            self.assertFalse(rows[key]["payload"].endswith("_et"))
            self.assertFalse(rows[key]["payload"].endswith("_utc"))
        self.assertNotIn("TIMELINE_CREATED_AT_ET", rows)
        self.assertNotIn("TIMELINE_UPDATED_AT_ET", rows)
        self.assertNotIn("OPTION_EVENT_DETAIL_STANDARD_GENERATED_AT", rows)
        self.assertEqual(rows["GENERATED_AT"]["payload"], "generated_at")
        self.assertIn("event_analysis_report_template", rows["GENERATED_AT"]["applies_to"])
        self.assertIn("option_activity_event_detail_template", rows["GENERATED_AT"]["applies_to"])
        self.assertIn("event_timeline_template", rows["REGISTRY_ITEM_CREATED_AT"]["applies_to"])
        self.assertIn("event_timeline_template", rows["REGISTRY_ITEM_UPDATED_AT"]["applies_to"])
        self.assertEqual(rows["DATA_TIMEFRAME"]["kind"], "field")
        self.assertEqual(rows["OPTION_DAYS_TO_EXPIRATION"]["kind"], "field")

    def test_field_like_payloads_are_unique_semantic_words(self):
        with Path("registry/current.csv").open(newline="") as csv_file:
            field_like_rows = [
                row
                for row in csv.DictReader(csv_file)
                if row["kind"] in {"field", "temporal_field", "classification_field"}
            ]

        payloads = [row["payload"] for row in field_like_rows]
        self.assertEqual(len(payloads), len(set(payloads)))

        by_key = {row["key"]: row for row in field_like_rows}
        for key in {"OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE", "VOLUME", "VWAP", "TRADE_COUNT"}:
            self.assertIn("market_data_template", by_key[key]["applies_to"])
            self.assertIn("option_bar_template", by_key[key]["applies_to"])
            self.assertIn("market_liquidity_template", by_key[key]["applies_to"])
        self.assertEqual(by_key["TRADE_COUNT"]["payload"], "trade_count")
        for deleted_key in {
            "BAR_OPEN",
            "BAR_HIGH",
            "BAR_LOW",
            "BAR_CLOSE",
            "BAR_VOLUME",
            "BAR_COUNT",
            "BAR_VWAP",
            "TRADE_OPEN",
            "TRADE_HIGH",
            "TRADE_LOW",
            "TRADE_CLOSE",
            "TRADE_VOLUME",
            "TRADE_VWAP",
        }:
            self.assertNotIn(deleted_key, by_key)

    def test_classification_fields_are_separate_semantic_axes(self):
        expected_classification_keys = {
            "ABNORMAL_ACTIVITY_TYPE",
            "ACCEPTANCE_OUTCOME",
            "DATA_KIND",
            "DOCS_STATUS",
            "ETF_HOLDING_ASSET_CLASS",
            "SECTOR_TYPE",
            "EVENT_ANALYSIS_STATUS",
            "EVENT_DEDUP_STATUS",
            "EVENT_IMPACT_SCOPE",
            "EVENT_TYPE",
            "EXPOSURE_TYPE",
            "SOURCE_THEME_TAGS",
            "MAINTENANCE_STATUS",
            "TRADE_SIDE_TYPE",
            "OPTION_RIGHT",
            "REGISTRY_ITEM_ARTIFACT_SYNC_POLICY",
            "REGISTRY_ITEM_KIND",
            "REVIEW_READINESS",
            "SOURCE_TYPE",
            "STATUS",
            "EXPOSURE_TAGS",
            "TASK_LIFECYCLE_STATUS",
            "TASK_SCOPE",
            "TEST_STATUS",
            "SOURCE_EVENT_TYPE",
            "UNIVERSE_TYPE",
        }
        with Path("registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_classification_keys:
            self.assertEqual(rows[key]["kind"], "classification_field")
            self.assertEqual(rows[key]["payload_format"], "field_name")
            self.assertIn("stable lowercase token", rows[key]["note"])
        self.assertNotIn("GDELT_IMPACT_SCOPE_HINT", rows)
        self.assertNotIn("OPTION_EVENT_DETAIL_SIDE_HINT", rows)
        self.assertNotIn("TRADING_ECONOMICS_CATEGORY", rows)
        self.assertIn("gdelt_article_template", rows["EVENT_IMPACT_SCOPE"]["applies_to"])
        self.assertEqual(rows["EVENT_IMPACT_SCOPE"]["payload"], "impact_scope")
        self.assertEqual(rows["TRADE_SIDE_TYPE"]["payload"], "trade_side_type")
        self.assertEqual(rows["SOURCE_EVENT_TYPE"]["payload"], "source_event_type")
        self.assertEqual(rows["TITLE"]["kind"], "field")
        self.assertEqual(rows["RETURN_ZSCORE"]["kind"], "field")

    def test_registered_artifact_sync_policies_match_sql_constraint(self):
        constraint_blocks = []
        for migration in sorted(Path("registry/sql/schema_migrations").glob("*.sql")):
            text = migration.read_text()
            if "CHECK (artifact_sync_policy IN (" in text:
                constraint_blocks.append(
                    text.split("CHECK (artifact_sync_policy IN (", 1)[1].split("));", 1)[0]
                )
        self.assertTrue(constraint_blocks)
        constrained_policies = tuple(re.findall(r"'([^']+)'", constraint_blocks[-1]))

        with Path("registry/current.csv").open(newline="") as csv_file:
            registered_policies = tuple(
                row["payload"]
                for row in csv.DictReader(csv_file)
                if row["kind"] == "status_value"
                and row["applies_to"] == "trading_registry.artifact_sync_policy"
            )

        self.assertEqual(sorted(registered_policies), sorted(constrained_policies))
        self.assertIn("registry_only", registered_policies)
        self.assertIn("sync_artifact", registered_policies)
        self.assertIn("review_on_merge", registered_policies)

    def test_test_scripts_are_documented_and_not_registered_as_scripts(self):
        test_scripts = sorted(Path("tests").glob("test_*.py"))
        self.assertTrue(test_scripts)

        tests_readme = Path("tests/README.md").read_text()
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
        self.assertEqual(item.artifact_sync_policy, "sync_artifact")
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

class WebSearchHelperTests(unittest.TestCase):
    def test_csv_registry_query_resolves_config_secret(self):
        from trading_registry import SecretResolver, create_csv_registry_query

        rows = {
            "id": "cfg_TESTSEARCH",
            "kind": "config",
            "key": "TEST_SEARCH_SECRET_ALIAS",
            "payload_format": "secret_alias",
            "payload": "test-search",
            "path": "/root/secrets/test-search.json",
            "applies_to": "unit",
            "artifact_sync_policy": "registry_only",
            "note": "unit",
            "created_at": "",
            "updated_at": "",
        }

        def read_text(path: str) -> str:
            if path.endswith("registry.csv"):
                raise AssertionError("registry CSV should be read by query helper")
            if path == "/root/secrets/registry.json":
                return json.dumps({"test-search": {"path": "/root/secrets/test-search.json"}})
            if path == "/root/secrets/test-search.json":
                return json.dumps({"api_key": "search-key"})
            raise AssertionError(path)

        import csv as _csv
        import tempfile as _tempfile

        with _tempfile.TemporaryDirectory() as temp_dir:
            registry_csv = Path(temp_dir) / "registry.csv"
            with registry_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = _csv.DictWriter(handle, fieldnames=list(rows))
                writer.writeheader()
                writer.writerow(rows)
            resolver = SecretResolver(create_csv_registry_query(registry_csv), read_text=read_text)
            self.assertEqual(resolver.load_secret_text_by_config_id("cfg_TESTSEARCH", "api_key"), "search-key")

    def test_bigquery_client_normalizes_query_results_with_mock_transport(self):
        from trading_bigquery.client import BigQueryClient
        from unittest.mock import patch

        class FakeResponse:
            status = 200

            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(self.payload).encode()

        service_account = {
            "type": "service_account",
            "project_id": "unit-project",
            "client_email": "unit@example.test",
            "token_uri": "https://oauth.example.test/token",
            "private_key": "-----BEGIN PRIVATE KEY-----\nunit\n-----END PRIVATE KEY-----\n",
        }
        query_payload = {"schema": {"fields": [{"name": "url"}, {"name": "title"}]}, "rows": [{"f": [{"v": "https://example.test"}, {"v": "Example"}]}], "totalRows": "1"}

        with patch("trading_bigquery.client._jwt_encode_rs256", return_value="signed.jwt"), patch("urllib.request.urlopen", side_effect=[FakeResponse({"access_token": "token", "expires_in": 3600}), FakeResponse(query_payload)]) as urlopen:
            result = BigQueryClient(service_account).query("SELECT url, title", max_results=1)

        self.assertEqual(result.schema, ["url", "title"])
        self.assertEqual(result.rows[0]["title"], "Example")
        token_request = urlopen.call_args_list[0].args[0]
        query_request = urlopen.call_args_list[1].args[0]
        self.assertEqual(token_request.full_url, "https://oauth.example.test/token")
        self.assertEqual(query_request.headers["Authorization"], "Bearer token")
        self.assertIn("/projects/unit-project/queries", query_request.full_url)

    def test_brave_search_client_normalizes_results_with_mock_transport(self):
        from trading_web_search.brave import BraveSearchClient
        from unittest.mock import patch
        import io

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"web": {"results": [{"title": "A", "url": "https://example.test", "description": "D", "site_name": "example"}]}}).encode()

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            results = BraveSearchClient("unit-key").search("macro release calendar", count=1)
        self.assertEqual(results[0].title, "A")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["X-subscription-token"], "unit-key")
        self.assertIn("macro+release+calendar", request.full_url)
