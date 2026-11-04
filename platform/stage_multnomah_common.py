"""Stage Multnomah's common sections without erasing its existing source detail.
The shared JS and canonical data are external assets. No publication or editorial auto-approval.
"""
from pathlib import Path
import shutil,json,re,hashlib,zipfile,datetime
ROOT=Path(__file__).resolve().parent.parent
HERE=Path(__file__).resolve().parent
OUT=ROOT/"deploy-multnomah"
mult=OUT/"multnomah"/"index.html"
assets=OUT/"assets";data=OUT/"data"
assets.mkdir(exist_ok=True);data.mkdir(exist_ok=True)
for file in ["standard_sections.js","standard_sections.css"]:
 shutil.copy2(HERE/file,assets/file)
for k in ["clark","multnomah"]:
 shutil.copy2(HERE/"output"/(k+"_2026_canonical.json"),data/(k+"_2026_canonical.json"))
html=mult.read_text(encoding="utf8")
# Existing original embedded data MUST be unchanged.
old_json=re.search(r'<script id="seed" type="application/json">(.*?)</script>',html,re.S)
assert old_json
oldhash=hashlib.sha256(old_json.group(1).encode()).hexdigest()
linktag='<link rel="stylesheet" href="/assets/standard_sections.css">'
if linktag not in html:
 html=html.replace('</head>',linktag+'</head>',1)
script='<script src="/assets/standard_sections.js"></script>'
if script not in html:
 html=html.replace('<script id="seed" type="application/json">',script+'\n<script id="seed" type="application/json">',1)
# Keep data isolated from huge inline HTML, fetch same-origin JSON only. No external API.
fetchvar="""const standardizedPromise=fetch('/data/multnomah_2026_canonical.json').then(r=>{if(!r.ok)throw Error('Missing standardized election data');return r.json()}).catch(err=>({error:String(err)}));
function topicCorrectionUrl(x){
 const subject='TLDR Vote correction: '+x.id+' — '+x.title;
 const body='Topic: '+x.title+'\\nPage: '+location.origin+location.pathname+'#topic='+encodeURIComponent(x.id)+'\\n\\nExact problem or claim:\\n\\nSupporting original source URL:\\n\\nSuggested correction:\\n\\nPlease do not send personal voting choices, home addresses, or sensitive information.';
 return 'mailto:james@sheridantech.io?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
}
function renderStandardizedInto(x){
 const id=x.id;
 standardizedPromise.then(edition=>{
  if(selected!==id)return;
  const holder=document.getElementById('std-topic-host');
  if(!holder)return;
  if(edition.error||!window.TLDRStandard){
   holder.innerHTML='<p class="gap"><strong>Research view unavailable.</strong> Please use the original source material below. The page is not claiming these fields are verified.</p>';
   return;
  }
  holder.innerHTML=TLDRStandard.render(edition,id);
  TLDRStandard.bind(holder);
  // Existing county navigation remains usable; refresh progress when content arrives.
  requestAnimationFrame(()=>{if(typeof countyUpdatePlace==='function')countyUpdatePlace()});
 });
}
"""
anchor="const root=document.getElementById('app');"
if "const standardizedPromise=" not in html:
 assert html.count(anchor)==1
 html=html.replace(anchor,anchor+"\n"+fetchvar,1)
# Wrap legacy material in details, but do not remove it.
old="'<section id=\"mult-topic-body\">'+description+'</section>'+"
new="'<section id=\"mult-topic-body\"><div id=\"std-topic-host\" data-standard-topic=\"'+esc(x.id)+'\"><p class=\"small\">Loading shared research view…</p></div><details class=\"legacy-panel\"><summary>Original pamphlet material and additional source details</summary>'+description+'</details></section>'+"
if old in html:
 html=html.replace(old,new,1)
else:assert new in html,"Legacy wrap anchor changed unexpectedly"
# Per-topic correction request rather than generic mailto (no backend claim).
old="'<p><a class=\"button\" href=\"mailto:james@sheridantech.io?subject=TLDR%20Vote%20Multnomah%20correction\">Report a factual correction or missing source ↗</a></p></article>';".replace("&#x20;","")
new="'<p><a class=\"button\" href=\"'+esc(topicCorrectionUrl(x))+'\">Report a factual correction or missing source ↗</a></p></article>';"
if old in html:html=html.replace(old,new,1)
else:assert new in html,"Correction anchor changed unexpectedly"
# Bind standardized section on existing render, after rendering the topic.
old="if(x){\n  root.querySelectorAll('[data-back]').forEach(b=>b.onclick=countyBack);"
new="if(x){\n  renderStandardizedInto(x);\n  root.querySelectorAll('[data-back]').forEach(b=>b.onclick=countyBack);"
if old in html:html=html.replace(old,new,1)
else:assert new in html
# The new common sections load FIRST; keep original text reachable under expandable view.
css="""
.legacy-panel{margin:14px 0;padding:13px 15px;background:#fff;border:1px solid #c9d8dc}
.legacy-panel>summary{font-size:16px;color:#205869}
#std-topic-host{min-height:130px}
@media(max-width:650px){.legacy-panel{padding:10px}}
"""
if ".legacy-panel>summary" not in html:html=html.replace("</style>",css+"</style>",1)
assert hashlib.sha256(re.search(r'<script id="seed" type="application/json">(.*?)</script>',html,re.S).group(1).encode()).hexdigest()==oldhash
assert html.count("renderStandardizedInto(x)")>=1
mult.write_text(html,encoding="utf8",newline="\n")
print(json.dumps({"modified":str(mult),"bytes":mult.stat().st_size,"data_files":[str(v.name) for v in data.iterdir()],
 "asset_files":[str(v.name) for v in assets.iterdir()],"embedded_old_data_unchanged":True,"published":False},indent=2))
