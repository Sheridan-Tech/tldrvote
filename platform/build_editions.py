"""Deterministic adapters: existing Clark/Multnomah curated source -> common TLDR Vote v1.
Does not run an LLM, invent a stance, or approve editorial assertions.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json,datetime,re
import jsonschema
ROOT=Path(__file__).resolve().parent.parent
HERE=Path(__file__).resolve().parent
DATE="2026-11-03"
def read(p):return json.loads(p.read_text(encoding="utf8"))
class SourceRegistry:
 def __init__(self):self.by_url={}
 def add(self,url,category="other",label="",page=None,sha=None):
  if not url or not url.startswith("https://"):raise ValueError("Invalid source URL: "+str(url))
  key=url
  if key in self.by_url:return self.by_url[key]["id"]
  id="src-"+sha256(key.encode()).hexdigest()[:16]
  s={"id":id,"url":url,"category":category,"label":label or "Referenced public record"}
  if page is not None:s["page"]=int(page)
  if sha is not None:s["sha256"]=sha
  self.by_url[key]=s
  return id
 def values(self):return list(sorted(self.by_url.values(),key=lambda x:x["id"]))
def claim(text="",status="UNKNOWN",ids=(),qualifier=""):
 c={"text":str(text or ""),"status":status,"source_ids":list(dict.fromkeys(ids))}
 if qualifier:c["qualifier"]=qualifier
 return c
def ed_source(reg,ref,kind="official_pamphlet"):
 if isinstance(ref,str):return reg.add(ref,kind,"Official publication")
 return reg.add(ref["url"],kind,ref.get("label","Official publication"))
def role_for(title):
 t=title.casefold()
 if "us senator" in t or "u.s. senator" in t:return "A U.S. senator represents the state in Congress, voting on federal laws and spending, confirming certain appointments, and overseeing federal agencies."
 if "us representative" in t or "u.s. representative" in t or "congress" in t:return "A U.S. House member represents a congressional district and votes on federal laws, spending and oversight."
 if "state senator" in t:return "A state senator votes on Oregon laws and state budgets and represents an Oregon legislative district."
 if "state representative" in t:return "A state representative votes on Oregon laws and state budgets and represents an Oregon legislative district."
 if "governor" in t:return "The governor leads Oregon's executive branch, proposes budgets, signs or vetoes laws, and oversees state agencies."
 if "secretary of state" in t:return "Oregon's Secretary of State oversees several statewide functions, including elections administration and public records."
 if "attorney general" in t:return "The Attorney General leads the state's legal office and represents the state in legal matters."
 if "state treasurer" in t:return "The State Treasurer manages state money, public investments and related financial programs within Oregon law."
 if "county commissioner" in t or "commissioner chair" in t:return "County commissioners set county policy and budgets, oversee county services, and make land-use decisions within their jurisdiction."
 if "county auditor" in t or ("auditor" in t and "multnomah county" in t):return "The County Auditor independently reviews county operations and spending and reports findings to the public."
 if "city auditor" in t or ("auditor" in t and "portland" in t):return "The City Auditor oversees municipal auditing and other specified city accountability functions."
 if "sheriff" in t:return "The sheriff leads county law-enforcement functions, including patrol and investigations, within the budget and legal rules."
 if "district attorney" in t:return "The district attorney oversees criminal prosecutions and certain legal proceedings in the district; a prosecutor does not decide guilt."
 if "mayor" in t:return "A mayor's duties depend on the city charter; the office helps lead city policy, administration and budget priorities."
 if "city council" in t or "councilor" in t:return "A city councilor works with other councilors on city laws, budgets, services and local land-use decisions."
 if "judge" in t or "justice" in t or "court" in t:return "A judge applies law to cases and follows court rules. Judicial candidates should not pledge outcomes in future cases."
 if "education" in t or "school" in t or "director" in t:return "This elected board role helps govern the named public body within its legal powers and budget; confirm the specific district's duties."
 return "The exact legal responsibilities of this office have not yet been independently reviewed. Consult its official office description."
def build_clark():
 raw=read(ROOT/"clark_2026.json")
 clear=read(ROOT/"clark_clearer_editorial.json")
 motivation=read(ROOT/"clark_measure_rationales.json")
 issue=read(ROOT/"clark_issue_comparison.json")
 reg=SourceRegistry();contests=[]
 for item in raw["items"]:
  official=ed_source(reg,item["source"],"official_ballot")
  pamphlet=ed_source(reg,item["pamphlet_source"]) if item.get("pamphlet_source") else official
  common={"id":item["id"],"kind":item["type"],"title":item["title"],
    "jurisdiction":item["jurisdiction"],"source_ids":list(dict.fromkeys([official,pamphlet])),"evidence_status":"PARTIAL"}
  if item["type"]=="race":
   role=clear["races"][item["id"]]["role"]
   candidates=[]
   for idx,c in enumerate(item["candidates"]):
    source=ed_source(reg,c["profile_source"],"candidate_statement")
    text=clear["candidates"].get(c["name"],"")
    cid=item["id"]+"::"+c["name"]
    candidates.append({"id":cid,"name":c["name"],"party":c.get("party_preference"),
      "profile_status":"MATCHED","reported_bio":{
       "professional_experience":c.get("reported_experience",""),
       "government_experience":c.get("reported_office_experience",""),
       "education":c.get("reported_education","")},
      "topics_mentioned":[],"priority":claim(text,"ATTRIBUTED",[source],"Candidate-stated priorities paraphrased by the assistant; not an independent performance finding"),
      "source_ids":[source]})
   rows=[]
   q=issue["races"][item["id"]]["topics"]
   for row in q:
    positions=[]
    for idx,c in enumerate(candidates):
     side="a" if idx==0 else "b"
     t=row.get(side)
     extra=row.get(side+"_source")
     src_ids=[reg.add(extra,"official_record" if "Official" in row.get(side+"_basis","") else "journalism","Outside-source record or report")] if extra else c["source_ids"]
     state=("RECORDED" if "vote" in row.get(side+"_basis","").lower() else "REPORTED" if extra else "STATED") if t else "NOT_FOUND"
     positions.append({"candidate_id":c["id"],"state":state,
       "claim":claim(t or "", "RECORDED" if state=="RECORDED" else "REPORTED" if state=="REPORTED" else "ATTRIBUTED" if t else "UNKNOWN",src_ids if t else [],row.get(side+"_basis","") if t else row.get(side+"_missing_reason","No candidate position found; no inference"))})
    rows.append({"issue":row["issue"],"positions":positions})
   common.update({"voting_method":"standard","candidates":candidates,"issue_matrix":rows,
    "office_role":claim(role,"DRAFT_INTERPRETATION",[official],"Generic office-role explanation; exact powers vary by jurisdiction"),
    "where_they_differ":claim(clear["races"][item["id"]]["contrast"],"DRAFT_INTERPRETATION",
      [source for candidate in candidates for source in candidate["source_ids"]],
      "Prepared comparison of attributed statements from every named candidate; evidence limits remain")})
  else:
   m=clear["measures"][item["id"]];r=motivation["measures"][item["id"]]
   ids=[official,pamphlet]
   text={"big_picture":m["decision"],"yes":m["yes"],"no":m["no"],
    "supporters_why":r["supporters_reason"],"critics_why":r["opponents_reason"],
    "who_affected":m["affects"],"money":m["money"],
    "other_impacts":r["secondary_effects"],"one_to_remember":m["caution"],
    "unresolved":raw["items"][raw["items"].index(item)].get("prepared_measure",{}).get("unresolved","Further review required.")}
   sections={}
   for k,v in text.items():
    qualifier=("Attributed original opposition or editorial question, not a guaranteed outcome. "+r.get("editor_note","")) if k=="critics_why" else "Prepared, source-attributed analysis, not a completed independent legal/fiscal review."
    sections[k]=claim(v,"DRAFT_INTERPRETATION",ids,qualifier)
   common["measure_sections"]=sections
  contests.append(common)
 sources=reg.values()
 return {"schema_version":"1.0.0",
  "election":{"id":"wa-2026-11-03-general","date":raw["election_date"],"kind":"general","state":"WA",
   "source_urls":[x["url"] for x in raw["references"] if "official" in x["id"] or "sample" in x["id"]],
   "snapshot_date":DATE},
  "jurisdiction":{"state":"WA","county":"Clark","label":"Clark County, WA","scope":"countywide_inventory_not_personal_ballot",
   "official_lookup_url":"https://voter.votewa.gov/"},
  "sources":sources,"contests":contests,
  "coverage":{"topics":45,"races":30,"measures":15,"candidates":51,"unmatched_profiles":0,
  "structural_issues":[],"editorial_approved_claims":0,
  "completeness_caveat":"Candidate-submitted profiles and selected outside checks are partial; the inventory is not an individual ballot."},
  "editorial_status":"PARTIAL","release_gate":{"ready":False,"blockers":["Independent candidate/measure claim review and named editorial signoff incomplete.","County-wide inventory is not a personalized ballot."]}}
def build_multnomah():
 raw=read(ROOT/"multnomah/ballot_researched.json")
 manifest=read(ROOT/"multnomah/source_manifest.json")
 reg=SourceRegistry()
 for name,entry in manifest.items():
  reg.add(entry["url"],"official_ballot" if "ballot" in name else "official_pamphlet",
   "Original Multnomah election office PDF: "+name,sha=entry["sha256"])
 contests=[]
 for item in raw["items"]:
  official=reg.add(item["official_ballot_source"],"official_ballot","Original official candidate/measure roster page")
  common={"id":item["id"],"kind":item["type"],"title":item["title"],
   "jurisdiction":item.get("jurisdiction") or "Multnomah County / applicable district",
   "source_ids":[official],"evidence_status":"UNREVIEWED"}
  if item["type"]=="race":
   candidates=[]
   for cand in item["candidates"]:
    profile=cand.get("pamphlet_profile") or {}
    source=reg.add(profile["profile_source"],"candidate_statement","Candidate-submitted Oregon voters pamphlet, page "+str(profile["source_page"]),
     page=profile["source_page"]) if profile.get("profile_source") else None
    topics=list(dict.fromkeys(profile.get("topics_mentioned") or []))
    if source:
     if topics:
      text="The candidate-submitted pamphlet text contains words about: "+", ".join(topics)+". This automated topic list does not establish support or opposition to any policy."
     else:text="A candidate-submitted pamphlet statement was located; no policy priorities have been independently extracted or reviewed."
     priority=claim(text,"DRAFT_INTERPRETATION",[source],"Automated lexical topic detection, not a factual stance or verified policy plan")
    else:
     priority=claim("No individual candidate statement was reliably matched in the reviewed official pamphlets.","UNKNOWN",[],
      "No negative inference about qualifications, views, or whether material was submitted.")
    cid=item["id"]+"::"+cand["name"]
    candidates.append({"id":cid,"name":cand["name"],"party":cand.get("party_listed_on_ballot"),
     "profile_status":"MATCHED" if source else "NOT_LOCATED",
     "reported_bio":{str(k):str(v) for k,v in (profile.get("candidate_reported_bio") or {}).items()},
     "topics_mentioned":topics,"priority":priority,
     "source_ids":[source] if source else [official]})
   topicset=set()
   for cand in candidates:topicset.update(cand["topics_mentioned"])
   if not topicset:
    topicset={"Relevant public service and experience","Office duties and accountability"}
   rows=[]
   for issue in sorted(topicset):
    positions=[]
    for cand in candidates:
     found=issue in cand["topics_mentioned"]
     source_ids=cand["source_ids"] if found else []
     status="MENTION_ONLY" if found else "NOT_FOUND"
     meaning=("This subject appears in the candidate-submitted text, but the automated keyword match does not identify a position." if found
       else "No position established in the reviewed sources. Absence is not opposition.")
     positions.append({"candidate_id":cand["id"],"state":status,
      "claim":claim(meaning,"DRAFT_INTERPRETATION" if found else "UNKNOWN",source_ids,
       "No candidate policy stance inferred from topic keywords.")})
    rows.append({"issue":issue,"positions":positions})
   common.update({"voting_method":"ranked-choice" if item.get("voting_method")=="ranked-choice" else "standard",
    "candidates":candidates,"issue_matrix":rows,
    "office_role":claim(role_for(item["title"]),"DRAFT_INTERPRETATION",[official],
     "Generic office-role description based on the title, not a legal opinion; verify the applicable charter/statute."),
    "where_they_differ":claim(
     "The material currently available does not support a fully researched side-by-side comparison of policy positions. The matrix shows topics mentioned, NOT the candidates’ positions. A systematic source review and equal candidate questions are required.",
     "UNKNOWN",[],"No candidate-by-candidate evaluation or ranking was inferred.")})
  else:
   b=item.get("measure_brief") or {}
   args=b.get("voter_arguments") or {}
   support_refs=[reg.add(u,"official_pamphlet","Original published pamphlet argument") for u in args.get("for_sources",[])[:10]]
   oppose_refs=[reg.add(u,"official_pamphlet","Original published pamphlet argument") for u in args.get("against_sources",[])[:10]]
   yes_src=[official]
   allrefs=list(dict.fromkeys([official]+support_refs+oppose_refs))
   def c(text,status="DRAFT_INTERPRETATION",srcs=None,qual="Prepared explanation; not a completed independent legal or fiscal review"):
    return claim(text or "Not yet established from the reviewed material.",status,allrefs if srcs is None else srcs,qual)
   measure_sections={
    "big_picture":c(b.get("description"),"DRAFT_INTERPRETATION",yes_src),
    "yes":c(b.get("yes"),"DRAFT_INTERPRETATION",yes_src),
    "no":c(b.get("no"),"DRAFT_INTERPRETATION",yes_src),
    "supporters_why":c(args.get("in_favor_or_official_rationale") or b.get("tradeoff_for"),
     "DRAFT_INTERPRETATION",support_refs or yes_src,
     "Attributed published argument where available; otherwise a possible pro-rationale, not an assertion of supporters' private motives."),
    "critics_why":c(args.get("opposition_or_concerns") or b.get("tradeoff_against"),
     "DRAFT_INTERPRETATION",oppose_refs or yes_src,
     "Attributed published argument where available; otherwise an analytical concern, not an invented opposition group."),
    "who_affected":c("People and services within "+str(item.get("jurisdiction") or "the jurisdiction listed on the ballot")+
     " may be affected. Exact property/voter eligibility must be checked on the official personalized ballot.","DRAFT_INTERPRETATION",yes_src),
    "money":c(b.get("money"),"DRAFT_INTERPRETATION",yes_src,
     "Financial figures are estimates from the original source and are NOT an independently replicated forecast."),
    "other_impacts":c(b.get("tradeoff_against"),"DRAFT_INTERPRETATION",allrefs,
     "Potential secondary effects, not guaranteed outcomes."),
    "one_to_remember":c(b.get("nuance"),"DRAFT_INTERPRETATION",yes_src),
    "unresolved":c(b.get("unresolved"),"DRAFT_INTERPRETATION",yes_src)}
   common["source_ids"]=allrefs
   common["measure_sections"]=measure_sections
  contests.append(common)
 count=Counter(i["kind"] for i in contests)
 candidates_count=sum(len(i["candidates"]) for i in contests if i["kind"]=="race")
 missing=sum(c["profile_status"]=="NOT_LOCATED" for i in contests if i["kind"]=="race" for c in i["candidates"])
 assert len(contests)==66 and count["race"]==60 and count["measure"]==6
 assert candidates_count==155 and missing==25
 return {"schema_version":"1.0.0",
  "election":{"id":"or-2026-11-03-general","date":raw["election_date"],"kind":"general","state":"OR",
   "source_urls":["https://multco.us/info/november-3-2026-general-election",
    "https://sos.oregon.gov/elections/Voters-Pamphlet/Pages/default.aspx"],"snapshot_date":DATE},
  "jurisdiction":{"state":"OR","county":"Multnomah","label":"Multnomah County, OR",
   "scope":"countywide_inventory_not_personal_ballot",
   "official_lookup_url":"https://sos.oregon.gov/elections/Pages/myvote.aspx"},
  "sources":reg.values(),"contests":contests,
  "coverage":{"topics":66,"races":60,"measures":6,"candidates":155,"unmatched_profiles":25,
   "structural_issues":["Official E-019 report summary 63 contests/116 filings differs from detailed-page totals 60/109; election authority clarification pending.",
    "25 candidate-submitted profiles not reliably matched; no negative inference."],
   "editorial_approved_claims":0,
   "completeness_caveat":"Candidate issue keywords are not positions; the 130 matched profiles have not been independently verified."},
  "editorial_status":"UNREVIEWED","release_gate":{"ready":False,
   "blockers":["Unreconciled official contest/candidate totals.","25 candidate profiles not reliably located.",
    "Candidate policy positions and office roles require original-record editorial review.",
    "Measure legal/fiscal forecasts and human editorial signoff incomplete.",
    "County-wide inventory is not a personalized ballot."]}}
def main():
 (HERE/'output').mkdir(parents=True,exist_ok=True)
 jsonschema.Draft202012Validator.check_schema(read(HERE/"schema.json"))
 for key,edition in [("clark",build_clark()),("multnomah",build_multnomah())]:
  jsonschema.validate(edition,read(HERE/"schema.json"),format_checker=jsonschema.FormatChecker())
  out=HERE/"output"/(key+"_2026_canonical.json")
  out.write_text(json.dumps(edition,ensure_ascii=False,indent=2),encoding="utf8")
  print("BUILT",key,"topics",len(edition["contests"]),"sources",len(edition["sources"]),
   "candidates",edition["coverage"]["candidates"],"bytes",out.stat().st_size)
if __name__=="__main__":main()
