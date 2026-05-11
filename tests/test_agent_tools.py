import pytest
from agent.target_discovery_agent import get_top_targets, list_available_diseases


class TestGetTopTargets:

    def test_returns_top_targets_for_known_disease(self, mart_db):
        result = get_top_targets.invoke({"disease_id": "EFO_1001951"})
        assert "APC" in result
        assert "ERBB2" in result

    def test_respects_top_n_limit(self, mart_db):
        result = get_top_targets.invoke({"disease_id": "EFO_1001951", "top_n": 1})
        # Only rank 1 should appear -- APC yes, ERBB2 no
        assert "APC" in result
        assert "ERBB2" not in result

    def test_unknown_disease_returns_not_found_message(self, mart_db):
        result = get_top_targets.invoke({"disease_id": "EFO_9999999"})
        assert "No targets found" in result

    def test_result_contains_score_column(self, mart_db):
        result = get_top_targets.invoke({"disease_id": "EFO_1001951"})
        assert "association_score" in result

    def test_result_contains_evidence_count(self, mart_db):
        result = get_top_targets.invoke({"disease_id": "EFO_1001951"})
        assert "evidence_count" in result


class TestListAvailableDiseases:

    def test_returns_both_diseases(self, mart_db):
        result = list_available_diseases.invoke({"limit": 20})
        assert "EFO_1001951" in result
        assert "EFO_0000181" in result

    def test_respects_limit(self, mart_db):
        result = list_available_diseases.invoke({"limit": 1})
        # Breast carcinoma has more targets (2 vs 3 actually -- colorectal has 3)
        # Only one disease ID should appear
        lines = [l for l in result.strip().split("\n") if "EFO_" in l]
        assert len(lines) == 1

    def test_returns_target_count_column(self, mart_db):
        result = list_available_diseases.invoke({"limit": 20})
        assert "target_count" in result