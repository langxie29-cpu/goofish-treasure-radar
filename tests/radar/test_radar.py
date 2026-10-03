import asyncio
import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.radar import EvaluationStore, Item, Radar
from src.radar.model_extractor import extract_models
from src.radar.money_extractor import extract_money
from src.radar.price_integrity import analyze_price
from src.radar.interest_rules import score_interest
from src.radar.rule_filter import normalize_item, parse_listed_price


@pytest.mark.parametrize('price,text,kind', [
    (180, '老式客显，正常使用，可小刀', 'NEGOTIABLE_REAL_PRICE'),
    (180, '正常使用，180元', 'REAL_PRICE'),
    (1, '价格随便挂，具体私聊', 'PLACEHOLDER_PRICE'),
    (100, '100定金，总价1800', 'DEPOSIT_PRICE'),
    (50, '50是电源板价格，整机另议', 'PARTIAL_PRICE'),
    (80, '80元/天', 'RENTAL_PRICE'),
    (999, '高价回收示波器', 'WANTED_PRICE'),
    (50, '2200出，诚心要最低2000', 'PLACEHOLDER_PRICE'),
    (1, '1元出，正常使用', 'REAL_PRICE'),
    (1, '不知道是什么', 'UNCERTAIN'),
    (100, '只出售尾款资格', 'PARTIAL_PRICE'),
    (100, '最低配置100元，整机总价1800', 'PARTIAL_PRICE'),
    (200, '原价2200元，现在200元出', 'REAL_PRICE'),
    (180, '运费20元，可小刀', 'NEGOTIABLE_REAL_PRICE'),
    (180, '无需定金，180元出', 'REAL_PRICE'),
    (180, '无定金，180元出', 'REAL_PRICE'),
    (0, '0元免费送，自提', 'REAL_PRICE'),
])
def test_price_types(price, text, kind):
    result = analyze_price(Item('1', '电子设备', price, text))
    assert result.price_type.value == kind
    assert 0 <= result.price_confidence <= 100
    if kind == 'NEGOTIABLE_REAL_PRICE':
        assert result.price_confidence >= 70


def test_effective_price_and_confidence():
    mismatch = analyze_price(Item('1', 'CRT', 50, '2200出，诚心要最低2000'))
    assert mismatch.mentioned_prices == [2200, 2000]
    assert (mismatch.effective_price_min, mismatch.effective_price_max) == (2000, 2200)
    assert 'PRICE_MISMATCH' in mismatch.risk_flags
    assert mismatch.price_confidence < 30
    deposit = analyze_price(Item('2', 'CRT', 100, '100定金，总价1800'))
    assert deposit.effective_price_min == deposit.effective_price_max == 1800
    assert analyze_price(Item('3', 'CRT', 80, '80元/天')).effective_price_min is None


@pytest.mark.parametrize('text,expected', [
    ('¥2200', [2200]), ('￥2200', [2200]), ('2200元', [2200]),
    ('2200块', [2200]), ('2200出', [2200]), ('最低2000', [2000]),
    ('2000包邮', [2000]), ('到手1800', [1800]), ('售价：1800', [1800]),
    ('￥2,200.50', [2200.5]), ('１８０元', [180]),
    ('220V 50Hz 100MHz 2020年 12V 640x480', []),
    ('最低220V，到手100MHz', []),
    ('LJ64HB34 TDS1002 PVM-9040', []),
    ('型号PR-888，电压220V，180元出', [180]),
    ('180元，最低160，邮费20元', [180, 160, 20]),
    ('库存2200台，2020年产，尺寸640x480', []),
    ('1000元/天', [1000]),
    ('原价2200元，180元出', [2200, 180]),
])
def test_money(text, expected):
    assert [m.amount for m in extract_money(text)] == expected


@pytest.mark.parametrize('text,expected', [
    ('SHARP LJ64HB34', ['LJ64HB34']),
    ('Tektronix TDS1002', ['TDS1002']),
    ('Sony PVM-9040', ['PVM-9040']),
    ('珠江 PR-888', ['PR-888']),
    ('DMG-01 FG-100 HP-54600B', ['DMG-01', 'FG-100', 'HP-54600B']),
    ('tds1002 TDS1002', ['TDS1002']),
    ('220V 50Hz 100MHz 2020年 12V 640x480 USB2 HDMI2 IP65 DDR4', []),
])
def test_models(text, expected):
    assert [m.model for m in extract_models(text)] == expected


@pytest.mark.parametrize('text', ['CRT 监视器', 'VFD 客显', 'TFEL 电致发光', '等离子显示屏', '示波器 库存', '工业显示器 拆机'])
def test_interest(text):
    assert score_interest(text).rule_interest_score >= 45


def test_seller_words_alone_not_treasure():
    assert score_interest('清仓 库存 仓库翻出 不懂 按废品处理').rule_interest_score < 20
    assert score_interest('CRT CRT CRT').rule_interest_score == score_interest('CRT').rule_interest_score


@pytest.mark.parametrize('value,expected', [(180,180), ('¥180',180), ('￥1,800.50',1800.5),
    ('180元',180), (None,None), ('180起',None), ('NaN',None), ('inf',None), (-10,None), (True,None), ('220V',None)])
def test_listed_parser(value, expected):
    assert parse_listed_price(value) == expected


def test_upstream_adapter():
    item = normalize_item({'商品信息': {'商品ID':'123','商品标题':'CRT','当前售价':'¥180','商品描述':'正常使用'}})
    assert item.listed_price == 180
    assert item.description == '正常使用'
    with pytest.raises(ValueError):
        normalize_item({'title':'missing id'})


