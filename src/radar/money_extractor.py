"""Contextual CNY amounts; standalone specifications are deliberately ignored."""
import re
import unicodedata
from .schemas import MoneyMention

NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?'
BOUNDARY = r'(?<![A-Za-z0-9.\-])'
PATTERN = re.compile(
    rf'{BOUNDARY}(?:'
    rf'[¥￥]\s*(?P<currency>{NUMBER})|'
    rf'(?P<suffix>{NUMBER})\s*(?:元|块钱?|包邮|到手|定金|订金|尾款|出(?=售|掉|[，,。！!、\s]|$))|'
    rf'(?:最低|底价|到手|总价|售价|价格|定金|订金|尾款|整机价?|出)\s*[:：]?\s*(?P<prefix>{NUMBER})'
    rf')', re.I)
TECH_SUFFIX = re.compile(r'\s*(?:[kmg]?hz|[kmg]?v|mah|[kmg]?w|gb|tb|mm|cm|年|月|寸|英寸|[x×*]\s*\d)', re.I)


def extract_money(text: str) -> list[MoneyMention]:
    text = unicodedata.normalize('NFKC', text or '')
    mentions = []
    for match in PATTERN.finditer(text):
        group = next(k for k in ('currency', 'suffix', 'prefix') if match.group(k))
        start, end = match.span(group)
        if TECH_SUFFIX.match(text[end:]):
            continue
        before = text[max(0, match.start()-8):match.start()]
        after = text[match.end():match.end()+8]
        local = before + match.group() + after
        role = 'sale'
        # Attribution is local, never across punctuation into another price clause.
        clause = re.split(r'[，,。;；\n]', local)
        context = next((c for c in clause if match.group() in c), match.group())
        if re.search(r'原价|购入|买入|当年|运费|邮费|押金|退款', context):
            role = 'reference'
        elif re.search(r'总价|整机价|全套价', context):
            role = 'total'
        elif re.search(r'定金|订金', context):
            role = 'deposit'
        elif re.search(r'尾款', context):
            role = 'balance'
        elif re.search(r'最低|底价|到手', context):
            role = 'minimum'
        mentions.append(MoneyMention(float(match.group(group).replace(',', '')),
                                     match.group(), match.start(), match.end(), role))
    return mentions
