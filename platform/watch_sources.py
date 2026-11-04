"""Read-only official-source monitor; never auto-publishes changed PDF/HTML.
Usage: python platform/watch_sources.py --edition multnomah --check
Without --check, prints registered sources and expected hashes only.
"""
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit
import json,hashlib,argparse,datetime,requests
HERE=Path(__file__).resolve().parent
ALLOW={'multco.us','sos.oregon.gov','clark.wa.gov','www.sos.wa.gov'}
def official_roots(edition):
 d=json.loads((HERE/"output"/(edition+"_2026_canonical.json")).read_text("utf8"))
 roots=[]
 for x in d["sources"]:
  if x["category"] not in ("official_ballot","official_pamphlet"):continue
  url=x["url"].split('#',1)[0]
  if urlsplit(url).hostname not in ALLOW:continue
  previous=next((v for v in roots if v["url"]==url),None)
  if previous:
   if not previous["expected_sha256"] and x.get("sha256"):previous["expected_sha256"]=x["sha256"]
  else:roots.append({"url":url,"category":x["category"],"expected_sha256":x.get("sha256")})
 return roots
def audit(edition,download=False):
 roots=official_roots(edition)
 if not download:return {"edition":edition,"sources":len(roots),"registered":roots,"status":"NOT_CHECKED"}
 results=[]
 for source in roots:
  item={"url":source["url"],"expected_sha256":source["expected_sha256"]}
  try:
   response=requests.get(source["url"],timeout=(8,24),stream=True,
     headers={"User-Agent":"TLDRVote/1.0 source-monitor; evidence-review only"})
   item["http_status"]=response.status_code
   if response.status_code!=200:
    item["status"]="HTTP_REVIEW_REQUIRED";response.close();results.append(item);continue
   h=hashlib.sha256();total=0;limit=20*1024*1024
   for chunk in response.iter_content(65536):
    total+=len(chunk)
    if total>limit:
     item["status"]="OVERSIZE_REVIEW_REQUIRED";break
    h.update(chunk)
   else:
    item["retrieved_bytes"]=total;item["observed_sha256"]=h.hexdigest()
    item["status"]="UNCHANGED" if item["expected_sha256"] and h.hexdigest()==item["expected_sha256"] else "CHANGE_OR_UNPINNED_REVIEW_REQUIRED"
   response.close()
  except requests.RequestException as e:
   item["status"]="NETWORK_REVIEW_REQUIRED";item["error"]=type(e).__name__
  results.append(item)
 return {"edition":edition,"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "status":"CHANGE_REVIEW_REQUIRED" if any(x["status"]!="UNCHANGED" for x in results) else "UNCHANGED",
  "results":results,"note":"A content hash change requires re-ingestion and editorial review; does not authorize publication or imply the page is false."}
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--edition",choices=["clark","multnomah"],required=True)
 parser.add_argument("--check",action="store_true")
 args=parser.parse_args();report=audit(args.edition,args.check)
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if args.check:
  (HERE/"output"/(args.edition+"_source_watch.json")).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
