import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.routes import radar
from src.radar import EvaluationStore, Radar

def test_missing_database_is_empty_and_read_only(tmp_path, monkeypatch):
    path = tmp_path / 'not-created.sqlite3'
    monkeypatch.setenv('APP_DATABASE_FILE', str(path))
    app=FastAPI(); app.include_router(radar.router)
    client=TestClient(app)
    assert client.get('/api/radar/candidates').json()=={'total':0,'items':[]}
    assert client.get('/api/radar/summary').json()=={'items_today':0,'candidates':0}
    assert not path.exists()

def test_candidate_pagination_and_raw_images(tmp_path, monkeypatch):
    path=tmp_path/'radar.sqlite3'
    monkeypatch.setenv('APP_DATABASE_FILE',str(path))
    engine=Radar(EvaluationStore(str(path)))
    engine.evaluate_sync({'item_id':'123','title':'SHARP LJ64HB34 工业 TFEL 拆机库存屏','listed_price':180})
    engine.evaluate_sync({'item_id':'456','title':'普通塑料袋','listed_price':5})
    app=FastAPI(); app.include_router(radar.router); client=TestClient(app)
    result=client.get('/api/radar/candidates').json()
    assert result['total']==1
    assert result['items'][0]['item_id']=='123'
    assert result['items'][0]['url']=='https://www.goofish.com/item?id=123'
    assert client.get('/api/radar/candidates?candidates_only=false&limit=1').json()['total']==2
    assert client.get('/api/radar/candidates?page=2').json()['items']==[]
    assert client.get('/api/radar/candidates?limit=101').status_code==422
    assert client.get('/api/radar/summary').json()=={'items_today':2,'candidates':1}
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE result_items(id INTEGER PRIMARY KEY,item_id TEXT,raw_json TEXT)')
        conn.execute('INSERT INTO result_items VALUES(1,?,?)',('123','{"item_id":"123","title":"test","image_urls":["https://example.com/a.jpg"],"url":"https://www.goofish.com/item?id=123"}'))
    assert client.get('/api/radar/candidates').json()['items'][0]['image_urls']==['https://example.com/a.jpg']
