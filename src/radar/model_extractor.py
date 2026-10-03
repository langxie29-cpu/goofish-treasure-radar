"""Candidate models, not authoritative identification. Preserve meaningful hyphens."""
import re
import unicodedata
from .schemas import DetectedModel

CANDIDATE = re.compile(r'(?<![A-Za-z0-9])(?:[A-Za-z]{1,8}[- ]?)?\d{1,6}[A-Za-z]{0,5}(?:[- ][A-Za-z0-9]{1,8})?(?![A-Za-z0-9])')
TECH = re.compile(r'^(?:\d+(?:V|HZ|MHZ|GHZ|KHZ|W|MAH|GB|TB|MM|CM)|\d+[X×]\d+|USB[- ]?\d+|HDMI[- ]?\d+|IP\d+)$', re.I)


def extract_models(text: str) -> list[DetectedModel]:
    text = unicodedata.normalize('NFKC', text or '').replace('–', '-').replace('—', '-')
    found = {}
    for match in CANDIDATE.finditer(text):
        model = match.group().upper().strip()
        # Must contain alphabetic prefix and digits; specifications and dates fail this gate.
        if not re.match(r'^[A-Z]', model) or not re.search(r'\d', model) or TECH.fullmatch(model):
            continue
        model = re.sub(r'(?<=[A-Z]) (?=\d)', '-', model)
        if len(model) < 4 or len(model) > 24:
            continue
        if model.startswith(('DDR', 'PCIE', 'RGB', 'DC', 'AC')) and not '-' in model:
            continue
        found.setdefault(model, DetectedModel(model, 80 if '-' in model or re.search(r'\d[A-Z]', model) else 65))
    return list(found.values())
