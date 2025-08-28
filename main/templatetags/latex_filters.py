from django import template
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
