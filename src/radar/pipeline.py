"""Zero-API-cost evaluation, with persistent content-based deduplication."""
import asyncio
import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Protocol
from .interest_rules import score_interest
from .model_extractor import extract_models
from .money_extractor import extract_money
from .price_integrity import analyze_price
from .rule_filter import normalize_item
from .schemas import EvaluationResult, Item
from .storage import EvaluationStore

ENGINE_VERSION = '1.0.0'


class AIEvaluator(Protocol):
    """Future explicit, opt-in stage; MVP does not instantiate or invoke it."""
    async def evaluate(self, item: Item, rules: EvaluationResult) -> dict: ...


class Radar:
    def __init__(self, store: EvaluationStore | None = None, *, interest_threshold: int = 50):
        if not 0 <= interest_threshold <= 100:
            raise ValueError('interest_threshold must be in [0, 100]')
        self.store = store
        self.interest_threshold = interest_threshold

    async def evaluate(self, item) -> EvaluationResult:
        return await asyncio.to_thread(self.evaluate_sync, item)

    def evaluate_sync(self, record) -> EvaluationResult:
        item = normalize_item(record)
        encoded = json.dumps({'item': asdict(item), 'interest_threshold': self.interest_threshold},
                             ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
        fingerprint = hashlib.sha256(encoded).hexdigest()
        if self.store:
            cached = self.store.cached(item.item_id, fingerprint, ENGINE_VERSION)
            if cached:
                return replace(cached, duplicate=True)
        money = extract_money(item.text)
        price = analyze_price(item, money)
        models = extract_models(item.text)
        interest = score_interest(item.text, len(models))
        candidate = interest.rule_interest_score >= self.interest_threshold
        # Suspicious prices do not discard rare technology; label them instead.
        reason = f'{interest.reason} {price.reason} ' + ('值得点开核实，不代表值得购买。' if candidate else '暂未达到点开兴趣阈值。')
        result = EvaluationResult(item.item_id, item.title, item.listed_price, price.price_type,
                                  price.price_confidence, price.effective_price_min, price.effective_price_max,
                                  interest.rule_interest_score, models, price.risk_flags, interest.interest_flags,
                                  reason, datetime.now(timezone.utc).isoformat(), price.mentioned_prices,
                                  fingerprint, ENGINE_VERSION, candidate)
        if self.store and not self.store.save(result):
            return replace(result, duplicate=True)
        return result
