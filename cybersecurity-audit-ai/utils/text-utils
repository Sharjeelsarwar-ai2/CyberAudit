import re

_SIGNAL = re.compile(
    r"\b(CRITICAL|HIGH|MEDIUM|LOW|NON-COMPLIANT|PARTIAL)\b|CVE-|OWASP|\bA\d{2}\b",
    re.IGNORECASE,
)


def condense(text: str, max_chars: int) -> str:
    """Shrink an agent's output to its highest-signal lines (headings, table rows,
    severity lines) so it can be passed to the next agent without blowing the token budget."""
    text = text or ""
    if len(text) <= max_chars:
        return text

    lines = [
        ln.rstrip()[:220]
        for ln in text.splitlines()
        if ln.strip() and not re.fullmatch(r"[\s|:\-]+", ln)
    ]
    chosen, used = set(), 0

    def add_pass(predicate):
        nonlocal used
        for i, ln in enumerate(lines):
            if i in chosen or not predicate(ln):
                continue
            if used + len(ln) + 1 > max_chars:
                continue
            chosen.add(i)
            used += len(ln) + 1

    add_pass(lambda ln: ln.lstrip().startswith("#"))
    add_pass(lambda ln: ln.lstrip().startswith("|") or bool(_SIGNAL.search(ln)))
    add_pass(lambda ln: True)

    return "\n".join(lines[i] for i in sorted(chosen)) + "\n[...condensed...]"
