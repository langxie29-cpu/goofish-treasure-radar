"""Normalize upstream Chinese records or generic English records."""
import math
import re
import unicodedata
from collections.abc import Mapping
from .schemas import Item


def parse_listed_price(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    raw = unicodedata.normalize('NFKC', str(value)).strip()
    raw = re.sub(r'^[¥￥]\s*', '', raw)
    raw = re.sub(r'\s*(?:元|块)$', '', raw).replace(',', '')
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', raw):
        return None
    amount = float(raw)
    return amount if math.isfinite(amount) else None


def normalize_item(record: Item | Mapping) -> Item:
    if isinstance(record, Item):
        if not record.item_id.strip() or not record.title.strip():
            raise ValueError('item_id and title are required')
        return Item(record.item_id.strip(), record.title.strip(),
                    parse_listed_price(record.listed_price), record.description,
                    record.url, record.image_urls)
    if not isinstance(record, Mapping):
        raise ValueError('item must be a mapping or Item')
    data = record.get('商品信息', record)
    if not isinstance(data, Mapping):
        raise ValueError('商品信息 must be a mapping')
    def get(en, zh, default=''):
        return data.get(en, data.get(zh, default))
    item_id = str(get('item_id', '商品ID') or '').strip()
    title = str(get('title', '商品标题') or '').strip()
    if not item_id or not title:
        raise ValueError('item_id and title are required; missing IDs are never merged')
    price = get('listed_price', '当前售价', data.get('price'))
    images = get('image_urls', '商品图片列表', ()) or ()
    if isinstance(images, str):
        images = (images,)
    return Item(item_id, title, parse_listed_price(price),
                str(get('description', '商品描述') or ''),
                str(get('url', '商品链接') or ''), tuple(map(str, images)))
