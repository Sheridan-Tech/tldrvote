"""Create a new jurisdiction intake manifest; this never fabricates ballot data.
New regions require an authority URL, signed-off roster reconciliation and a parser adapter.
"""
from pathlib import Path
import argparse,re,datetime,json
HERE=Path(__file__).resolve().parent
def slug(s):
 s=re.sub(r'[^a-z0-9]+','-',s.casefold()).strip('-')
 if not s:raise ValueError("Invalid jurisdiction name")
 return s
def scaffold(state,county,election_date,kind,authority_url,lookup_url):
 datetime.date.fromisoformat(election_date)
 if not re.fullmatch('[A-Z]{2}',state):raise ValueError("Use two-letter state abbreviation")
 if not authority_url.startswith('https://') or not lookup_url.startswith('https://'):
  raise ValueError("Official URLs must use HTTPS")
 id=slug(state+'-'+county+'-'+election_date+'-'+kind)
 dir=HERE/'jurisdictions'/id
 dir.mkdir(parents=True,exist_ok=False)
 cfg={'schema_version':'1.0.0','jurisdiction_id':id,
  'state':state,'county':county,'election_date':election_date,'election_type':kind,
  'election_authority_url':authority_url,'personal_ballot_lookup':lookup_url,
  'scope':'countywide_inventory_not_personal_ballot',
  'source_artifacts':[],
  'adapter_status':'NOT_IMPLEMENTED',
  'source_acquisition':'PENDING',
  'roster_reconciliation':'PENDING',
  'candidate_profiles':'PENDING',
  'claim_level_research':'PENDING',
  'human_editorial_review':'PENDING',
  'privacy_scope_review':'PENDING',
  'release_ready':False,
  'instructions':'Add approved source PDFs/APIs, register hashes, implement a jurisdiction adapter, reconcile official roster, then run structural QA and human editorial review. Never auto-publish.'}
 (dir/'manifest.json').write_text(json.dumps(cfg,indent=2),encoding='utf8')
 print('INTAKE_CREATED',dir/'manifest.json','STATUS',cfg['adapter_status'])
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--state',required=True)
 p.add_argument('--county',required=True)
 p.add_argument('--date',required=True)
 p.add_argument('--kind',choices=['general','primary','special','other'],default='general')
 p.add_argument('--authority-url',required=True)
 p.add_argument('--ballot-lookup-url',required=True)
 a=p.parse_args();scaffold(a.state,a.county,a.date,a.kind,a.authority_url,a.ballot_lookup_url)
