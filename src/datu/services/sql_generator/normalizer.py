# datu/services/sql_generation/normalizer.py
import re


def normalize_for_preview(content: str) -> str:
    """
    Force the legacy format the UI expects so preview regex matches:
    - Normalize any '### Query Name:' (and variants) to 'Query name:'
    - Remove Complexity/Estimated bullets
    - Collapse blank lines between 'Query name: ...' and the following ```sql fence
    """
    if not content:
        return content

    out = content

    # Headings -> legacy header
    out = re.sub(
        r"^(?:\s*#{1,6}\s*)?Query\s*Name:\s*",
        "Query name: ",
        out,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # Drop complexity bullets the agent sometimes adds
    out = re.sub(r"^\s*-\s*\*\*Complexity\*\*:[^\n]*\n?", "", out, flags=re.MULTILINE | re.IGNORECASE)
    out = re.sub(r"^\s*-\s*\*\*Estimated\s+Execution\s+Time\*\*:[^\n]*\n?", "", out, flags=re.MULTILINE | re.IGNORECASE)

    # Ensure header followed immediately by code fence
    out = re.sub(
        r"(Query name:\s*[^\n]+)\n\s*\n\s*```sql",
        r"\1\n```sql",
        out,
        flags=re.IGNORECASE,
    )

    return out
