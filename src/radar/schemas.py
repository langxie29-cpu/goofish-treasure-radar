"""Stable crawler-independent domain contracts. No external dependencies."""
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PriceType(str, Enum):
    REAL_PRICE = 'REAL_PRICE'
    NEGOTIABLE_REAL_PRICE = 'NEGOTIABLE_REAL_PRICE'
    PLACEHOLDER_PRICE = 'PLACEHOLDER_PRICE'
    DEPOSIT_PRICE = 'DEPOSIT_PRICE'
    PARTIAL_PRICE = 'PARTIAL_PRICE'
    RENTAL_PRICE = 'RENTAL_PRICE'
    WANTED_PRICE = 'WANTED_PRICE'
    UNCERTAIN = 'UNCERTAIN'


@dataclass(frozen=True)
class Item:
    item_id: str
    title: str
    listed_price: float | None
    description: str = ''
    url: str = ''
    image_urls: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return self.title + '\n' + self.description


@dataclass(frozen=True)
class MoneyMention:
    amount: float
    text: str
    start: int
    end: int
    role: str = 'sale'


@dataclass(frozen=True)
class PriceIntegrityResult:
    price_type: PriceType
    listed_price: float | None
    effective_price_min: float | None
    effective_price_max: float | None
    price_confidence: int
    risk_flags: list[str]
    reason: str
    mentioned_prices: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class DetectedModel:
    model: str
    confidence: int
    source: str = 'regex_heuristic'


@dataclass(frozen=True)
class InterestResult:
    rule_interest_score: int
    interest_flags: list[str]
    reason: str


@dataclass(frozen=True)
class EvaluationResult:
    item_id: str
    title: str
    listed_price: float | None
    price_type: PriceType
    price_confidence: int
    effective_price_min: float | None
    effective_price_max: float | None
    rule_interest_score: int
    detected_models: list[DetectedModel]
    risk_flags: list[str]
    interest_flags: list[str]
    evaluation_reason: str
    evaluated_at: str
    mentioned_prices: list[float]
    input_hash: str
    engine_version: str
    worth_opening: bool
    duplicate: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result['price_type'] = self.price_type.value
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> 'EvaluationResult':
        payload = dict(value)
        payload['price_type'] = PriceType(payload['price_type'])
        payload['detected_models'] = [DetectedModel(**m) for m in payload['detected_models']]
        return cls(**payload)
