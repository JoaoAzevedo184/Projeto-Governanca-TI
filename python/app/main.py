import csv,io,os,time
from fastapi import FastAPI,UploadFile,File
from fastapi.responses import Response
from prometheus_client import Counter,generate_latest,CONTENT_TYPE_LATEST
from pydantic import BaseModel,Field
app=FastAPI(title="MVP Observabilidade Hibrida",version="1.0.0")
events=[];slos=[];risks=[]
REQ=Counter("observability_http_requests_total","Requisicoes",["method","path","status"])
@app.middleware("http")
async def met(req,call_next):
 r=await call_next(req);REQ.labels(req.method,req.url.path,r.status_code).inc();return r
@app.get("/health")
def health():return {"status":"UP","environment":os.getenv("APP_ENV","local")}
@app.get("/metrics",include_in_schema=False)
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
def rows_from_csv(raw:bytes):
 # As fixtures trazem BOM, um preambulo decorativo (titulo/descricao) antes do
 # cabecalho e uma coluna vazia a esquerda. O cabecalho e a primeira linha com
 # pelo menos 3 celulas preenchidas; colunas sem nome sao descartadas.
 rs=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
 h=next((i for i,r in enumerate(rs) if sum(1 for c in r if c.strip())>=3),None)
 if h is None:return []
 cols=[(i,c.strip()) for i,c in enumerate(rs[h]) if c.strip()]
 return [{k:(r[i].strip() if i<len(r) else "") for i,k in cols} for r in rs[h+1:] if any(c.strip() for c in r)]
@app.post("/api/v1/imports/events",status_code=202)
async def upload(file:UploadFile=File(...)):
 global events;events=rows_from_csv(await file.read());return {"totalRows":len(events),"status":"COMPLETED"}
def yes(v):return str(v).strip().lower() in {"1","true","sim","yes"}
def num(x,k):
 try:return float(x.get(k) or 0)
 except:return 0
@app.get("/api/v1/kpis")
def kpis(service:str|None=None,severity:str|None=None):
 xs=[x for x in events if (not service or x.get("Servico")==service) and (not severity or x.get("Severidade")==severity)];n=len(xs)
 return {"eventCount":n,"mttdMinutes":round(sum(num(x,"MTTD_min") for x in xs)/n,2) if n else 0,"mttrMinutes":round(sum(num(x,"MTTR_min") for x in xs)/n,2) if n else 0,"actionableRate":round(sum(yes(x.get("Acionavel")) for x in xs)/n,4) if n else 0,"duplicateRate":round(sum(yes(x.get("Duplicado")) for x in xs)/n,4) if n else 0,"runbookRate":round(sum(yes(x.get("Runbook")) for x in xs)/n,4) if n else 0,"incidentRate":round(sum(yes(x.get("Gerou_incidente")) for x in xs)/n,4) if n else 0}
class Slo(BaseModel):service:str;sli:str;target:float=Field(gt=0,le=1);windowMinutes:int=Field(gt=0);observed:float=Field(ge=0,le=1)
@app.post("/api/v1/slos",status_code=201)
def slo(x:Slo):
 d=x.model_dump();d["errorBudgetMinutes"]=round((1-x.target)*x.windowMinutes,2);d["consumedBudgetMinutes"]=round(max(0,x.target-x.observed)*x.windowMinutes,2);slos.append(d);return d
@app.get("/api/v1/slos")
def slo_list():return slos
class Cost(BaseModel):name:str;monthlyVolumeGb:float=Field(ge=0);retentionDays:int=Field(gt=0);pricePerGb:float=Field(ge=0);monthlyPlatformCost:float=Field(ge=0);monthlyPeopleCost:float=Field(ge=0)
@app.post("/api/v1/costs/compare")
def costs(items:list[Cost]):
 out=[]
 for x in items:out.append({"name":x.name,"monthlyCost":round(x.monthlyVolumeGb*x.pricePerGb+x.monthlyPlatformCost+x.monthlyPeopleCost,2),"retentionDays":x.retentionDays})
 return {"ranking":sorted(out,key=lambda z:z["monthlyCost"])}
class Tune(BaseModel):action:str;evidence:list[str]=Field(min_length=1);owner:str;expectedImpact:str
@app.post("/api/v1/tuning/recommendations",status_code=201)
def tune(x:Tune):return x.model_dump()|{"status":"PROPOSED"}
