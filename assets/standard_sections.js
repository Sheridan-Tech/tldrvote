/* TLDR Vote v1 shared, data-driven editorial sections. No inferred candidate stances.
   A claim's status and provenance are displayed; this renderer never approves research. */
(function(scope){
 'use strict';
 function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
 function link(src,label){
  if(!src||typeof src.url!=='string'||!src.url.startsWith('https://'))return '';
  return '<a href="'+esc(src.url)+'" target="_blank" rel="noopener noreferrer">'+esc(label||src.label)+'</a>';
 }
 function sourceLinks(claim,refs){
  const out=(claim?.source_ids||[]).map(id=>refs[id]).filter(Boolean);
  return out.length?'<span class="std-cites">Sources: '+out.map((s,i)=>link(s,s.label||('Record '+(i+1)))).join(' · ')+'</span>':
   '<span class="std-cites">No claim-specific original source established.</span>';
 }
 function claimText(c,refs,{hideCites=false}={}){
  if(!c)return '<p class="std-missing">Not researched yet.</p>';
  const noEvidence=c.status==='UNKNOWN'||!c.text;
  const qualifier=c.qualifier||'';
  return '<p class="'+(noEvidence?'std-missing':'')+'">'+esc(c.text||'Not yet established.')+'</p>'+
   (qualifier?'<p class="std-limit">'+esc(qualifier)+'</p>':'')+
   (hideCites?'':sourceLinks(c,refs));
 }
 function sourceList(ids,refs){
  const unique=[...new Set(ids||[])].map(id=>refs[id]).filter(Boolean);
  return unique.length?'<ul class="std-source-list">'+unique.map(s=>
   '<li>'+link(s,s.label)+(s.page?' · PDF page '+esc(s.page):'')+
   (s.sha256?' · preserved SHA256 recorded':'')+'</li>').join('')+'</ul>':
   '<p class="std-missing">No original source has been linked.</p>';
 }
 function renderRace(x,refs){
  const people=x.candidates||[];
  const sections='<section class="std-section" id="std-office"><h3>What this office actually controls</h3>'+
   claimText(x.office_role,refs)+'</section>'+
   '<section class="std-section" id="std-priorities"><h3>Candidates’ stated priorities</h3>'+
    '<p class="std-preface">The original pamphlet profiles are candidate-submitted and not independently fact-checked. Where research is unfinished, this section shows what the text mentions—not an invented policy position.</p>'+
    '<div class="std-candidate-grid">'+people.map(p=>
      '<article class="std-candidate"><h4>'+esc(p.name)+'</h4>'+
      (p.party?'<p class="std-limit">Ballot party designation: '+esc(p.party)+'</p>':'')+
      (p.profile_status==='MATCHED'?claimText(p.priority,refs):
       '<p class="std-missing">No standalone candidate statement reliably identified in the reviewed pamphlet. This says nothing about qualifications or beliefs.</p>')+
      sourceList(p.source_ids,refs)+'</article>').join('')+'</div></section>';
  const rows=(x.issue_matrix||[]);
  const header='<section class="std-section" id="std-issues"><h3>Side-by-side: where each candidate stands on the main issues</h3>'+
   '<p class="std-warning"><strong>Research incomplete:</strong> an issue mentioned in a pamphlet is <em>not</em> proof that a candidate supports or opposes it. We show the same issues for everyone. Blank positions stay blank until independently checked.</p>';
  const renderRow=(row,idx)=>'<section class="std-topic" data-std-row="'+idx+'"><h4>'+esc(row.issue)+'</h4>'+
   '<div class="std-position-grid">'+row.positions.map(position=>{
    const p=people.find(c=>c.id===position.candidate_id);
    const name=p?p.name:'Unmatched candidate ID';
    const state=position.state;
    const kind=state==='MENTION_ONLY'?'Topic mentioned; position not established':state==='NOT_FOUND'?'No documented position in reviewed material':state+' — review source';
    return '<div class="std-position"><strong>'+esc(name)+'</strong>'+
      '<div class="std-state">'+esc(kind)+'</div>'+claimText(position.claim,refs,{hideCites:false})+'</div>';
   }).join('')+'</div></section>';
  let comparison='';
  if(people.length>6&&rows.length>1){
   comparison='<label for="std-issue-choice">Choose an issue to compare</label><select id="std-issue-choice" data-std-issue>'+
    rows.map((row,i)=>'<option value="'+i+'">'+esc(row.issue)+'</option>').join('')+'</select>'+
    rows.map(renderRow).join('');
  }else{
   comparison=rows.slice(0,4).map(renderRow).join('')+
     (rows.length>4?'<details class="std-more"><summary>See '+(rows.length-4)+' more issue comparisons</summary>'+
      rows.slice(4).map((r,i)=>renderRow(r,i+4)).join('')+'</details>':'');
  }
  const differences='<section class="std-section" id="std-differences"><h3>Where they differ</h3>'+
   claimText(x.where_they_differ,refs)+'</section>';
  return sections+header+comparison+'</section>'+differences;
 }
 function renderMeasure(x,refs){
  const s=x.measure_sections||{};
  const panel=(title,id)=>'<section class="std-section" id="std-'+id+'"><h3>'+esc(title)+'</h3>'+claimText(s[id],refs)+'</section>';
  const choices='<div class="std-choice-grid"><section><h3>What a Yes vote would do</h3>'+
   claimText(s.yes,refs)+'</section><section><h3>What a No vote would do</h3>'+
   claimText(s.no,refs)+'</section></div>';
  return panel('The big picture','big_picture')+
   '<div class="std-section" id="std-choices">'+choices+'</div>'+
   panel('Why supporters want it','supporters_why')+
   panel('Why critics question it','critics_why')+
   panel('Who would be affected','who_affected')+
   panel('Money and financial effects','money')+
   panel('Other impacts and possible side effects','other_impacts')+
   panel('One thing to remember','one_to_remember')+
   panel('What remains unresolved','unresolved');
 }
 function render(edition,topicId){
  const x=edition.contests.find(t=>t.id===topicId);
  if(!x)return '<div class="std-error">No standardized content for this topic.</div>';
  const refs=Object.fromEntries(edition.sources.map(s=>[s.id,s]));
  const body=x.kind==='race'?renderRace(x,refs):renderMeasure(x,refs);
  return '<div class="std-explainer" data-std-topic="'+esc(topicId)+'">'+
   '<p class="std-eyebrow">TLDR VOTE · STANDARDIZED RESEARCH VIEW</p>'+
   '<h2>Understand this '+(x.kind==='race'?'race':'measure')+'</h2>'+
   '<p class="std-warning">Independent, source-linked research preview. This is not a personalized ballot or a completed fact-check. Original election sources, unresolved claims and candidate-submitted material are distinguished below.</p>'+
   body+
   '<section class="std-section" id="std-sources"><h3>Original sources and evidence status</h3>'+
   sourceList(x.source_ids,refs)+
   '<p class="std-limit">Editorial review: '+esc(x.evidence_status)+'. This source record is not a verified election-authority endorsement.</p></section>'+
   '<section class="std-section std-feedback" id="std-feedback"><h3>Report a correction or missing source</h3>'+
   '<p>Please include the exact claim and an original source if possible. Reports are not published as corrections until reviewed.</p>'+
   '<p><a href="'+esc('https://github.com/Sheridan-Tech/tldrvote/issues/new?template=correction.yml&title='+encodeURIComponent('[Correction] '+x.title))+'" target="_blank" rel="noopener noreferrer">Open a tracked public correction report (GitHub sign-in required)</a></p>'+
   '<p><a href="'+esc('mailto:james@sheridantech.io?subject='+encodeURIComponent('TLDR Vote correction — '+x.id)+'&body='+encodeURIComponent('Topic: '+x.title+'\nPage: '+location.href+'\nClaim or error:\n\nPrimary source URL:\n\nSuggested correction:\n'))+'">Email a private correction instead</a></p>'+
   '<p class="std-limit">Do not send your private voting choices, registration details or home address.</p></section>'+
   '</div>';
 }
 function bind(container){
  if(!container)return;
  const input=container.querySelector('select[data-std-issue]');
  if(input){
   const update=()=>{
    for(const row of container.querySelectorAll('.std-topic[data-std-row]'))row.hidden=row.dataset.stdRow!==input.value;
   };
   input.onchange=update;update();
  }
 }
 scope.TLDRStandard={render,bind};
})(window);
