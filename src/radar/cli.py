"""Offline JSONL evaluation and safe database backfill. No network calls."""
import argparse
import json
import sqlite3
import sys
from .pipeline import Radar
from .storage import EvaluationStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', help='JSONL path, or - for stdin')
    parser.add_argument('--db', default='data/app.sqlite3')
    parser.add_argument('--backfill', action='store_true', help='Evaluate upstream result_items.raw_json')
    args = parser.parse_args()
    if bool(args.input) == args.backfill:
        parser.error('choose exactly one of --input or --backfill')
    radar = Radar(EvaluationStore(args.db))
    if args.backfill:
        with sqlite3.connect(args.db) as conn:
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='result_items'").fetchone()
            if not exists:
                parser.error('result_items does not exist; crawl or use --input first')
            records = (json.loads(row[0]) for row in conn.execute('SELECT raw_json FROM result_items ORDER BY id'))
            for item in records:
                print(json.dumps(radar.evaluate_sync(item).to_dict(), ensure_ascii=False))
        return
    stream = sys.stdin if args.input == '-' else open(args.input, encoding='utf-8-sig')
    errors = 0
    try:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                print(json.dumps(radar.evaluate_sync(item).to_dict(), ensure_ascii=False, allow_nan=False))
            except (ValueError, TypeError) as exc:
                errors += 1
                print(f'line {line_number}: {exc}', file=sys.stderr)
    finally:
        if stream is not sys.stdin:
            stream.close()
    if errors:
        raise SystemExit(1)
