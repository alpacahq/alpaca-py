import os, json, yaml
from app import app

schema = app.openapi()

base = os.environ.get("PUBLIC_BASE_URL") or os.environ.get("RAILWAY_STATIC_URL") or "http://localhost:8000"
schema["servers"] = [{"url": base}]

p = schema.get("paths", {})
if "/v1/order/bracket"  in p and "post" in p["/v1/order/bracket"]:
    p["/v1/order/bracket"]["post"]["operationId"]  = "placeBracketOrder"
if "/v1/order/stop"     in p and "post" in p["/v1/order/stop"]:
    p["/v1/order/stop"]["post"]["operationId"]     = "placeStopOrder"
if "/v1/order/trailing" in p and "post" in p["/v1/order/trailing"]:
    p["/v1/order/trailing"]["post"]["operationId"] = "placeTrailingStopOrder"

with open("openapi.json","w",encoding="utf-8") as f:
    json.dump(schema, f, indent=2)
with open("openapi.yaml","w",encoding="utf-8") as f:
    yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True)

print("Wrote openapi.json & openapi.yaml with servers[0].url =", base)
