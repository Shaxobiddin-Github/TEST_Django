from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

# Only match real LaTeX: $...$, \\frac, \\sqrt, \\sum, \\int, etc.
LATEX_PATTERN = re.compile(r'(\\(frac|sqrt|sum|int|cdot|times|div|leq|geq|neq|approx|pm|mp|infty|pi|phi|alpha|beta|gamma|theta|lambda|mu|sigma|omega|mathbb|mathcal|vec|overrightarrow|overleftarrow|bar|hat|underline|displaystyle|to|rightarrow|leftarrow|uparrow|downarrow|Rightarrow|Leftarrow|Leftrightarrow|dots|ldots|cdots|vdots|ddots|log|ln|exp|sin|cos|tan|csc|sec|cot|arcsin|arccos|arctan|mathrm|sum|prod|int|iint|iiint|lim)|\$.*?\$)')

def contains_latex(value):
    """
    Returns True if the string contains real LaTeX/math markers, else False.
    """
    if not isinstance(value, str):
        return False
    return bool(LATEX_PATTERN.search(value))

register.filter('contains_latex', contains_latex)

# Heuristic inline renderer: wraps only LaTeX snippets (e.g., \sqrt{...}, \frac{...}{...}, x^2)
LATEX_FRAC = re.compile(r"\\frac\s*\{[^{}]+\}\s*\{[^{}]+\}")
# Support optional index: \sqrt[3]{...}
LATEX_SQRT = re.compile(r"\\sqrt\s*(\[[^\[\]]+\])?\s*\{[^{}]+\}")
LATEX_SIMPLE_POWER = re.compile(r"(?<![\\$])\b([A-Za-z])\s*\^\s*(\d+)(?![A-Za-z])")

def render_latex_inline(value: str) -> str:
    """
    Wrap only LaTeX parts with \( ... \) so normal text stays normal.
    If the text already contains math delimiters ($...$, \(...\), \[...\]), return as-is.
    """
    if not isinstance(value, str):
        return value
    # If already delimited, do nothing
    if '$' in value or '\\(' in value or '\\[' in value:
        return mark_safe(value)

    s = value

    # Wrap \frac{..}{..}
    s = LATEX_FRAC.sub(lambda m: f"\\({m.group(0)}\\)", s)
    # Wrap \sqrt{..}
    s = LATEX_SQRT.sub(lambda m: f"\\({m.group(0)}\\)", s)
    # Wrap simple x^2 like patterns (avoid already in math)
    s = LATEX_SIMPLE_POWER.sub(lambda m: f"\\({m.group(1)}^{m.group(2)}\\)", s)

    # Conservative: return string with only the specific LaTeX fragments wrapped
    return mark_safe(s)

register.filter('render_latex_inline', render_latex_inline)
