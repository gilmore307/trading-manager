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
        for migration in sorted(Path("scripts/registry/sql/schema_migrations").glob("*.sql")):
            text = migration.read_text()
            if "CHECK (kind IN (" in text:
                constraint_blocks.append(text.split("CHECK (kind IN (", 1)[1].split("));", 1)[0])
        self.assertTrue(constraint_blocks)
        constrained_kinds = sorted(re.findall(r"'([^']+)'", constraint_blocks[-1]))

        kind_files = sorted(
            path.stem
            for path in Path("scripts/registry/kinds").glob("*.md")
            if path.name != "README.md"
        )

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            current_kinds = {row["kind"] for row in csv.DictReader(csv_file)}

        self.assertEqual(kind_files, constrained_kinds)
        self.assertLessEqual(current_kinds, set(constrained_kinds))
        self.assertIn("payload_format", constrained_kinds)

    def test_component_repository_rows_use_trading_data_and_manager_boundaries(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["TRADING_DATA_REPO"]["payload"], "trading-data")
        self.assertEqual(rows["TRADING_DATA_REPO"]["path"], "/root/projects/trading-data")
        self.assertIn("trading-data.git", rows["TRADING_DATA_REPO"]["note"])
        self.assertEqual(rows["TRADING_MANAGER_REPO"]["payload"], "trading-manager")
        self.assertEqual(rows["TRADING_MANAGER_REPO"]["path"], "/root/projects/trading-manager")
        self.assertIn("control-plane", rows["TRADING_MANAGER_REPO"]["note"])
        self.assertNotIn("TRADING_MAIN_REPO", rows)
        self.assertNotIn("TRADING_SOURCE_REPO", rows)
        self.assertNotIn("TRADING_DERIVED_REPO", rows)
        self.assertNotIn("TRADING_STRATEGY_REPO", rows)
        for row in rows.values():
            self.assertNotIn("trading-main", row["payload"])
            self.assertNotIn("trading-main", row["path"])
            self.assertNotIn("trading-source", row["payload"])
            self.assertNotIn("trading-source", row["path"])
            self.assertNotIn("trading-derived", row["payload"])
            self.assertNotIn("trading-derived", row["path"])
            self.assertNotIn("trading-strategy", row["payload"])
            self.assertNotIn("trading-strategy", row["path"])

    def test_data_feed_and_data_source_rows_are_separated(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertEqual(rows["SEC_EDGAR"]["kind"], "provider")
        self.assertEqual(
            rows["SEC_EDGAR"]["path"],
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        )
        expected_current_providers = {
            "ALPACA",
            "GDELT",
            "OKX",
            "SEC_EDGAR",
            "THETADATA",
            "TRADING_ECONOMICS",
        }
        actual_providers = {key for key, row in rows.items() if row["kind"] == "provider"}
        self.assertEqual(actual_providers, expected_current_providers)
        for obsolete_provider_term in {"BEA", "BLS", "CENSUS", "FRED", "US_TREASURY_FISCAL_DATA"}:
            self.assertNotIn(obsolete_provider_term, rows)
        self.assertEqual(rows["GITHUB"]["kind"], "term")
        expected_sources = {
            "SOURCE_01_MARKET_REGIME": "source_01_market_regime",
            "SOURCE_02_TARGET_CANDIDATE_HOLDINGS": "source_02_target_candidate_holdings",
            "SOURCE_03_TARGET_STATE": "source_03_target_state",
            "SOURCE_05_OPTION_EXPRESSION": "source_05_option_expression",
            "SOURCE_06_POSITION_EXECUTION": "source_06_position_execution",
            "SOURCE_07_EVENT_OVERLAY": "source_07_event_overlay",
        }
        expected_feeds = {
            "ALPACA_BARS": "01_feed_alpaca_bars",
            "ALPACA_LIQUIDITY": "02_feed_alpaca_liquidity",
            "ALPACA_NEWS": "03_feed_alpaca_news",
            "OKX_CRYPTO_MARKET_DATA": "04_feed_okx_crypto_market_data",
            "GDELT_NEWS": "05_feed_gdelt_news",
            "ETF_HOLDINGS": "06_feed_etf_holdings",
            "TRADING_ECONOMICS_CALENDAR_WEB": "07_feed_trading_economics_calendar_web",
            "SEC_COMPANY_FINANCIALS": "08_feed_sec_company_financials",
            "THETADATA_OPTION_SELECTION_SNAPSHOT": "09_feed_thetadata_option_selection_snapshot",
            "THETADATA_OPTION_PRIMARY_TRACKING": "10_feed_thetadata_option_primary_tracking",
            "THETADATA_OPTION_EVENT_TIMELINE": "11_feed_thetadata_option_event_timeline",
        }
        for key, payload in expected_sources.items():
            self.assertEqual(rows[key]["kind"], "data_source")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn(f"data_source/{payload}", rows[key]["path"])
            self.assertNotIn("_model_inputs", rows[key]["payload"])
            self.assertNotIn("_model_inputs", rows[key]["path"])
        for key, payload in expected_feeds.items():
            self.assertEqual(rows[key]["kind"], "data_feed")
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn(f"data_feed/{payload}", rows[key]["path"])
        for row in rows.values():
            self.assertNotIn("trading-source", row["path"])
            self.assertNotIn("trading-derived", row["path"])
            self.assertNotIn("data_sources/", row["path"])
            self.assertNotIn("data_bundles/", row["path"])
            self.assertNotIn("source_availability", row["path"])
            self.assertNotIn("source_interfaces", row["path"])
        self.assertNotIn("MACRO_DATA", rows)
        self.assertNotIn("STOCK_ETF_EXPOSURE_BUNDLE_DEPRECATED", rows)
        self.assertNotIn("EQUITY_ABNORMAL_ACTIVITY_BUNDLE", rows)
        self.assertNotIn("EQUITY_ABNORMAL_ACTIVITY_BUNDLE_CONFIG", rows)
        for obsolete_config in {
            "01_MARKET_REGIME_MODEL_INPUTS_BUNDLE_CONFIG",
            "03_STRATEGY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG",
            "05_OPTION_EXPRESSION_MODEL_INPUTS_BUNDLE_CONFIG",
        }:
            self.assertNotIn(obsolete_config, rows)
        self.assertEqual(rows["TARGET_STATE_VECTOR_SYNCHRONIZED_STATE_WINDOWS"]["payload"], "5min;15min;60min;390min")
        self.assertEqual(rows["TARGET_STATE_VECTOR_VERSION_DEFAULT"]["payload"], "target_state_vector_v1")
        self.assertEqual(
            rows["TARGET_STATE_VECTOR_WINDOW_SYNC_POLICY"]["payload"],
            "market_sector_target_blocks_must_share_identical_observation_windows",
        )
        self.assertIn("3_target_direction_score_<window>", rows["TARGET_STATE_VECTOR_DIRECTION_NEUTRAL_SCORE_FAMILIES"]["payload"])
        self.assertIn("3_tradability_score_<window>", rows["TARGET_STATE_VECTOR_DIRECTION_NEUTRAL_SCORE_FAMILIES"]["payload"])
        for expected_target_state_vector_payload in {
            "market_regime_state",
            "market_trend_state",
            "market_volatility_state",
            "market_breadth_state",
            "market_liquidity_stress_state",
            "market_correlation_state",
            "sector_context_state",
            "sector_relative_direction_state",
            "sector_trend_quality_stability_state",
            "sector_volatility_state",
            "sector_breadth_dispersion_state",
            "sector_liquidity_tradability_state",
            "target_direction_return_shape",
            "target_trend_quality_state",
            "target_volatility_range_state",
            "target_gap_jump_state",
            "target_volume_activity_state",
            "target_liquidity_tradability_state",
            "target_vwap_location_state",
            "target_session_position_state",
            "target_data_quality_state",
            "target_vs_market_residual_direction",
            "target_vs_sector_residual_direction",
            "target_vs_market_volatility",
            "target_vs_sector_volatility",
            "target_market_beta_correlation",
            "target_sector_beta_correlation",
            "sector_confirmation_state",
            "idiosyncratic_residual_state",
            "relative_liquidity_tradability_state",
            "3_target_direction_score_<window>",
            "3_target_trend_quality_score_<window>",
            "3_target_path_stability_score_<window>",
            "3_target_noise_score_<window>",
            "3_target_transition_risk_score_<window>",
            "3_target_liquidity_tradability_score",
            "3_context_direction_alignment_score_<window>",
            "3_context_support_quality_score_<window>",
            "3_tradability_score_<window>",
            "3_state_quality_score",
            "3_evidence_count",
            "target_state_vector",
            "score_payload",
            "target_state_embedding",
            "state_cluster_id",
            "state_quality_diagnostics",
            "5min",
            "15min",
            "60min",
            "390min",
            "sector_confirmed",
            "sector_divergent",
            "flat_or_mixed",
            "completed_1min_bars",
        }:
            self.assertIn(expected_target_state_vector_payload, {row["payload"] for row in rows.values()})
        self.assertEqual(rows["MODEL_VECTOR_TAXONOMY"]["payload"], "trading-model/docs/92_vector_taxonomy.md")
        self.assertEqual(rows["ALPHA_CONFIDENCE_MODEL"]["payload"], "alpha_confidence_model")
        self.assertEqual(rows["MODEL_04_ALPHA_CONFIDENCE"]["payload"], "model_04_alpha_confidence")
        self.assertEqual(rows["TRADING_PROJECTION_MODEL"]["payload"], "trading_projection_model")
        self.assertEqual(rows["MODEL_05_TRADING_PROJECTION"]["payload"], "model_05_trading_projection")
        self.assertEqual(rows["MARKET_DIRECTION_SCORE"]["payload"], "1_market_direction_score")
        self.assertEqual(rows["MARKET_TREND_QUALITY_SCORE"]["payload"], "1_market_trend_quality_score")
        self.assertEqual(rows["MARKET_LIQUIDITY_SUPPORT_SCORE"]["payload"], "1_market_liquidity_support_score")
        self.assertEqual(rows["MARKET_COVERAGE_SCORE"]["payload"], "1_coverage_score")
        self.assertEqual(rows["MARKET_DATA_QUALITY_SCORE"]["payload"], "1_data_quality_score")
        for retired_layer_one_field in {
            "PRICE_BEHAVIOR_FACTOR",
            "TREND_CERTAINTY_FACTOR",
            "CAPITAL_FLOW_FACTOR",
            "SENTIMENT_FACTOR",
            "VALUATION_PRESSURE_FACTOR",
            "FUNDAMENTAL_STRENGTH_FACTOR",
            "MACRO_ENVIRONMENT_FACTOR",
            "MARKET_STRUCTURE_FACTOR",
            "RISK_STRESS_FACTOR",
            "TRANSITION_PRESSURE",
            "DATA_QUALITY_SCORE",
        }:
            self.assertNotIn(retired_layer_one_field, rows)
        self.assertNotIn("TARGET_STATE_VECTOR_TRAILING_STATE_WINDOWS", rows)
        self.assertNotIn("04_TRADE_QUALITY_MODEL_INPUTS", rows)
        self.assertNotIn("04_TRADE_QUALITY_MODEL_INPUTS_BUNDLE_CONFIG", rows)
        self.assertNotIn("06_EVENT_OVERLAY_MODEL_INPUTS", rows)
        self.assertNotIn("06_EVENT_OVERLAY_MODEL_INPUTS_BUNDLE_CONFIG", rows)
        self.assertNotIn("07_PORTFOLIO_RISK_MODEL_INPUTS", rows)
        self.assertNotIn("07_PORTFOLIO_RISK_MODEL_INPUTS_BUNDLE_CONFIG", rows)

    def test_event_database_scope_is_not_active(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            offenders = [
                (row["key"], row["applies_to"])
                for row in csv.DictReader(csv_file)
                if "event_database" in (row["applies_to"] or "")
            ]
        self.assertEqual(offenders, [])

    def test_applies_to_uses_type_first_source_scopes(self):
        pattern = re.compile(r"(?:^|;)[0-9]{2}_source_")
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            offenders = [
                (row["key"], row["applies_to"])
                for row in csv.DictReader(csv_file)
                if pattern.search(row["applies_to"] or "")
            ]
        self.assertEqual(offenders, [])

    def test_model_input_output_fields_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        expected = {
            "OPTION_SYMBOL": ("identity_field", "option_symbol", "source_06_position_execution"),
            "DOLLAR_VOLUME": ("field", "dollar_volume", "source_03_target_state"),
            "QUOTE_AVG_BID_SIZE": ("field", "avg_bid_size", "source_03_target_state"),
            "QUOTE_AVG_ASK_SIZE": ("field", "avg_ask_size", "source_03_target_state"),
            "QUOTE_SPREAD_BPS": ("field", "spread_bps", "source_03_target_state"),
            "SNAPSHOT_TYPE": ("classification_field", "snapshot_type", "source_05_option_expression"),
            "INFORMATION_ROLE_TYPE": ("classification_field", "information_role_type", "source_07_event_overlay"),
            "EVENT_CATEGORY_TYPE": ("classification_field", "event_category_type", "source_07_event_overlay"),
            "SCOPE_TYPE": ("classification_field", "scope_type", "source_07_event_overlay"),
            "REFERENCE_TYPE": ("classification_field", "reference_type", "source_07_event_overlay"),
            "EVENT_REFERENCE": ("path_field", "reference", "source_07_event_overlay"),
            "QUOTE_BID_EXCHANGE": ("field", "bid_exchange", "source_05_option_expression"),
            "QUOTE_ASK_EXCHANGE": ("field", "ask_exchange", "source_05_option_expression"),
            "QUOTE_BID_CONDITION": ("field", "bid_condition", "source_05_option_expression"),
            "QUOTE_ASK_CONDITION": ("field", "ask_condition", "source_05_option_expression"),
        }
        for key, (kind, payload, applies_to) in expected.items():
            self.assertEqual(rows[key]["kind"], kind)
            self.assertEqual(rows[key]["payload"], payload)
            self.assertIn(applies_to, rows[key]["applies_to"])

        for key in ["SYMBOL", "DATA_TIMESTAMP", "BAR_OPEN", "BAR_VWAP"]:
            self.assertIn("source_01_market_regime", rows[key]["applies_to"])
        for key in ["ETF_SYMBOL", "ETF_HOLDING_SYMBOL", "SECTOR_TYPE"]:
            self.assertIn("source_02_target_candidate_holdings", rows[key]["applies_to"])
        for key in ["EVENT_ID", "EVENT_TIME", "TITLE", "SOURCE_NAME"]:
            self.assertIn("source_07_event_overlay", rows[key]["applies_to"])
        self.assertNotIn("OPTION_CONTRACT_COUNT", rows)
        self.assertNotIn("OPTION_CONTRACTS", rows)
        self.assertNotIn("QUOTE_TIMESTAMP", rows)
        self.assertNotIn("IV_TIMESTAMP", rows)
        self.assertNotIn("GREEKS_TIMESTAMP", rows)

    def test_initial_data_kinds_are_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        by_key = {row["key"]: row for row in rows}
        data_kinds = {row["key"]: row for row in rows if row["kind"] == "data_kind"}
        data_features = {row["key"]: row for row in rows if row["kind"] == "data_feature"}
        data_derived = {row["key"]: row for row in rows if row["kind"] == "data_derived"}

        self.assertEqual(data_kinds, {})
        self.assertEqual(data_derived, {})
        self.assertEqual(
            set(data_features),
            {
                "FEATURE_01_MARKET_REGIME",
                "FEATURE_02_SECTOR_CONTEXT",
                "FEATURE_03_TARGET_STATE_VECTOR",
            },
        )
        self.assertEqual(data_features["FEATURE_01_MARKET_REGIME"]["payload"], "feature_01_market_regime")
        self.assertIn("data_feature/feature_01_market_regime", data_features["FEATURE_01_MARKET_REGIME"]["path"])
        self.assertEqual(data_features["FEATURE_02_SECTOR_CONTEXT"]["payload"], "feature_02_sector_context")
        self.assertIn("data_feature/feature_02_sector_context", data_features["FEATURE_02_SECTOR_CONTEXT"]["path"])
        self.assertEqual(
            data_features["FEATURE_03_TARGET_STATE_VECTOR"]["payload"],
            "feature_03_target_state_vector",
        )
        self.assertIn(
            "data_feature/feature_03_target_state_vector",
            data_features["FEATURE_03_TARGET_STATE_VECTOR"]["path"],
        )
        self.assertIn("trading-data", data_features["FEATURE_01_MARKET_REGIME"]["applies_to"])
        self.assertIn("market_regime_model", data_features["FEATURE_01_MARKET_REGIME"]["applies_to"])
        self.assertIn("source_01_market_regime", data_features["FEATURE_01_MARKET_REGIME"]["applies_to"])
        self.assertIn("sector_context_model", data_features["FEATURE_02_SECTOR_CONTEXT"]["applies_to"])
        self.assertIn("source_01_market_regime", data_features["FEATURE_02_SECTOR_CONTEXT"]["applies_to"])
        self.assertIn("model_03_target_state_vector", data_features["FEATURE_03_TARGET_STATE_VECTOR"]["applies_to"])
        self.assertIn("target_state_vector_model", data_features["FEATURE_03_TARGET_STATE_VECTOR"]["applies_to"])
        self.assertNotIn("feature_snapshots", data_features["FEATURE_01_MARKET_REGIME"]["applies_to"])
        for row in rows:
            self.assertNotIn("trading-source/storage/templates/data_kinds", row["path"])
        for deleted_preview_key in {
            "MACRO_RELEASE_EVENT",
            "GDELT_ARTICLE",
            "TRADING_ECONOMICS_CALENDAR_EVENT",
            "EQUITY_BAR",
            "EQUITY_LIQUIDITY_BAR",
            "CRYPTO_BAR",
            "CRYPTO_LIQUIDITY_BAR",
            "OPTION_ACTIVITY_EVENT",
            "OPTION_ACTIVITY_EVENT_DETAIL",
            "OPTION_BAR",
            "OPTION_CHAIN_SNAPSHOT",
            "ETF_HOLDINGS_SNAPSHOT",
            "STOCK_ETF_EXPOSURE",
            "EQUITY_ABNORMAL_ACTIVITY_EVENT",
            "TRADING_EVENT",
            "EVENT_FACTOR",
            "EVENT_ANALYSIS_REPORT",
            "DATA_KIND_TEMPLATE_GENERATOR",
            "DATA_KIND_TEMPLATE_PREVIEW_FILE_PATH",
        }:
            self.assertNotIn(deleted_preview_key, by_key)
        reclassified_data_kind_keys = {
            "ETF_CONSTITUENT_WEIGHT",
            "ETF_FUND_METADATA",
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
        }
        for key in reclassified_data_kind_keys:
            self.assertIn(key, by_key)
            self.assertNotEqual(by_key[key]["kind"], "data_kind")

        self.assertEqual(by_key["SNAPSHOT_TIME"]["kind"], "temporal_field")
        self.assertEqual(by_key["SNAPSHOT_TIME"]["payload"], "snapshot_time")
        self.assertIn("feature_01_market_regime", by_key["SNAPSHOT_TIME"]["applies_to"])
        self.assertNotIn("feature_snapshots", by_key["SNAPSHOT_TIME"]["applies_to"])
        payloads = {row["payload"] for row in rows}
        for generated_feature_column in {"spy_return_30m", "spy_return_1d", "spy_return_5d", "spy_return_20d"}:
            self.assertNotIn(generated_feature_column, payloads)

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

        expected_feed_capabilities = {
            "ALPACA_EQUITY_BAR",
            "ALPACA_EQUITY_NEWS",
            "ALPACA_EQUITY_LATEST_SNAPSHOT",
            "CRYPTO_TRADE",
            "CRYPTO_QUOTE",
            "CRYPTO_ORDER_BOOK",
            "OKX_CRYPTO_CANDLE",
            "EQUITY_TRADE",
            "EQUITY_QUOTE",
            "EQUITY_SNAPSHOT",
            "ETF_ISSUER_HOLDINGS",
            "GDELT_GKG_RECORD",
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
            "TRADING_ECONOMICS_CALENDAR_PAGE",
        }
        for key in expected_feed_capabilities:
            self.assertEqual(by_key[key]["kind"], "feed_capability")
        self.assertIn("01_feed_alpaca_bars", by_key["ALPACA_EQUITY_BAR"]["applies_to"])
        self.assertIn("03_feed_alpaca_news", by_key["ALPACA_EQUITY_NEWS"]["applies_to"])
        self.assertIn("02_feed_alpaca_liquidity", by_key["ALPACA_EQUITY_LATEST_SNAPSHOT"]["applies_to"])
        self.assertIn("05_feed_gdelt_news", by_key["GDELT_GKG_RECORD"]["applies_to"])
        self.assertIn("06_feed_etf_holdings", by_key["ETF_ISSUER_HOLDINGS"]["applies_to"])
        self.assertIn("07_feed_trading_economics_calendar_web", by_key["TRADING_ECONOMICS_CALENDAR_PAGE"]["applies_to"])
        for obsolete_calendar_or_macro_key in {
            "CALENDAR_DISCOVERY",
            "ECONOMIC_RELEASE_CALENDAR",
            "EQUITY_EARNINGS_CALENDAR",
            "FOMC_MEETING",
            "FOMC_MINUTES",
            "FOMC_SEP",
            "FOMC_STATEMENT",
            "MACRO_RELEASE_CALENDAR",
            "ECONOMIC_RELEASE_EVENT",
            "FOMC_CALENDAR",
            "NASDAQ_EARNINGS_CALENDAR",
            "BEA_SECRET_ALIAS",
            "BLS_SECRET_ALIAS",
            "CENSUS_SECRET_ALIAS",
            "FRED_SECRET_ALIAS",
        }:
            self.assertNotIn(obsolete_calendar_or_macro_key, by_key)
        self.assertNotIn("MACRO_RELEASE", by_key)

    def test_layer_one_artifact_chain_is_registered(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        expected = {
            "SOURCE_01_MARKET_REGIME": ("data_source", "source_01_market_regime"),
            "FEATURE_01_MARKET_REGIME": ("data_feature", "feature_01_market_regime"),
            "MODEL_01_MARKET_REGIME": ("term", "model_01_market_regime"),
            "MODEL_01_MARKET_REGIME_EXPLAINABILITY": ("term", "model_01_market_regime_explainability"),
            "MODEL_01_MARKET_REGIME_DIAGNOSTICS": ("term", "model_01_market_regime_diagnostics"),
        }
        for key, (kind, payload) in expected.items():
            self.assertEqual(rows[key]["kind"], kind)
            self.assertEqual(rows[key]["payload"], payload)

        self.assertIn("model_01_market_regime", rows["MODEL_01_MARKET_REGIME_EXPLAINABILITY"]["applies_to"])
        self.assertIn("model_01_market_regime", rows["MODEL_01_MARKET_REGIME_DIAGNOSTICS"]["applies_to"])

    def test_market_regime_etf_universe_shared_csv_columns_are_registered(self):
        shared_path = Path("/root/projects/trading-storage/main/shared/market_regime_etf_universe.csv")
        with shared_path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 47)
        self.assertEqual(
            list(rows[0].keys()),
            ["symbol", "universe_type", "model_layer", "exposure_type", "bar_grain", "fund_name", "issuer_name", "interpretation"],
        )
        self.assertEqual(rows[0]["symbol"], "AIQ")
        self.assertEqual(rows[0]["model_layer"], "layer_02_sector_context")
        self.assertEqual({row["model_layer"] for row in rows}, {"layer_01_market_regime", "layer_02_sector_context"})
        self.assertIn("RSP", {row["symbol"] for row in rows})
        self.assertIn("SHY", {row["symbol"] for row in rows})
        self.assertIn("IEF", {row["symbol"] for row in rows})
        self.assertEqual(rows[-1]["symbol"], "VIXY")

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}
        self.assertEqual(registry["MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV"]["payload"], "trading-storage/main/shared/market_regime_etf_universe.csv")
        self.assertEqual(registry["MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV"]["path"], "/root/projects/trading-storage/main/shared/market_regime_etf_universe.csv")
        expected_fields = {
            "SYMBOL": "symbol",
            "UNIVERSE_TYPE": "universe_type",
            "MODEL_LAYER": "model_layer",
            "EXPOSURE_TYPE": "exposure_type",
            "BAR_GRAIN": "bar_grain",
            "FUND_NAME": "fund_name",
            "ISSUER_NAME": "issuer_name",
            "INTERPRETATION": "interpretation",
        }
        classification_fields = {"UNIVERSE_TYPE", "MODEL_LAYER", "EXPOSURE_TYPE"}
        self.assertEqual(registry["MODEL_LAYER_LAYER_01_MARKET_REGIME"]["kind"], "term")
        self.assertEqual(registry["MODEL_LAYER_LAYER_01_MARKET_REGIME"]["payload"], "layer_01_market_regime")
        self.assertEqual(registry["MODEL_LAYER_LAYER_02_SECTOR_CONTEXT"]["kind"], "term")
        self.assertEqual(registry["MODEL_LAYER_LAYER_02_SECTOR_CONTEXT"]["payload"], "layer_02_sector_context")
        identity_fields = {"SYMBOL", "FUND_NAME", "ISSUER_NAME"}
        text_fields = {"INTERPRETATION"}
        for key, payload in expected_fields.items():
            expected_kind = "classification_field" if key in classification_fields else "identity_field" if key in identity_fields else "text_field" if key in text_fields else "field"
            self.assertEqual(registry[key]["kind"], expected_kind)
            self.assertEqual(registry[key]["payload"], payload)
            self.assertIn("market_regime_etf_universe", registry[key]["applies_to"])
            if key not in {"SYMBOL", "ISSUER_NAME", "INTERPRETATION"}:
                self.assertEqual(registry[key]["path"], "trading-storage/main/shared/market_regime_etf_universe.csv")

    def test_market_regime_relative_strength_combinations_shared_csv_is_registered(self):
        shared_path = Path("/root/projects/trading-storage/main/shared/market_regime_relative_strength_combinations.csv")
        with shared_path.open(newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 55)
        self.assertEqual(
            list(rows[0].keys()),
            [
                "combination_id",
                "combination_type",
                "model_layer",
                "numerator_symbol",
                "denominator_symbol",
                "numerator_bar_grain",
                "denominator_bar_grain",
                "feature_bar_grain",
                "interpretation",
            ],
        )
        by_id = {row["combination_id"]: row for row in rows}
        self.assertEqual(by_id["rsp_spy"]["feature_bar_grain"], "30m")
        self.assertEqual(by_id["rsp_spy"]["model_layer"], "layer_01_market_regime")
        self.assertEqual(by_id["smh_xlk"]["model_layer"], "layer_02_sector_context")
        self.assertEqual({row["model_layer"] for row in rows}, {"layer_01_market_regime", "layer_02_sector_context"})
        self.assertEqual(by_id["tlt_shy"]["combination_type"], "primary")
        self.assertEqual(by_id["ief_shy"]["combination_type"], "primary")
        self.assertEqual(by_id["smh_xlk"]["feature_bar_grain"], "1d")

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry = {row["key"]: row for row in csv.DictReader(csv_file)}
        self.assertEqual(
            registry["MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV"]["payload"],
            "trading-storage/main/shared/market_regime_relative_strength_combinations.csv",
        )
        self.assertEqual(
            registry["MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV"]["path"],
            "/root/projects/trading-storage/main/shared/market_regime_relative_strength_combinations.csv",
        )
        expected_fields = {
            "COMBINATION_ID": ("identity_field", "combination_id"),
            "COMBINATION_TYPE": ("classification_field", "combination_type"),
            "MODEL_LAYER": ("classification_field", "model_layer"),
            "NUMERATOR_SYMBOL": ("identity_field", "numerator_symbol"),
            "DENOMINATOR_SYMBOL": ("identity_field", "denominator_symbol"),
            "NUMERATOR_BAR_GRAIN": ("field", "numerator_bar_grain"),
            "DENOMINATOR_BAR_GRAIN": ("field", "denominator_bar_grain"),
            "FEATURE_BAR_GRAIN": ("field", "feature_bar_grain"),
            "INTERPRETATION": ("text_field", "interpretation"),
        }
        for key, (kind, payload) in expected_fields.items():
            self.assertEqual(registry[key]["kind"], kind)
            self.assertEqual(registry[key]["payload"], payload)
            if key not in {"INTERPRETATION", "MODEL_LAYER"}:
                self.assertEqual(registry[key]["path"], "trading-storage/main/shared/market_regime_relative_strength_combinations.csv")
            self.assertIn("market_regime_relative_strength_combinations", registry[key]["applies_to"])

    def test_registered_payload_formats_match_sql_constraint(self):
        constraint_blocks = []
        for migration in sorted(Path("scripts/registry/sql/schema_migrations").glob("*.sql")):
            text = migration.read_text()
            if "CHECK (payload_format IN (" in text:
                constraint_blocks.append(text.split("CHECK (payload_format IN (", 1)[1].split("));", 1)[0])
        self.assertTrue(constraint_blocks)
        constrained_formats = tuple(re.findall(r"'([^']+)'", constraint_blocks[-1]))

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
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
            "review_status",
            "acceptance_status",
            "test_status",
            "maintenance_status",
            "docs_status",
            "artifact_sync_policy",
        }
        retired_unaccepted_slot_status_domains = {
            "acceptance_status",
            "task_lifecycle_status",
            "review_status",
            "test_status",
            "maintenance_status",
            "docs_status",
        }
        expected_domains = {"artifact_sync_policy_type"}

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
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
        self.assertFalse(domains & retired_unaccepted_slot_status_domains)
        payloads = [row["payload"] for row in status_rows]
        self.assertEqual(len(payloads), len(set(payloads)))
        self.assertEqual(
            next(row for row in status_rows if row["payload"] == "registry_only")["key"],
            "ARTIFACT_SYNC_POLICY_TYPE_REGISTRY_ONLY",
        )

    def test_temporal_fields_are_separate_and_iso_scoped(self):
        expected_temporal_keys = {
            "AS_OF_DATE",
            "DATA_TIMESTAMP",
            "EVENT_TIME",
            "OPTION_EXPIRATION",
            "REGISTRY_ITEM_CREATED_AT",
            "REGISTRY_ITEM_UPDATED_AT",
            "SNAPSHOT_TIME",
            "AVAILABLE_TIME",
            "TRADEABLE_TIME",
            "UNDERLYING_TIMESTAMP",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
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
        self.assertNotIn("GENERATED_AT", rows)
        self.assertEqual(rows["REGISTRY_ITEM_CREATED_AT"]["applies_to"], "trading_registry")
        self.assertEqual(rows["REGISTRY_ITEM_UPDATED_AT"]["applies_to"], "trading_registry")
        self.assertEqual(rows["TIMEFRAME"]["kind"], "field")
        self.assertEqual(rows["OPTION_DAYS_TO_EXPIRATION"]["kind"], "field")
        self.assertIn("model_03_target_state_vector", rows["AVAILABLE_TIME"]["applies_to"])
        self.assertIn("target_state_vector_model", rows["TRADEABLE_TIME"]["applies_to"])

    def test_field_like_payloads_are_unique_semantic_words(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registry_rows = list(csv.DictReader(csv_file))
            field_like_rows = [
                row
                for row in registry_rows
                if row["kind"] in {"field", "identity_field", "path_field", "temporal_field", "classification_field", "text_field", "parameter_field"}
            ]
            state_vector_value_rows = [row for row in registry_rows if row["kind"] == "state_vector_value"]

        payloads = [row["payload"] for row in field_like_rows]
        self.assertEqual(len(payloads), len(set(payloads)))

        retired_unaccepted_slot_scopes = {
            "acceptance_receipt_slots",
            "completion_receipt_slots",
            "execution_key_slots",
            "maintenance_output_slots",
            "task_register_slots",
        }
        for row in field_like_rows:
            self.assertNotIn("trading-source/storage/templates/data_kinds", row["path"])
            applies_to = set(filter(None, row["applies_to"].split(";")))
            self.assertFalse({part for part in applies_to if part.endswith("_template")})
            self.assertNotIn("option_template", applies_to)
            self.assertNotIn("data_kind_template", applies_to)
            self.assertFalse(applies_to & retired_unaccepted_slot_scopes)

        by_key = {row["key"]: row for row in field_like_rows}
        expected_bar_fields = {
            "BAR_OPEN": "bar_open",
            "BAR_HIGH": "bar_high",
            "BAR_LOW": "bar_low",
            "BAR_CLOSE": "bar_close",
            "BAR_VOLUME": "bar_volume",
            "BAR_VWAP": "bar_vwap",
            "BAR_TRADE_COUNT": "bar_trade_count",
        }
        for key, payload in expected_bar_fields.items():
            self.assertIn("source_01_market_regime", by_key[key]["applies_to"])
            self.assertIn("source_03_target_state", by_key[key]["applies_to"])
            self.assertIn("source_06_position_execution", by_key[key]["applies_to"])
            self.assertEqual(by_key[key]["payload"], payload)
        self.assertEqual(by_key["TIMEFRAME"]["payload"], "timeframe")
        self.assertEqual(by_key["TARGET_CANDIDATE_ID"]["kind"], "identity_field")
        self.assertIn("model_03_target_state_vector", by_key["TARGET_CANDIDATE_ID"]["applies_to"])
        target_state_fields = {
            "TARGET_STATE_VECTOR_VERSION": "target_state_vector_version",
            "MARKET_CONTEXT_STATE_REF": "market_context_state_ref",
            "SECTOR_CONTEXT_STATE_REF": "sector_context_state_ref",
            "TARGET_STATE_VECTOR_REF": "target_state_vector_ref",
            "SOURCE_RUN_REF": "source_run_ref",
            "RUN_ID": "run_id",
        }
        for key, payload in target_state_fields.items():
            self.assertEqual(by_key[key]["payload"], payload)
        self.assertIn("feature_03_target_state_vector", by_key["RUN_ID"]["applies_to"])

        state_vector_values = {row["key"]: row for row in state_vector_value_rows}
        target_state_vector_values = {
            "MARKET_STATE_FEATURES": "market_state_features",
            "SECTOR_STATE_FEATURES": "sector_state_features",
            "TARGET_STATE_FEATURES": "target_state_features",
            "CROSS_STATE_FEATURES": "cross_state_features",
            "STATE_OBSERVATION_WINDOWS": "state_observation_windows",
            "STATE_WINDOW_SYNC_POLICY": "state_window_sync_policy",
            "FEATURE_QUALITY_DIAGNOSTICS": "feature_quality_diagnostics",
            "SECTOR_RELATIVE_DIRECTION_STATE": "sector_relative_direction_state",
            "SECTOR_TREND_QUALITY_STABILITY_STATE": "sector_trend_quality_stability_state",
            "TARGET_DIRECTION_RETURN_SHAPE": "target_direction_return_shape",
            "TARGET_TREND_QUALITY_STATE": "target_trend_quality_state",
            "TARGET_LIQUIDITY_TRADABILITY_STATE": "target_liquidity_tradability_state",
            "TARGET_VS_MARKET_RESIDUAL_DIRECTION": "target_vs_market_residual_direction",
            "TARGET_VS_SECTOR_RESIDUAL_DIRECTION": "target_vs_sector_residual_direction",
            "RELATIVE_LIQUIDITY_TRADABILITY_STATE": "relative_liquidity_tradability_state",
        }
        for key, payload in target_state_vector_values.items():
            self.assertEqual(state_vector_values[key]["payload"], payload)
        self.assertIn("feature_03_target_state_vector", state_vector_values["MARKET_STATE_FEATURES"]["applies_to"])
        self.assertIn("model_03_target_state_vector", state_vector_values["CROSS_STATE_FEATURES"]["applies_to"])
        self.assertIn("market_state_features", state_vector_values["STATE_OBSERVATION_WINDOWS"]["applies_to"])
        self.assertIn("cross_state_features", state_vector_values["STATE_WINDOW_SYNC_POLICY"]["applies_to"])
        self.assertIn("feature_03_target_state_vector", state_vector_values["FEATURE_QUALITY_DIAGNOSTICS"]["applies_to"])
        self.assertIn("sector_state_features", state_vector_values["SECTOR_RELATIVE_DIRECTION_STATE"]["applies_to"])
        self.assertIn("target_state_features", state_vector_values["TARGET_DIRECTION_RETURN_SHAPE"]["applies_to"])
        self.assertIn("cross_state_features", state_vector_values["TARGET_VS_MARKET_RESIDUAL_DIRECTION"]["applies_to"])
        for deleted_key in {
            "OPEN_PRICE",
            "HIGH_PRICE",
            "LOW_PRICE",
            "CLOSE_PRICE",
            "VOLUME",
            "VWAP",
            "TRADE_COUNT",
            "DATA_TIMEFRAME",
            "BAR_COUNT",
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
            "EVENT_CATEGORY_TYPE",
            "EXPOSURE_TYPE",
            "INFORMATION_ROLE_TYPE",
            "OPTION_RIGHT_TYPE",
            "REFERENCE_TYPE",
            "REGISTRY_ITEM_ARTIFACT_SYNC_POLICY_TYPE",
            "REGISTRY_ITEM_KIND",
            "SCOPE_TYPE",
            "SECTOR_TYPE",
            "SNAPSHOT_TYPE",
            "UNIVERSE_TYPE",
            "MODEL_LAYER",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_classification_keys:
            self.assertEqual(rows[key]["kind"], "classification_field")
            self.assertEqual(rows[key]["payload_format"], "field_name")
            if key == "MODEL_LAYER":
                self.assertIn("explicitly assigns", rows[key]["note"])
            else:
                self.assertIn("stable lowercase token", rows[key]["note"])
        self.assertNotIn("GDELT_IMPACT_SCOPE_HINT", rows)
        self.assertNotIn("OPTION_EVENT_DETAIL_SIDE_HINT", rows)
        self.assertNotIn("TRADING_ECONOMICS_CATEGORY", rows)
        self.assertNotIn("EVENT_IMPACT_SCOPE", rows)
        self.assertNotIn("TRADE_SIDE_TYPE", rows)
        self.assertNotIn("SOURCE_EVENT_TYPE", rows)
        self.assertEqual(rows["OPTION_RIGHT_TYPE"]["payload"], "option_right_type")
        vague_payloads = {"category", "type", "status", "right", "themes", "tags", "scope", "class", "outcome", "readiness"}
        classification_payloads = {
            row["payload"] for row in rows.values() if row["kind"] == "classification_field"
        }
        self.assertFalse(classification_payloads & vague_payloads)
        for row in rows.values():
            if row["kind"] == "classification_field" and row["payload"] not in {"data_kind", "kind"}:
                self.assertRegex(row["payload"], r"_(type|status|scope|policy_type|tags|class|layer)$")
        self.assertNotIn("OPTION_RIGHT", rows)
        self.assertNotIn("STATUS", rows)
        self.assertNotIn("DATA_KIND_TEMPLATE_STATUS", rows)
        self.assertEqual(rows["REGISTRY_ITEM_ARTIFACT_SYNC_POLICY_TYPE"]["payload"], "artifact_sync_policy_type")
        self.assertNotIn("ACCEPTANCE_OUTCOME", rows)
        self.assertNotIn("REVIEW_READINESS", rows)
        self.assertNotIn("REGISTRY_ITEM_ARTIFACT_SYNC_POLICY", rows)
        self.assertEqual(rows["TITLE"]["kind"], "identity_field")
        self.assertNotIn("RETURN_ZSCORE", rows)

    def test_identity_fields_are_separate_from_plain_fields(self):
        expected_identity_keys = {
            "ID",
            "SYMBOL",
            "TITLE",
            "EVENT_ID",
            "ETF_SYMBOL",
            "ETF_HOLDING_SYMBOL",
            "ETF_HOLDING_NAME",
            "ISSUER_NAME",
            "OPTION_SYMBOL",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_identity_keys:
            self.assertEqual(rows[key]["kind"], "identity_field")
            self.assertIn(rows[key]["payload_format"], {"field_name", "text"})
            self.assertIn("Identity value", rows[key]["note"])
        for vague_key in {"ISSUER", "OPTION_EVENT_DETAIL_PROVIDER", "OPTION_EVENT_DETAIL_STANDARD_SOURCE"}:
            self.assertNotIn(vague_key, rows)
        self.assertEqual(rows["ISSUER_NAME"]["payload"], "issuer_name")
        self.assertNotIn("OPTION_EVENT_DETAIL_SOURCE_PROVIDER_NAME", rows)
        self.assertNotIn("TIMELINE_HEADLINE", rows)

    def test_path_fields_are_separate_from_identity_fields(self):
        expected_path_keys = {
            "REGISTRY_ITEM_PATH",
            "EVENT_REFERENCE",
        }
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in expected_path_keys:
            self.assertEqual(rows[key]["kind"], "path_field")
            self.assertIn("Path value", rows[key]["note"])
        self.assertNotIn("URL", rows)
        self.assertNotIn("EVENT_SOURCE_REF", rows)
        self.assertNotIn("EVENT_LINK_URL", rows)
        self.assertNotIn("EVENT_ANALYSIS_REPORT_URL", rows)
        self.assertNotIn("EVENT_REPORT_URL", rows)
        self.assertNotIn("EVENT_REPORT_JSON_URL", rows)
        self.assertNotIn("EVENT_SOURCE_REFERENCE", rows)
        self.assertNotIn("SOURCE_REFERENCES", rows)
        self.assertEqual(rows["EVENT_REFERENCE"]["payload"], "reference")
        self.assertNotIn("TRADING_ECONOMICS_REFERENCE_PERIOD", rows)

    def test_text_fields_are_separate_from_plain_fields(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        for key in {
            "REGISTRY_ITEM_NOTE",
            "SUMMARY",
        }:
            self.assertEqual(rows[key]["kind"], "text_field")
            self.assertIn("Text value", rows[key]["note"])

    def test_parameter_fields_are_separate_from_text_and_plain_fields(self):
        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            rows = {row["key"]: row for row in csv.DictReader(csv_file)}

        self.assertNotIn("DATA_TASK_PARAMS", rows)

    def test_registered_artifact_sync_policies_match_sql_constraint(self):
        constraint_blocks = []
        for migration in sorted(Path("scripts/registry/sql/schema_migrations").glob("*.sql")):
            text = migration.read_text()
            if "CHECK (artifact_sync_policy IN (" in text:
                constraint_blocks.append(
                    text.split("CHECK (artifact_sync_policy IN (", 1)[1].split("));", 1)[0]
                )
        self.assertTrue(constraint_blocks)
        constrained_policies = tuple(re.findall(r"'([^']+)'", constraint_blocks[-1]))

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
            registered_policies = tuple(
                row["payload"]
                for row in csv.DictReader(csv_file)
                if row["kind"] == "status_value"
                and row["applies_to"] == "artifact_sync_policy_type"
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

        with Path("scripts/registry/current.csv").open(newline="") as csv_file:
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
                        key="TRADING_MANAGER_REPO",
                        payload_format="repo_name",
                        payload="trading-manager",
                        path="/root/projects/trading-manager",
                        applies_to=None,
                    )
                ]
            }

        reader = RegistryReader(query)
        self.assertEqual(reader.get_key_by_id("rep_H6S3V8LA"), "TRADING_MANAGER_REPO")
        self.assertEqual(reader.get_payload_by_id("rep_H6S3V8LA"), "trading-manager")
        self.assertEqual(reader.get_path_by_id("rep_H6S3V8LA"), "/root/projects/trading-manager")
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
            return [create_row(kind="repo", key="TRADING_MANAGER_REPO", payload="trading-manager")]

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
                    "kind": "source_secret_file",
                    "use": "git operations",
                    "fields": {"pat": "GitHub personal access token"},
                }
            },
            "github",
            "/root/secrets/registry.json",
        )
        self.assertEqual(entry["alias"], "github")
        self.assertEqual(entry["path"], "/root/secrets/github.json")
        self.assertEqual(entry["kind"], "source_secret_file")

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
                            "kind": "source_secret_file",
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
