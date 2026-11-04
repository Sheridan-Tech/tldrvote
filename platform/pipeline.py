"""One repeatable TLDR Vote staging command; never pushes to production.
python platform/pipeline.py --preview
python platform/pipeline.py --authoritative  # must fail until reviewers resolve blockers
"""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib,datetime,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def run(cmd):
 print('RUN',str(cmd),flush=True)
 p=subprocess.run([sys.executable,'-X','utf8']+[str(x) for x in cmd],cwd=str(ROOT),capture_output=True,text=True,timeout=150)
 print(p.stdout[-8000:],flush=True)
 if p.returncode:print(p.stderr[-5000:],flush=True)
 return p
def main():
 ap=argparse.ArgumentParser()
 mode=ap.add_mutually_exclusive_group(required=True)
 mode.add_argument('--preview',action='store_true',help='Build and test with visible limitations')
 mode.add_argument('--authoritative',action='store_true',help='Block unless all claims and ballots are independently reviewed')
 ap.add_argument('--test-browser',action='store_true',help='Run Chromium end-to-end tests as well')
 args=ap.parse_args()
 steps=[]
 for file in ['build_schema.py','build_editions.py']:
  p=run([HERE/file]);steps.append([file,p.returncode])
  if p.returncode:raise SystemExit(p.returncode)
 qa=run([HERE/'validate_release.py']+(['--authoritative'] if args.authoritative else []))
 steps.append(['validate_release.py',qa.returncode])
 if qa.returncode:
  if args.authoritative and qa.returncode==2:
   print('INTENDED_RELEASE_BLOCK: editorial quality requirements remain incomplete')
  raise SystemExit(qa.returncode)
 t=run([HERE/'test_pipeline.py']);steps.append(['test_pipeline.py',t.returncode])
 if t.returncode:raise SystemExit(t.returncode)
 t=run([HERE/'research_jobs.py']);steps.append(['research_jobs.py',t.returncode])
 if t.returncode:raise SystemExit(t.returncode)
 # Local ZLT checkout already has deploy-multnomah. Fresh repo checkout can stage from root static pages.
 staged=ROOT/'deploy-multnomah'
 (staged/'multnomah').mkdir(parents=True,exist_ok=True)
 for rel in ['index.html','multnomah/index.html','transparency.html']:
  dst=staged/rel
  src=ROOT/rel
  if not dst.exists():
   if not src.exists():raise SystemExit('Missing baseline static page: '+str(src))
   shutil.copyfile(src,dst)
 p=run([HERE/'stage_multnomah_common.py']);steps.append(['stage_multnomah_common.py',p.returncode])
 if p.returncode:raise SystemExit(p.returncode)
 if args.test_browser:
  p=run([HERE/'test_standardized_ui.py']);steps.append(['test_standardized_ui.py',p.returncode])
  if p.returncode:raise SystemExit(p.returncode)
 # Export explicit deploy files; no side effects beyond local stage.
 (ROOT/'assets').mkdir(exist_ok=True)
 (ROOT/'data').mkdir(exist_ok=True)
 for x in ['standard_sections.js','standard_sections.css']:
  shutil.copyfile(HERE/x,ROOT/'assets'/x)
 for name in ['clark','multnomah']:
  shutil.copyfile(HERE/'output'/(name+'_2026_canonical.json'),ROOT/'data'/(name+'_2026_canonical.json'))
 # Standardized Multnomah HTML for PR/release, preserving existing Clark data and content.
 source=staged/'multnomah'/'index.html'
 target=ROOT/'multnomah'/'index.html'
 target.parent.mkdir(exist_ok=True)
 shutil.copyfile(source,target)
 manifest={'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'mode':'PREVIEW_NOT_AUTHORITY','published':False,'steps':steps,
  'artifacts':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
   for p in [target,ROOT/'assets'/'standard_sections.js',ROOT/'assets'/'standard_sections.css',
    ROOT/'data'/'clark_2026_canonical.json',ROOT/'data'/'multnomah_2026_canonical.json']}}
 (HERE/'output'/'pipeline_run.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
 print('STAGED_ARTIFACTS',json.dumps(manifest,indent=2))
if __name__=='__main__':main()
