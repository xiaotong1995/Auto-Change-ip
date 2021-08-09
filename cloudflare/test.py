import requests

domain = "tcqy88.com"
token = "248946,9478c514420b7afb461280e212e9a91f"
api="https://dnsapi.cn/Record.List"
data = {
    "login_token": token,
    "domain": domain,
    "format": "json"
}
req=requests.post(api,data=data,timeout=5)
out_json=req.json()
code=out_json["status"]["code"]
ip=""
if code=="1":
    records=out_json["records"]
    for record in records:
        if record["type"]=="A":
            print(record)