"""Additive, namespaced SQLite schema; never changes upstream tables."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .schemas import EvaluationResult

SCHEMA = '''
CREATE TABLE IF NOT EXISTS radar_schema_versions(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO radar_schema_versions VALUES(1);
CREATE TABLE IF NOT EXISTS radar_evaluations(
 item_id TEXT PRIMARY KEY, title TEXT NOT NULL, listed_price REAL,
 price_type TEXT NOT NULL, price_confidence INTEGER NOT NULL CHECK(price_confidence BETWEEN 0 AND 100),
 effective_price_min REAL, effective_price_max REAL,
 rule_interest_score INTEGER NOT NULL CHECK(rule_interest_score BETWEEN 0 AND 100),
 detected_models TEXT NOT NULL, risk_flags TEXT NOT NULL, interest_flags TEXT NOT NULL,
 evaluation_reason TEXT NOT NULL, evaluated_at TEXT NOT NULL,
 input_hash TEXT NOT NULL, engine_version TEXT NOT NULL, worth_opening INTEGER NOT NULL,
 evaluation_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS radar_interest_idx ON radar_evaluations(rule_interest_score DESC);
CREATE TABLE IF NOT EXISTS radar_observations(
 item_id TEXT NOT NULL, input_hash TEXT NOT NULL, engine_version TEXT NOT NULL,
 observed_at TEXT NOT NULL, evaluation_json TEXT NOT NULL,
 PRIMARY KEY(item_id,input_hash,engine_version)
);
CREATE TABLE IF NOT EXISTS model_price_history(
 model TEXT NOT NULL, item_id TEXT NOT NULL, price REAL NOT NULL,
 condition TEXT, observed_at TEXT NOT NULL, input_hash TEXT NOT NULL,
 PRIMARY KEY(model,item_id,input_hash)
);
'''


class EvaluationStore:
    def __init__(self, path: str):
        if path == ':memory:':
            raise ValueError('Use a temporary file for durable per-operation connections')
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def cached(self, item_id: str, input_hash: str, engine_version: str):
        with self.connection() as conn:
            row = conn.execute('SELECT evaluation_json FROM radar_evaluations WHERE item_id=? AND input_hash=? AND engine_version=?',
                               (item_id, input_hash, engine_version)).fetchone()
        return EvaluationResult.from_dict(json.loads(row[0])) if row else None

    def save(self, result: EvaluationResult) -> bool:
        payload = result.to_dict()
        payload['duplicate'] = False
        serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        keys = ['item_id', 'title', 'listed_price', 'price_type', 'price_confidence',
                'effective_price_min', 'effective_price_max', 'rule_interest_score',
                'detected_models', 'risk_flags', 'interest_flags', 'evaluation_reason',
                'evaluated_at', 'input_hash', 'engine_version', 'worth_opening']
        values = [json.dumps(payload[k], ensure_ascii=False) if isinstance(payload[k], list) else payload[k] for k in keys]
        with self.connection() as conn:
            inserted = conn.execute('INSERT OR IGNORE INTO radar_observations VALUES (?,?,?,?,?)',
                                    (result.item_id, result.input_hash, result.engine_version, result.evaluated_at, serialized)).rowcount
            if not inserted:
                return False
            columns = ','.join(keys + ['evaluation_json'])
            placeholders = ','.join('?' for _ in range(len(keys)+1))
            update = ','.join(f'{k}=excluded.{k}' for k in keys if k != 'item_id') + ',evaluation_json=excluded.evaluation_json'
            conn.execute(f'INSERT INTO radar_evaluations ({columns}) VALUES ({placeholders}) ON CONFLICT(item_id) DO UPDATE SET {update}', values+[serialized])
            # Only credible full-item prices enter history. Asking prices, never confirmed sale prices.
            if result.price_confidence >= 70 and result.price_type.value in {'REAL_PRICE', 'NEGOTIABLE_REAL_PRICE'}:
                for model in result.detected_models:
                    conn.execute('INSERT OR IGNORE INTO model_price_history VALUES (?,?,?,?,?,?)',
                                 (model.model, result.item_id, result.listed_price, None, result.evaluated_at, result.input_hash))
        return True
