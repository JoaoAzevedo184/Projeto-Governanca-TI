import pathlib
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
ALERTAS=pathlib.Path(__file__).resolve().parents[2]/'datasets'/'alertas.csv'
def test_health():assert c.get('/health').json()['status']=='UP'
def test_slo():assert c.post('/api/v1/slos',json={'service':'ERP','sli':'availability','target':.999,'windowMinutes':43200,'observed':.998}).status_code==201
def test_import_e_kpis():
 # Baseline conferido contra datasets/dashboard_referencia.csv.
 with ALERTAS.open('rb') as f:r=c.post('/api/v1/imports/events',files={'file':('alertas.csv',f,'text/csv')})
 assert r.status_code==202 and r.json()['totalRows']==500
 k=c.get('/api/v1/kpis').json()
 assert k['mttdMinutes']==50.46
 assert k['mttrMinutes']==236.44
 assert k['actionableRate']==.25
 assert k['duplicateRate']==.368
 assert k['runbookRate']==.244
 assert k['incidentRate']==.142
def test_kpis_filtra_por_severidade():
 with ALERTAS.open('rb') as f:c.post('/api/v1/imports/events',files={'file':('alertas.csv',f,'text/csv')})
 assert c.get('/api/v1/kpis',params={'severity':'Critical'}).json()['eventCount']==41
