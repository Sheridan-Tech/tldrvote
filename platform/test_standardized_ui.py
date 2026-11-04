"""Test shared standardized sections, original evidence preservation and all 111 topics.
Local staging only. Browser checks do not independently fact-check political claims.
"""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright
from collections import Counter
import json
R=Path(r'C:\Users\James\AI-Workspace\Projects\TLDR-Vote')
root=R/'deploy-multnomah'
mult=json.loads((R/'platform/output/multnomah_2026_canonical.json').read_text("utf8"))
clark=json.loads((R/'platform/output/clark_2026_canonical.json').read_text("utf8"))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)))
Thread(target=server.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(server.server_port)
report={"checked_topics":0,"multnomah_measures":0,"multnomah_races":0,
 "candidate_entries":0,"clark_canonical_rendered":0,"source_links":0,
 "labeled_missing_positions":0,"no_js_errors":True,"desktop_mobile":False,
 "errors":[]}
try:
 with sync_playwright() as pw:
  try:b=pw.chromium.launch(headless=True)
  except Exception:b=pw.chromium.launch(channel='chrome',headless=True)
  p=b.new_page(viewport={'width':1280,'height':900})
  p.on('pageerror',lambda e:report["errors"].append(str(e)))
  p.on('response',lambda r:report["errors"].append("HTTP "+str(r.status)+" "+r.url) if r.status>=400 and r.url.startswith(base) else None)
  res=p.goto(base+'/multnomah/',wait_until='domcontentloaded')
  assert res.status==200
  assert p.locator('[data-open]').count()==66
  for item in mult['contests']:
   p.locator('[data-open="'+item['id']+'"]').first.click()
   host=p.locator('#std-topic-host')
   host.locator('.std-explainer').wait_for(timeout=9000)
   assert host.get_by_role('heading',name='Original sources and evidence status').count()==1
   assert p.locator('details.legacy-panel').count()==1
   assert not p.locator('details.legacy-panel').evaluate('(el)=>el.open')
   assert p.locator('details.legacy-panel>summary').count()==1
   if item['kind']=='race':
    assert host.get_by_role('heading',name='What this office actually controls').count()==1
    assert host.get_by_role('heading',name='Candidates’ stated priorities').count()==1
    assert host.get_by_role('heading',name='Side-by-side: where each candidate stands on the main issues').count()==1
    assert host.get_by_role('heading',name='Where they differ').count()==1
    assert host.locator('.std-candidate').count()==len(item['candidates'])
    report['candidate_entries']+=len(item['candidates'])
    assert host.locator('.std-position').count()>=len(item['candidates'])
    assert 'Research incomplete' in host.inner_text()
    if item['id']=='or-us-senator':
     assert 'automated topic list does not establish support or opposition' in host.inner_text()
    if len(item['candidates'])>6:
     sel=host.locator('select[data-std-issue]')
     if len(item['issue_matrix'])>1:
      assert sel.count()==1
      if sel.locator('option').count()>1:
       sel.select_option('1')
       assert host.locator('.std-topic:visible').count()==1
    report['multnomah_races']+=1
   else:
    for heading in ['The big picture','What a Yes vote would do','What a No vote would do',
      'Why supporters want it','Why critics question it','Who would be affected',
      'Money and financial effects','Other impacts and possible side effects',
      'One thing to remember','What remains unresolved']:
     assert host.get_by_role('heading',name=heading).count()==1,(item['id'],heading)
    report['multnomah_measures']+=1
   assert host.locator('a[href^="https://"]').count()>=1
   report['source_links']+=host.locator('a[href^="https://"]').count()
   assert item['id'] in p.locator('a[href^="mailto:"][class="button"]').last.get_attribute('href')
   p.locator('details.legacy-panel>summary').click()
   assert p.locator('details.legacy-panel').evaluate('(e)=>e.open')
   p.locator('#county-wayfinder [data-county-back]').click()
   p.locator('[data-open]').first.wait_for()
   report['checked_topics']+=1
  # Both counties can be rendered by exactly the same JS component.
  rendered=p.evaluate('''async()=>{const x=await (await fetch('/data/clark_2026_canonical.json')).json();return x.contests.map(c=>({kind:c.kind,html:TLDRStandard.render(x,c.id)}))}''')
  assert len(rendered)==45
  assert sum(x['kind']=='measure' for x in rendered)==15
  assert sum(x['kind']=='race' for x in rendered)==30
  assert all('Original sources and evidence status' in x['html'] for x in rendered)
  report['clark_canonical_rendered']=len(rendered)
  p.set_viewport_size({'width':390,'height':844})
  p.goto(base+'/multnomah/#topic=or-rcv-city-of-portland-councilor-district-3',wait_until='domcontentloaded')
  p.locator('#std-topic-host .std-explainer').wait_for()
  assert p.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2')
  p.screenshot(path=str(R/'platform/output/multnomah_standard_mobile.png'))
  report['desktop_mobile']=True
  b.close()
 report['no_js_errors']=not report["errors"]
 assert report['no_js_errors'],report['errors']
 assert report['checked_topics']==66 and report['clark_canonical_rendered']==45
 assert report['candidate_entries']==155 and report['multnomah_measures']==6
 report['status']="PASS"
finally:
 server.shutdown();server.server_close()
(R/'platform/output/standardized_ui_test.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps(report,ensure_ascii=False,indent=2))
