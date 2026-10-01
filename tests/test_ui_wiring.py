import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates"
SCRIPT_DIR = ROOT / "static" / "js"
BUILT_IN_HANDLERS = {
    "clearTimeout",
    "document",
    "event",
    "if",
    "requestAnimationFrame",
    "setTimeout",
    "this",
    "window",
}


def test_inline_controls_call_defined_functions_and_broken_filters_stay_fixed():
    templates = list(TEMPLATE_DIR.glob("*.html"))
    scripts = list(SCRIPT_DIR.rglob("*.js"))
    sources = [path.read_text(encoding="utf-8", errors="ignore") for path in templates + scripts]
    combined_source = "\n".join(sources)
    defined_functions = set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", combined_source))
    defined_functions.update(
        re.findall(
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
            combined_source,
        )
    )

    missing_handlers = []
    for path in templates:
        source = path.read_text(encoding="utf-8", errors="ignore")
        handlers = re.findall(
            r"\bon(?:click|submit|change|input|keyup|keydown|focus|blur)\s*=\s*['\"]([^'\"]+)",
            source,
            flags=re.IGNORECASE,
        )
        for handler in handlers:
            match = re.match(r"\s*([A-Za-z_$][\w$]*)\s*\(", handler)
            if match and match.group(1) not in defined_functions | BUILT_IN_HANDLERS:
                missing_handlers.append(f"{path.relative_to(ROOT)}: {handler}")

    admin_dashboard = (TEMPLATE_DIR / "admin_dashboard.html").read_text(encoding="utf-8")
    rules_matrix = (TEMPLATE_DIR / "rules_matrix.html").read_text(encoding="utf-8")
    app_script = (SCRIPT_DIR / "app.js").read_text(encoding="utf-8")

    assert not missing_handlers, "Undefined inline event handlers: " + "; ".join(missing_handlers)
    assert "filterByTab('Refund', event)" in admin_dashboard
    assert 'oninput="filterRuleTable()"' in rules_matrix
    assert "function filterRuleTable()" in app_script
    assert "No rules match this search." in app_script