def test_sqlite_dedup_changes_history_and_additive_schema(tmp_path):
    path = str(tmp_path/'db.sqlite3')
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE existing_data(id INTEGER PRIMARY KEY, value TEXT)')
        conn.execute("INSERT INTO existing_data VALUES(1,'keep')")
    radar = Radar(EvaluationStore(path))
    item = {'item_id':'1','title':'CRT Sony PVM-9040','listed_price':180,'description':'180元出'}
    first = asyncio.run(radar.evaluate(item))
    second = asyncio.run(radar.evaluate(item))
    assert first.worth_opening and not first.duplicate and second.duplicate
    item['listed_price'] = 160
    item['description'] = '160元出'
    third = asyncio.run(radar.evaluate(item))
    assert not third.duplicate
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM radar_evaluations').fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM radar_observations').fetchone()[0] == 2
        assert conn.execute('SELECT COUNT(*) FROM model_price_history').fetchone()[0] == 2
        assert conn.execute('SELECT value FROM existing_data').fetchone()[0] == 'keep'
        assert conn.execute('SELECT listed_price FROM radar_evaluations').fetchone()[0] == 160


def test_concurrent_claim_only_one_new_evaluation(tmp_path):
    store = EvaluationStore(str(tmp_path/'db.sqlite3'))
    radar = Radar(store)
    item = {'item_id':'1','title':'VFD','listed_price':180}
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _:radar.evaluate_sync(item), range(8)))
    assert sum(not x.duplicate for x in results) == 1


def test_suspicious_price_preserves_interesting_item_without_history(tmp_path):
    path = str(tmp_path/'db.sqlite3')
    result = Radar(EvaluationStore(path)).evaluate_sync({'item_id':'1','title':'SHARP LJ64HB34 TFEL','listed_price':1,'description':'价格随便挂'})
    assert result.worth_opening
    assert result.price_confidence < 30
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM model_price_history').fetchone()[0] == 0


def test_threshold_change_invalidates_cached_decision(tmp_path):
    store = EvaluationStore(str(tmp_path/'db.sqlite3'))
    item = {'item_id':'1','title':'CRT','listed_price':180}
    assert Radar(store, interest_threshold=50).evaluate_sync(item).worth_opening
    result = Radar(store, interest_threshold=90).evaluate_sync(item)
    assert not result.duplicate and not result.worth_opening


def test_cli_demo_and_backfill(tmp_path):
    db = str(tmp_path/'db.sqlite3')
    result = subprocess.run([sys.executable,'-m','src.radar','--input','examples/items.jsonl','--db',db],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert len([json.loads(line) for line in result.stdout.splitlines()]) == 5
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE result_items(id INTEGER PRIMARY KEY,raw_json TEXT)')
        conn.execute('INSERT INTO result_items VALUES(1,?)', (json.dumps({'item_id':'existing','title':'CRT','listed_price':180}),))
    result = subprocess.run([sys.executable,'-m','src.radar','--backfill','--db',db],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['item_id'] == 'existing'


def test_reverted_listing_updates_latest_row(tmp_path):
    path = str(tmp_path/'db.sqlite3')
    radar = Radar(EvaluationStore(path))
    a = {'item_id':'1','title':'CRT','listed_price':180}
    b = {**a,'listed_price':160}
    radar.evaluate_sync(a)
    radar.evaluate_sync(b)
    radar.evaluate_sync(a)
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT listed_price FROM radar_evaluations').fetchone()[0] == 180


def test_dispatcher_radar_never_calls_ai_images_or_seller(monkeypatch, tmp_path):
    from src.services.item_analysis_dispatcher import ItemAnalysisDispatcher, ItemAnalysisJob
    monkeypatch.setenv('RADAR_ENABLED', 'true')
    monkeypatch.setenv('APP_DATABASE_FILE', str(tmp_path/'db.sqlite3'))
    records, notices = [], []
    async def forbidden(*args):
        raise AssertionError('MVP must not call AI, image downloader or extra seller requests')
    async def saver(record, keyword):
        records.append(record)
        return True
    async def notifier(item, reason):
        notices.append((item, reason))
    async def run():
        dispatcher = ItemAnalysisDispatcher(concurrency=2, skip_ai_analysis=False,
            seller_loader=forbidden,image_downloader=forbidden,ai_analyzer=forbidden,
            saver=saver,notifier=notifier)
        job = ItemAnalysisJob('CRT','CRT','ai',True,'ignored',(),
                              {'商品信息':{'商品ID':'1','商品标题':'CRT Sony PVM-9040','当前售价':'180','商品描述':'180元出'}},
                              'seller','优秀','1年')
        dispatcher.submit(job)
        await dispatcher.join()
        dispatcher.submit(job)
        await dispatcher.join()
    asyncio.run(run())
    assert len(records) == 2 and len(notices) == 1
    assert records[0]['ai_analysis']['analysis_source'] == 'radar'
    assert records[0]['radar_evaluation']['price_confidence'] >= 70


def test_deposit_amount_extracted():
    assert [m.amount for m in extract_money('100定金，总价1800')] == [100,1800]


def test_crawler_contains_no_automation_masking():
    source = Path('src/scraper.py').read_text()
    assert 'AutomationControlled' not in source
    assert "Object.defineProperty(navigator, 'webdriver'" not in source
    assert '--disable-web-security' not in source
