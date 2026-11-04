"""Deterministic election registry & phase calculations. No speculative new elections.
Official certification must be explicitly confirmed, never guessed from due date.
"""
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime,date,time
import json,argparse
HERE=Path(__file__).resolve().parent
TZ=ZoneInfo("America/Los_Angeles")
def registry():
 data=json.loads((HERE/"elections.json").read_text("utf8"))
 ids=[r["id"] for r in data["elections"]]
 assert len(ids)==len(set(ids))
 for x in data["elections"]:
  assert x["authority_url"].startswith("https://")
  assert x["local_url"].startswith("https://")
  assert x["personal_lookup_url"].startswith("https://")
  assert x["scope"]=="countywide_inventory_not_personal_ballot"
  assert date.fromisoformat(x["ballots_start"])<=date.fromisoformat(x["election_date"])
 return data["elections"]
def status(entry,as_of):
 if as_of.tzinfo is None:raise ValueError("Pass timezone-aware datetime")
 local=as_of.astimezone(TZ)
 start=datetime.combine(date.fromisoformat(entry["ballots_start"]),time.min,TZ)
 cutoff=datetime.combine(date.fromisoformat(entry["election_date"]),time.fromisoformat(entry["poll_close_local"]),TZ)
 if local<start:return "UPCOMING"
 if local<=cutoff:return "VOTING_PERIOD"
 if entry.get("verified_certified_at"):
  if local>=datetime.fromisoformat(entry["verified_certified_at"]).astimezone(TZ):
   return "CERTIFIED_ARCHIVE"
 due=entry.get("certification_due")
 if due and local.date()>date.fromisoformat(due):
  return "PAST_CERTIFICATION_DEADLINE_NOT_VERIFIED"
 return "POLLS_CLOSED_CERTIFICATION_NOT_VERIFIED"
def snapshot(as_of=None):
 now=as_of or datetime.now(TZ)
 return {"as_of":now.isoformat(),"elections":[{"id":e["id"],"county":e["county"],"state":e["state"],
  "election_date":e["election_date"],"phase":status(e,now),
  "authority_url":e["authority_url"],"personal_lookup_url":e["personal_lookup_url"],
  "certification_verified":bool(e.get("verified_certified_at"))} for e in registry()]}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--asof",help="ISO datetime with timezone, e.g. 2026-11-03T21:30:00-08:00")
 args=p.parse_args()
 asof=datetime.fromisoformat(args.asof) if args.asof else datetime.now(TZ)
 print(json.dumps(snapshot(asof),ensure_ascii=False,indent=2))
