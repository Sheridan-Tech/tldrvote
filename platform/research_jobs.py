"""Create deterministic research work units from canonical election records.
No AI calls. All generated work remains OPEN until cited evidence and human review exist.
"""
from pathlib import Path
import json,hashlib,collections
HERE=Path(__file__).resolve().parent
def make():
 jobs=[]
 for county in ('clark','multnomah'):
  edition=json.loads((HERE/'output'/(county+'_2026_canonical.json')).read_text('utf8'))
  for contest in edition['contests']:
   if contest['kind']=='race':
    for candidate in contest['candidates']:
     for topic in contest['issue_matrix']:
      position=next(v for v in topic['positions'] if v['candidate_id']==candidate['id'])
      if position['state'] not in ('NOT_FOUND','MENTION_ONLY'):continue
      title=contest['title']
      question=('What documented position, if any, has '+candidate['name']+' publicly expressed on '+topic['issue']+
       ' while campaigning for '+title+' in the 2026 election? Record exact wording, date, source and counterevidence; do not infer from affiliation.')
      key=county+'|'+contest['id']+'|'+candidate['id']+'|'+topic['issue']
      jobs.append({'id':'job-'+hashlib.sha256(key.encode()).hexdigest()[:18],
       'edition':county,'topic_id':contest['id'],'subject':candidate['name'],
       'work_type':'candidate_issue_position','question':question,
       'starting_source_ids':candidate['source_ids'],
       'required_evidence':['exact dated primary statement or vote','source passage and URL','same question applied to opponents',
         'contrary evidence and relevant context','human editorial signoff'],
       'result_state':'OPEN','release_approved':False,'blocked_reason':'No verified comparable position yet'})
    jobs.append({'id':'job-'+hashlib.sha256((county+'|'+contest['id']+'|office').encode()).hexdigest()[:18],
      'edition':county,'topic_id':contest['id'],'subject':contest['title'],'work_type':'office_powers_review',
      'question':'Verify exact legal powers and limits of this office in its jurisdiction, with a state/county/city primary source.',
      'starting_source_ids':contest['source_ids'],'required_evidence':['operative authority','scope and dates','human reviewer'],
      'result_state':'OPEN','release_approved':False,'blocked_reason':'Office-role summary is editorial draft'})
   else:
    jobs.append({'id':'job-'+hashlib.sha256((county+'|'+contest['id']+'|measure').encode()).hexdigest()[:18],
      'edition':county,'topic_id':contest['id'],'subject':contest['title'],'work_type':'measure_legal_fiscal_review',
      'question':'Verify operative Yes/No legal effects, source-attributed reasons, side effects, cost assumptions, time periods and critical caveats for '+contest['title'],
      'starting_source_ids':contest['source_ids'],
      'required_evidence':['proposed text and official analysis','recomputed financial examples and assumptions',
        'attributed for/against argument if filed','implementation alternatives or tradeoffs',
        'counterevidence','human legal/fiscal reviewer'],
      'result_state':'OPEN','release_approved':False,'blocked_reason':'Full independent legal/fiscal and editorial review incomplete'})
 report={'schema_version':'1.0','purpose':'Research jobs for human/AI-assisted investigation; output MUST be reviewed before public use.',
  'rules':['Never infer an absent candidate stance','Do not score or endorse candidates or ballots',
   'Require primary evidence and passage-specific citations','A model draft cannot self-approve a political finding',
   'Conflicting material remains attributed and unresolved until reviewed'],
  'jobs':jobs,'counts':dict(collections.Counter(j['work_type'] for j in jobs))}
 (HERE/'output'/'research_jobs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'jobs':len(jobs),'types':report['counts'],'approved':0},indent=2))
if __name__=='__main__':make()
