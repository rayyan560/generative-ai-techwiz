import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _theme_variables(stylesheet, selector):
    variables = {}
    pattern = re.escape(selector) + r"\s*\{([^{}]*)\}"
    for match in re.finditer(pattern, stylesheet, flags=re.DOTALL):
        variables.update(dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", match.group(1))))
    return variables


def _resolve_hex(value, variables, depth=0):
    if depth > 8:
        raise ValueError("CSS variable reference is cyclic")
    reference = re.fullmatch(r"var\((--[\w-]+)\)", value.strip())
    if reference:
        return _resolve_hex(variables[reference.group(1)], variables, depth + 1)
    color = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", color):
        color = "#" + "".join(character * 2 for character in color[1:])
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError(f"Expected a solid hex color, got {value}")
    return tuple(int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))


def _relative_luminance(color):
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in color]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))


def _contrast_ratio(foreground, background):
    first, second = sorted((_relative_luminance(foreground), _relative_luminance(background)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def test_primary_theme_text_and_status_colors_meet_wcag_aa_on_page_backgrounds():
    stylesheet = (ROOT / "static" / "css" / "style.css").read_text(encoding="utf-8")
    dark = _theme_variables(stylesheet, ":root")
    light = {**dark, **_theme_variables(stylesheet, '[data-theme="light"]')}
    checks = ("--text-heading", "--text-body", "--text-muted", "--primary", "--success", "--warning", "--danger", "--info")

    for name, variables in (("dark", dark), ("light", light)):
        background = _resolve_hex(variables["--bg-dark"], variables)
        for token in checks:
            foreground = _resolve_hex(variables[token], variables)
            ratio = _contrast_ratio(foreground, background)
            assert ratio >= 4.5, f"{name} theme {token} contrast is {ratio:.2f}:1"


def test_primary_and_success_button_text_meet_wcag_aa_across_gradients():
    stylesheet = (ROOT / "static" / "css" / "style.css").read_text(encoding="utf-8")
    variables = _theme_variables(stylesheet, ":root")

    for background_token in ("--primary-gradient", "--success-gradient"):
        endpoints = re.findall(r"#[0-9a-fA-F]{3,6}", variables[background_token])
        assert len(endpoints) >= 2, f"{background_token} should expose two testable color endpoints"
        foreground = _resolve_hex(variables["--primary-text"], variables)
        for endpoint in endpoints:
            background = _resolve_hex(endpoint, variables)
            ratio = _contrast_ratio(foreground, background)
            assert ratio >= 4.5, f"--primary-text on {background_token} endpoint {endpoint} is {ratio:.2f}:1"


def test_critical_action_colors_meet_wcag_aa_in_dark_and_light_themes():
    stylesheet = (ROOT / "static" / "css" / "style.css").read_text(encoding="utf-8")
    dark = _theme_variables(stylesheet, ":root")
    light = {**dark, **_theme_variables(stylesheet, '[data-theme="light"]')}
    pairs = (("#be123c", "#ffffff"), ("#047857", "#ffffff"), ("--cream", "--ink"))

    for theme_name, variables in (("dark", dark), ("light", light)):
        for background_token, foreground_token in pairs:
            background = _resolve_hex(variables.get(background_token, background_token), variables)
            foreground = _resolve_hex(variables.get(foreground_token, foreground_token), variables)
            ratio = _contrast_ratio(foreground, background)
            assert ratio >= 4.5, f"{theme_name} theme {foreground_token} on {background_token} is {ratio:.2f}:1"


def test_communication_bubbles_use_theme_aware_foreground_colors():
    communication = (ROOT / "templates" / "communication.html").read_text(encoding="utf-8")

    assert ".wa-client-avatar" in communication and "color: var(--ink)" in communication
    assert ".wa-msg-out" in communication and "color: var(--ink)" in communication
    assert ".wa-qchip" in communication and "color: var(--text-heading)" in communication
