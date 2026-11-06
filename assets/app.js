const $=s=>document.querySelector(s);
let items=[],meta={},intel={},view="overview";
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=s=>{if(!s)return"Date unknown";const d=new Date(s);return isNaN(d)?"Date unknown":d.toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"});};
const triage=x=>intel.items?.[x.id]||null;
const priorityOrder={high:0,medium:1,low:2};
function releaseDetails(x){
 if(x.category!=="Release"&&x.category!=="Component")return"";
 const components=(x.new_components||[]).map(c=>'<li><b>'+esc(c.type)+'</b> / <code>'+esc(c.name)+'</code> — '+esc(c.evidence)+'</li>').join("");
 const sections=(x.change_sections||[]).slice(0,12).map(s=>'<section class="release-section"><b>'+esc(s.heading)+'</b><ul>'+((s.items||[]).slice(0,6).map(v=>'<li>'+esc(v)+'</li>').join(""))+'</ul></section>').join("");
 const notes=x.release_notes?'<details class="release-details"><summary>Parsed release notes · '+((x.change_sections||[]).length)+' sections</summary>'+(components?'<b class="action-label">New components detected</b><ul>'+components+'</ul>':"")+(sections||'<p>'+esc(x.release_notes.slice(0,2500))+'</p>')+'<details><summary>Full upstream notes (raw)</summary><pre>'+esc(x.release_notes)+'</pre></details></details>':"";
 return(x.component_type?'<div class="component-pill">NEW '+esc(x.component_type.toUpperCase())+' · '+esc(x.component_name)+'</div>':"")+notes;
}
function editorial(x,t){
 if(view!=="triage"||!t)return"";
 const tags=(t.themes||[]).map(z=>'<span class="tag">'+esc(z.label)+'</span>').join("");
 const evidence=(t.evidence||[]).slice(0,3).map(e=>'<p><b>'+esc(e.theme)+':</b> '+esc(e.text)+'</p>').join("");
 const actions=(t.review_actions||[]).map(a=>'<li>'+esc(a)+'</li>').join("");
 return'<div class="editorial"><div class="editorial-head">WHY THIS ITEM WAS FLAGGED · '+esc(t.confidence)+'</div><p><b>Interpretation:</b> '+esc(t.why_it_matters)+'</p><div class="tags">'+tags+'</div>'+(actions?'<b class="action-label">Suggested review</b><ul>'+actions+'</ul>':"")+(evidence?'<details><summary>Matched source evidence</summary>'+evidence+'</details>':"")+'</div>';
}
function card(x){
 const t=triage(x),category=(x.category||"Signal").toLowerCase();
 const badge='<span class="tag '+esc(category)+'">'+esc((x.category||"SIGNAL").toUpperCase())+'</span>';
 const priority=view==="triage"&&t?'<span class="priority '+esc(t.priority)+'">'+esc(t.priority.toUpperCase())+' ATTENTION</span>':"";
 const metaLine='<div class="meta">'+badge+'<span class="tag">'+esc(x.project||"Ecosystem")+'</span>'+(x.component_type?'<span class="tag component">'+esc(x.component_type)+'</span>':"")+priority+'<time>'+date(x.date)+'</time></div>';
 return'<article class="item">'+metaLine+'<h3>'+esc(x.title)+'</h3>'+(x.version?'<span class="version">'+esc(x.version)+'</span>':"")+'<p>'+esc(x.summary||"Open the primary source for details.")+'</p>'+releaseDetails(x)+editorial(x,t)+'<div class="bottom"><span>'+esc(x.source||"Public source")+'</span><a href="'+esc(x.url||"#")+'" target="_blank" rel="noopener">OPEN PRIMARY SOURCE ↗</a></div></article>';
}
function draw(){
 const q=$("#q").value.toLowerCase(),category=$("#category").value,project=$("#project").value,sort=$("#sort").value;
 let rows=[...items];
 if(view==="overview")rows=rows.slice(0,8);
 if(view==="triage")rows=rows.filter(x=>triage(x)?.needs_review);
 if(view==="releases")rows=rows.filter(x=>["Release","Component","Plugin"].includes(x.category));
 if(category)rows=rows.filter(x=>x.category===category);
 if(project)rows=rows.filter(x=>x.project===project);
 if(q)rows=rows.filter(x=>[x.title,x.summary,x.project,x.category,x.source,x.version,x.release_notes,triage(x)?.why_it_matters,(triage(x)?.themes||[]).map(t=>t.label).join(" ")].join(" ").toLowerCase().includes(q));
 if(view==="triage")rows.sort((a,b)=>(priorityOrder[triage(a)?.priority]??3)-(priorityOrder[triage(b)?.priority]??3)||(new Date(b.date||0)-new Date(a.date||0)));
 else rows.sort((a,b)=>(new Date(a.date||0)-new Date(b.date||0))*(sort==="new"?-1:1));
 $("#count").textContent=rows.length+" SIGNALS";
 $("#list").innerHTML=rows.length?rows.map(card).join(""):'<div class="empty">No matching signals. Try another project or clear a filter.</div>';
}
function sources(){
 const rows=meta.sources||[];
 $("#count").textContent=rows.length+" CONFIGURED SOURCES";
 $("#list").innerHTML=rows.map(s=>'<article class="item"><div class="meta"><span class="tag">'+esc((s.type||"source").toUpperCase())+'</span><span class="tag">'+esc(s.project)+'</span></div><h3>'+esc(s.name)+'</h3><p>'+esc(s.url)+'</p><div class="bottom"><span>MONITORED AUTOMATICALLY</span><a href="'+esc(s.url)+'" target="_blank" rel="noopener">VISIT SOURCE ↗</a></div></article>').join("");
}
const views={
overview:["OVERVIEW","Signal Desk<span>.</span>","Latest intelligence","A short front page of the newest signals. Open the feed for the complete archive."],
feed:["INTELLIGENCE FEED","Intelligence feed<span>.</span>","All collected signals","Search and filter releases, new components, articles, community updates, and videos."],
triage:["EDITORIAL TRIAGE","Editorial triage<span>.</span>","Items flagged for review","Only entries with explicit source-text matches appear here. Each item shows its own matched evidence and suggested review."],
releases:["RELEASES & COMPONENTS","Releases<span>.</span>","Upstream releases, components, and plugins","Release notes, new Collector components, Grafana plugin catalog additions and version changes."],
sources:["SOURCE DIRECTORY","Source directory<span>.</span>","Configured source registry","The RSS, community, video, and GitHub release sources polled by the collection workflow."]
};
function change(next){
 if(!views[next])return;
 view=next;const [crumb,title,heading,subtitle]=views[next];
 $("#crumb").textContent=crumb;$("#title").innerHTML=title;$("#feed-title").textContent=heading;$("#subtitle").textContent=subtitle;
 document.querySelectorAll("[data-view]").forEach(n=>n.classList.toggle("active",n.dataset.view===next));
 if(next==="sources")sources();else draw();
}
async function init(){
 $("#today").textContent=new Date().toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"});
 try{
  const r=await Promise.all([
   fetch("data/updates.json?v=3").then(x=>{if(!x.ok)throw Error("updates");return x.json()}),
   fetch("data/meta.json?v=3").then(x=>{if(!x.ok)throw Error("meta");return x.json()}),
   fetch("data/intelligence.json?v=3").then(x=>x.ok?x.json():({items:{}})).catch(()=>({items:{}}))
  ]);
  items=r[0].items||[];meta=r[1];intel=r[2];
  $("#status").textContent="OPERATIONAL";$("#last").textContent=meta.generated_at?"Last sync "+date(meta.generated_at):"Awaiting sync";
  $("#total").textContent=items.length;$("#releases").textContent=items.filter(x=>["Release","Component","Plugin"].includes(x.category)).length;
  $("#sources").textContent=items.filter(x=>triage(x)?.needs_review).length;
  $("#synced").textContent=meta.generated_at?new Date(meta.generated_at).toLocaleString():"PENDING";
  $("#nav-count").textContent=items.length;$("#triage-count").textContent=items.filter(x=>(triage(x)?.themes||[]).length>0).length;
  const projects=[...new Set(items.map(x=>x.project).filter(Boolean))].sort();
  $("#project").innerHTML='<option value="">All projects</option>'+projects.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");
  change("overview");
 }catch(error){
  $("#status").textContent="NO DATA";$("#list").innerHTML='<div class="empty">The archive could not be loaded. Check the latest GitHub Actions collection run.</div>';
  $("#total").textContent="0";$("#releases").textContent="0";$("#sources").textContent="—";$("#synced").textContent="PENDING";
 }
}
document.addEventListener("click",event=>{
 const nav=event.target.closest("[data-view]");
 if(nav){event.preventDefault();change(nav.dataset.view);return;}
 const shortcut=event.target.closest("[data-filter]");
 if(shortcut){event.preventDefault();$("#q").value=shortcut.dataset.filter;change("feed");}
});
["q","category","project","sort"].forEach(id=>$("#"+id).addEventListener("input",()=>view==="sources"?sources():draw()));
document.addEventListener("keydown",event=>{if(event.key==="/"&&!["INPUT","TEXTAREA"].includes(document.activeElement.tagName)){event.preventDefault();$("#q").focus();}});
init();
