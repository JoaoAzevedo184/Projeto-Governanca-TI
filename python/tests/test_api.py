from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health():assert c.get('/health').json()['status']=='UP'
def test_slo():assert c.post('/api/v1/slos',json={'service':'ERP','sli':'availability','target':.999,'windowMinutes':43200,'observed':.998}).status_code==201
