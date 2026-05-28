"""
Tests for scripts/fetch_gene_symbols.py and scripts/fetch_disease_names.py.

Both scripts hit external HTTP APIs. We mock requests.post at the module
boundary so CI never depends on Ensembl or Open Targets availability.

Tested surface: resolve_batch() in both scripts.
get_target_ids() / get_disease_ids() are thin DuckDB wrappers — covered
implicitly by the agent tool tests that already exercise mart_target_rankings.
"""

import pytest
from unittest.mock import MagicMock

from scripts.fetch_gene_symbols import resolve_batch as resolve_gene_batch
from scripts.fetch_disease_names import resolve_batch as resolve_disease_batch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_response(status_code: int, json_data=None) -> MagicMock:
    """Build a mock requests.Response with the given status and JSON body."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


# ---------------------------------------------------------------------------
# fetch_gene_symbols — resolve_batch
# ---------------------------------------------------------------------------

class TestResolveGeneBatch:

    def test_parses_display_name_and_strips_source_annotation(self, mocker):
        mocker.patch(
            "scripts.fetch_gene_symbols.requests.post",
            return_value=make_response(200, {
                "ENSG00000134982": {"display_name": "APC [Source:HGNC;Acc:583]", "external_name": "APC"},
            })
        )
        result = resolve_gene_batch(["ENSG00000134982"])
        assert result["ENSG00000134982"] == "APC"

    def test_falls_back_to_external_name_when_display_name_empty(self, mocker):
        mocker.patch(
            "scripts.fetch_gene_symbols.requests.post",
            return_value=make_response(200, {
                "ENSG00000134982": {"display_name": "", "external_name": "APC"},
            })
        )
        result = resolve_gene_batch(["ENSG00000134982"])
        assert result["ENSG00000134982"] == "APC"

    def test_falls_back_to_ensembl_id_when_both_names_empty(self, mocker):
        mocker.patch(
            "scripts.fetch_gene_symbols.requests.post",
            return_value=make_response(200, {
                "ENSG00000134982": {"display_name": "", "external_name": ""},
            })
        )
        result = resolve_gene_batch(["ENSG00000134982"])
        assert result["ENSG00000134982"] == "ENSG00000134982"

    def test_null_response_for_id_returns_empty_string(self, mocker):
        # Retired/deprecated Ensembl IDs come back as null in the API response
        mocker.patch(
            "scripts.fetch_gene_symbols.requests.post",
            return_value=make_response(200, {
                "ENSG00000000000": None,
            })
        )
        result = resolve_gene_batch(["ENSG00000000000"])
        assert result["ENSG00000000000"] == ""

    def test_429_exhausted_returns_empty_strings(self, mocker):
        mocker.patch(
            "scripts.fetch_gene_symbols.requests.post",
            return_value=make_response(429)
        )
        mocker.patch("scripts.fetch_gene_symbols.time.sleep")  # don't actually wait
        result = resolve_gene_batch(["ENSG00000134982"])
        assert result == {"ENSG00000134982": ""}

    def test_non_200_non_429_returns_empty_strings_immediately(self, mocker):
        post = mocker.patch(
            "scripts.fetch_gene_symbols.requests.post",
            return_value=make_response(500)
        )
        result = resolve_gene_batch(["ENSG00000134982"])
        assert result == {"ENSG00000134982": ""}
        assert post.call_count == 1  # no retries on 500


# ---------------------------------------------------------------------------
# fetch_disease_names — resolve_batch
# ---------------------------------------------------------------------------

class TestResolveDiseasesBatch:

    def test_parses_diseases_list_correctly(self, mocker):
        mocker.patch(
            "scripts.fetch_disease_names.requests.post",
            return_value=make_response(200, {
                "data": {
                    "diseases": [
                        {"id": "EFO_1001951", "name": "colorectal carcinoma"},
                        {"id": "EFO_0000181", "name": "breast carcinoma"},
                    ]
                }
            })
        )
        result = resolve_disease_batch(["EFO_1001951", "EFO_0000181"])
        assert result["EFO_1001951"] == "colorectal carcinoma"
        assert result["EFO_0000181"] == "breast carcinoma"

    def test_fills_empty_string_for_ids_not_returned_by_api(self, mocker):
        # API returns only one of two requested IDs
        mocker.patch(
            "scripts.fetch_disease_names.requests.post",
            return_value=make_response(200, {
                "data": {
                    "diseases": [
                        {"id": "EFO_1001951", "name": "colorectal carcinoma"},
                    ]
                }
            })
        )
        result = resolve_disease_batch(["EFO_1001951", "EFO_0000181"])
        assert result["EFO_1001951"] == "colorectal carcinoma"
        assert result["EFO_0000181"] == ""

    def test_429_exhausted_returns_empty_strings(self, mocker):
        mocker.patch(
            "scripts.fetch_disease_names.requests.post",
            return_value=make_response(429)
        )
        mocker.patch("scripts.fetch_disease_names.time.sleep")
        result = resolve_disease_batch(["EFO_1001951"])
        assert result == {"EFO_1001951": ""}

    def test_non_200_non_429_returns_empty_strings_immediately(self, mocker):
        post = mocker.patch(
            "scripts.fetch_disease_names.requests.post",
            return_value=make_response(400)
        )
        result = resolve_disease_batch(["EFO_1001951"])
        assert result == {"EFO_1001951": ""}
        assert post.call_count == 1