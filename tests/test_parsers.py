import pytest
from dashboard.parsers import parse_agent_response


class TestParseAgentResponse:

    def test_parses_numbered_targets_with_ensembl_id(self):
        raw = (
            "Here are the top targets for colorectal cancer:\n"
            "1. APC (ENSG00000134982) — score: 0.72\n"
            "2. ERBB2 (ENSG00000141736) — score: 0.42\n"
        )
        result = parse_agent_response(raw)
        assert len(result["targets"]) == 2
        assert result["targets"][0]["gene"] == "APC"
        assert result["targets"][0]["ensembl_id"] == "ENSG00000134982"
        assert result["targets"][0]["score"] == pytest.approx(0.72)

    def test_parses_targets_without_ensembl_id(self):
        # Agent sometimes omits Ensembl ID -- parser should handle it
        raw = "1. APC — score: 0.72\n2. ERBB2 — score: 0.42\n"
        result = parse_agent_response(raw)
        assert len(result["targets"]) == 2
        assert result["targets"][0]["ensembl_id"] == ""

    def test_extracts_summary_line(self):
        raw = (
            "The top drug targets for colorectal carcinoma based on Open Targets data are:\n"
            "1. APC (ENSG00000134982) — score: 0.72\n"
        )
        result = parse_agent_response(raw)
        assert "colorectal carcinoma" in result["summary"]

    def test_empty_string_returns_empty_structure(self):
        result = parse_agent_response("")
        assert result == {"summary": "", "targets": [], "notes": []}

    def test_no_targets_returns_empty_targets_list(self):
        raw = "I could not find any targets for that disease ID."
        result = parse_agent_response(raw)
        assert result["targets"] == []

    def test_parenthetical_numbering_style(self):
        # Agent sometimes uses "1)" instead of "1."
        raw = "1) APC (ENSG00000134982) — score: 0.72\n"
        result = parse_agent_response(raw)
        assert len(result["targets"]) == 1
        assert result["targets"][0]["gene"] == "APC"

    @pytest.mark.parametrize("disease_line,expected_gene", [
        ("1. APC (ENSG00000134982) — score: 0.72", "APC"),
        ("1. ERBB2 (ENSG00000141736) — score: 0.42", "ERBB2"),
        ("1. TP53 (ENSG00000141510) — score: 0.91", "TP53"),
    ])
    def test_gene_extraction_across_genes(self, disease_line, expected_gene):
        result = parse_agent_response(disease_line)
        assert result["targets"][0]["gene"] == expected_gene