"""TLDR Vote v1 static-source + editorial release gate.
Structural errors block even preview. Unreviewed political claims block authoritative release.
"""
from pathlib import Path
from collections import Counter
import json,jsonschema,sys,hashlib,argparse,datetime
ROOT=Path(__file__).resolve().parent
def load(name):return json.loads((ROOT/"output"/(name+"_2026_canonical.json")).read_text("utf8"))
def qa(edition):
 problems=[];blockers=list(edition["release_gate"]["blockers"]);metrics=Counter()
 try:jsonschema.validate(edition,json.loads((ROOT/"schema.json").read_text("utf8")),format_checker=jsonschema.FormatChecker())
 except jsonschema.ValidationError as e:problems.append("SCHEMA: "+str(e.message))
 source_ids=[s["id"] for s in edition.get("sources",[])]
 known=set(source_ids)
 if len(known)!=len(source_ids):problems.append("Duplicate source IDs")
 urls={s["url"] for s in edition.get("sources",[])}
 if len(urls)!=len(source_ids):problems.append("Duplicate source URLs")
 for s in edition.get("sources",[]):
  if not s["url"].startswith("https://"):problems.append("Non-HTTPS source "+s["id"])
 allids=set()
 def claim_audit(c,path):
  metrics["claims"]+=1
  if c["status"]=="UNKNOWN":metrics["unknown_claims"]+=1
  if c["status"]=="EDITOR_APPROVED":
   if not c.get("reviewer") or not c.get("reviewed_at") or not c.get("source_excerpt") or not c["source_ids"]:
    problems.append("Unsupported editorial signoff: "+path)
  elif c["status"] in ("ATTRIBUTED","RECORDED","REPORTED","DRAFT_INTERPRETATION"):
   metrics["unreviewed_claims"]+=1
  for sid in c.get("source_ids",[]):
   if sid not in known:problems.append("Unresolved source reference "+path+" -> "+sid)
 for item in edition.get("contests",[]):
  key=item["id"];metrics[item["kind"]]+=1
  if key in allids:problems.append("Duplicate topic ID: "+key)
  allids.add(key)
  if not item.get("source_ids"):problems.append("Topic without official source: "+key)
  for sid in item["source_ids"]:
   if sid not in known:problems.append("Missing topic source: "+key+" "+sid)
  if item["kind"]=="race":
   if not item.get("candidates"):problems.append("Race without any candidates: "+key)
   cand_ids={c["id"] for c in item["candidates"]}
   names=[c["name"] for c in item["candidates"]]
   if len(cand_ids)!=len(item["candidates"]) or len(set(names))!=len(names):problems.append("Duplicate candidate: "+key)
   metrics["candidates"]+=len(item["candidates"])
   claim_audit(item["office_role"],key+"/office_role")
   claim_audit(item["where_they_differ"],key+"/where_they_differ")
   if not item.get("issue_matrix"):problems.append("Missing issue matrix: "+key)
   for c in item["candidates"]:
    if c["profile_status"]=="NOT_LOCATED":metrics["unmatched_profiles"]+=1
    claim_audit(c["priority"],key+"/"+c["name"]+"/priority")
   for row in item.get("issue_matrix",[]):
    metrics["issue_rows"]+=1
    have=[p["candidate_id"] for p in row["positions"]]
    if set(have)!=cand_ids or len(have)!=len(cand_ids):problems.append("Issue question not applied to everyone: "+key+"/"+row["issue"])
    for p in row["positions"]:
     metrics["position_cells"]+=1
     claim_audit(p["claim"],key+"/"+row["issue"]+"/"+p["candidate_id"])
     if p["state"]=="NOT_FOUND":
      if p["claim"]["status"]!="UNKNOWN":problems.append("Inferred position for missing evidence: "+key)
     if p["state"]=="MENTION_ONLY":
      if p["claim"]["status"]=="EDITOR_APPROVED":problems.append("Keyword treated as approved policy stance: "+key)
  else:
   assert item["kind"]=="measure"
   for label,c in item["measure_sections"].items():
    if not c["text"]:problems.append("Blank measure explanation: "+key+"/"+label)
    claim_audit(c,key+"/"+label)
 if len(edition["contests"])!=edition["coverage"]["topics"]:problems.append("Topic coverage mismatch")
 for name,k in [("races","race"),("measures","measure"),("candidates","candidates"),("unmatched_profiles","unmatched_profiles")]:
  if metrics[k]!=edition["coverage"][name]:problems.append("Coverage count mismatch: "+name)
 if edition["election"]["state"]!=edition["jurisdiction"]["state"]:problems.append("Election/state mismatch")
 if edition["coverage"]["structural_issues"]:blockers+=edition["coverage"]["structural_issues"]
 if edition["coverage"]["unmatched_profiles"]:blockers.append("Candidate profiles not located: "+str(edition["coverage"]["unmatched_profiles"]))
 if metrics["unreviewed_claims"] or metrics["unknown_claims"]:
  blockers.append(str(metrics["unreviewed_claims"])+" draft/attributed and "+str(metrics["unknown_claims"])+" unknown fields require claim-level review")
 if edition["editorial_status"]!="REVIEWED":blockers.append("Human editorial approval not complete")
 blockers=list(dict.fromkeys(blockers))
 # The bundle is not permitted to claim official or comprehensive status while any blocker remains.
 if edition["release_gate"]["ready"] and (problems or blockers):problems.append("FAIL-CLOSED: release_ready conflicts with quality/review defects")
 return {"edition":edition["jurisdiction"]["label"],"schema_version":edition["schema_version"],
  "structural_status":"PASS" if not problems else "FAIL","editorial_status":edition["editorial_status"],
  "authoritative_release":"BLOCKED" if problems or blockers else "READY",
  "problems":problems,"blockers":blockers,"metrics":dict(metrics)}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--authoritative",action="store_true",help="Fail if human-reviewed release gate is blocked")
 ap.add_argument("--edition",choices=["clark","multnomah","both"],default="both")
 args=ap.parse_args()
 outputs={}
 for name in ["clark","multnomah"] if args.edition=="both" else [args.edition]:
  report=qa(load(name));outputs[name]=report
  print(json.dumps({name:report},ensure_ascii=False,indent=2))
 (ROOT/"output"/"quality_report.json").write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding="utf8")
 if any(x["structural_status"]=="FAIL" for x in outputs.values()):raise SystemExit(1)
 if args.authoritative and any(x["authoritative_release"]!="READY" for x in outputs.values()):raise SystemExit(2)
if __name__=="__main__":main()
