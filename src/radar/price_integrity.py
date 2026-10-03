"""Explainable price credibility, separate from interest or purchase decisions."""
import re
from .money_extractor import extract_money
from .schemas import Item, MoneyMention, PriceIntegrityResult, PriceType


def analyze_price(item: Item, mentions: list[MoneyMention] | None = None) -> PriceIntegrityResult:
    mentions = extract_money(item.text) if mentions is None else mentions
    text = re.sub(r'(?:无需|不用|不收|不需要|无)(?:定金|订金)', '', item.text)
    listed = item.listed_price
    flags = []
    sale = [m.amount for m in mentions if m.role in {'sale', 'minimum', 'total'}]
    totals = [m.amount for m in mentions if m.role == 'total']
    lo = min(sale) if sale else listed
    hi = max(sale) if sale else listed
    kind, confidence, reason = PriceType.REAL_PRICE, 85, '标价未发现交易性质或正文价格冲突；规则判断，未验证卖家承诺。'
    # Specific transaction types have precedence; never infer full-item cost from rental/deposit prices.
    if re.search(r'求购|高价回收|收购|回收(?:示波器|仪器|设备|电脑|电子)|长期回收', text):
        kind, confidence, reason = PriceType.WANTED_PRICE, 2, '求购/回收信息，标价不是出售主要商品的价格。'
        lo = hi = None
    elif re.search(r'租赁|出租|日租|月租|(?:元|块)?\s*[/／]\s*(?:天|日|月|小时)|每天\s*\d', text):
        kind, confidence, reason = PriceType.RENTAL_PRICE, 5, '租赁或按时计价，不能当作购买价格。'
        lo = hi = None
    elif re.search(r'(?<!无)(?:定金|订金)', text):
        kind, confidence, reason = PriceType.DEPOSIT_PRICE, 5, '标价可能是定金，优先采用明确总价；不会把定金当全价。'
        lo, hi = (min(totals), max(totals)) if totals else (None, None)
    elif re.search(r'尾款|配件价|单件价|最低配置|低配价|起步价|起售|整机另议|整机另询|(?:是|为|仅|只卖).{0,10}(?:电源板|配件|空壳|主板).{0,5}(?:价格|价)|(?:元|块)[/／](?:个|件|只)|(?:\d+\s*元?)\s*起', text):
        kind, confidence, reason = PriceType.PARTIAL_PRICE, 10, '配件、尾款、单件或最低配置价格，主商品价格需核实。'
        lo, hi = (min(totals), max(totals)) if totals else (None, None)
    elif re.search(r'价格随便挂|随便标|随便挂|占位|标价不算|标价非实价|价格另议|价格私聊|具体私聊|具体价格.{0,5}(?:私聊|咨询)|勿直接拍|不要直接拍|拍下不发货|引流', text):
        kind, confidence, reason = PriceType.PLACEHOLDER_PRICE, 5, '有明确占位、私聊定价或禁止直接拍信号。'
        lo, hi = (min(sale), max(sale)) if sale else (None, None)
    elif listed is None:
        kind, confidence, reason = PriceType.UNCERTAIN, 0, '缺失有效页面标价。'
        flags.append('MISSING_LISTED_PRICE')
    elif sale and (listed < min(sale)*0.7 or listed > max(sale)*1.3):
        kind, confidence, reason = PriceType.PLACEHOLDER_PRICE, 15, '页面标价与正文交易价格明显不一致。'
        flags.append('PRICE_MISMATCH')
    elif re.search(r'可.{0,1}刀|小刀|可议价|可商量|可谈|可议', text):
        kind, confidence, reason = PriceType.NEGOTIABLE_REAL_PRICE, 85, '仅有正常议价信号，可刀不等于假价格。'
    elif listed in {0, 1, 9.9, 99, 999, 9999} and not any(m.amount == listed for m in mentions if m.role != 'reference'):
        kind, confidence, reason = PriceType.UNCERTAIN, 45, '常见占位数值但无明确假价证据；保留低价机会，需核实。'
        flags.append('COMMON_PLACEHOLDER_VALUE')
    if kind not in {PriceType.REAL_PRICE, PriceType.NEGOTIABLE_REAL_PRICE, PriceType.UNCERTAIN}:
        flags.append(kind.value)
    if listed is not None and sale and (listed < min(sale)*0.7 or listed > max(sale)*1.3):
        if 'PRICE_MISMATCH' not in flags:
            flags.append('PRICE_MISMATCH')
    if re.search(r'不会测试|未测试|不知道|不懂|故障|按废品', text):
        flags.append('CONDITION_UNVERIFIED')
    return PriceIntegrityResult(kind, listed, lo, hi, confidence, flags, reason,
                                list(dict.fromkeys(m.amount for m in mentions)))
