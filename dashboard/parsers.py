import re


def parse_agent_response(raw: str) -> dict:
    """
    Extract structured data from agent response string.

    Returns dict with keys:
        summary  (str)         -- first substantial line before any targets
        targets  (list[dict])  -- each has: gene, ensembl_id, score
        notes    (list[str])   -- remaining lines after targets

    Parsing strategy: look for lines matching the pattern
        "1. GENE (ENSGxxxxxxxx) — score: 0.71"
    Everything before the first match is the summary.
    Everything after is notes.
    """
    lines = raw.strip().split("\n")
    targets = []
    notes = []
    summary = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(
            r"^\d+[\.\)]\s+(\w+)\s*\(?(ENSG\d+)?\)?.*?(\d+\.\d+)", line
        )
        if match:
            targets.append({
                "gene": match.group(1),
                "ensembl_id": match.group(2) or "",
                "score": float(match.group(3)),
            })
        elif len(targets) == 0 and len(line) > 20:
            summary = line
        else:
            notes.append(line)

    return {"summary": summary, "targets": targets, "notes": notes}