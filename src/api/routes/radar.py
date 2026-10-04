"""Read-only presentation of existing Radar evaluations. No crawler or engine changes."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Query
from src.radar.rule_filter import normalize_item

router = APIRouter(prefix="/api/radar", tags=["radar"])

def _connection():
    path = Path(os.getenv("APP_DATABASE_FILE", "data/app.sqlite3")).resolve()
    if not path.exists():
        return None
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='radar_evaluations'").fetchone():
        conn.close()
        return None
    return conn

@router.get("/summary")
def summary():
    conn = _connection()
    if conn is None:
        return {"items_today": 0, "candidates": 0}
    try:
        today = datetime.now(timezone.utc).date().isoformat()
        row = conn.execute("SELECT sum(substr(evaluated_at,1,10)=?),sum(worth_opening) FROM radar_evaluations", (today,)).fetchone()
        return {"items_today": row[0] or 0, "candidates": row[1] or 0}
    finally:
        conn.close()

@router.get("/candidates")
def candidates(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), candidates_only: bool = True):
    conn = _connection()
    if conn is None:
        return {"total": 0, "items": []}
    try:
        where = "WHERE worth_opening=1" if candidates_only else ""
        total = conn.execute(f"SELECT count(*) FROM radar_evaluations {where}").fetchone()[0]
        rows = conn.execute(f"SELECT item_id,evaluation_json FROM radar_evaluations {where} ORDER BY evaluated_at DESC,item_id LIMIT ? OFFSET ?", (limit, (page-1)*limit)).fetchall()
        has_raw = conn.execute("SELECT 1 FROM sqlite_master WHERE name='result_items'").fetchone()
        items = []
        for row in rows:
            item = json.loads(row['evaluation_json'])
            item.update(url=f"https://www.goofish.com/item?id={row['item_id']}", image_urls=[])
            raw = conn.execute("SELECT raw_json FROM result_items WHERE item_id=? ORDER BY id DESC LIMIT 1", (row['item_id'],)).fetchone() if has_raw else None
            if raw:
                try:
                    normalized = normalize_item(json.loads(raw[0]))
                    item['url'] = normalized.url or item['url']
                    item['image_urls'] = list(normalized.image_urls)
                except (ValueError, TypeError, KeyError):
                    pass
            items.append(item)
        return {"total": total, "items": items}
    finally:
        conn.close()
