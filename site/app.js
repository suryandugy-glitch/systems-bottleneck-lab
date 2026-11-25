const $ = id => document.getElementById(id);
document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(tab => {
    const active = tab === button;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('.panel').forEach(panel => {
    panel.hidden = panel.id !== button.dataset.tab;
    panel.classList.toggle('active', !panel.hidden);
  });
}));
function chartPlan(){
  const skew = Number($('plan-skew').value)/100, indexed = $('plan-index').value==='index';
  $('skew-value').textContent = Math.round(skew*100)+'%';
  const sizes=[100,500,1000,5000,10000,50000];
  const costs=sizes.map(n=>indexed?(.12+Math.log2(n)*.014+skew*n*.00014):(.1+n*.00055));
  const max=Math.max(...costs)*1.12, x=i=>52+i*99, y=v=>250-v/max*210;
  const lines=[0,.25,.5,.75,1].map(t=>'<line x1="45" x2="558" y1="'+y(max*t)+'" y2="'+y(max*t)+'" stroke="#29384f" stroke-dasharray="4 5"/><text x="7" y="'+(y(max*t)+4)+'" fill="#7991aa" font-size="11">'+(max*t).toFixed(1)+'</text>').join('');
  const poly=costs.map((v,i)=>x(i)+','+y(v)).join(' ');
  const dots=costs.map((v,i)=>'<circle cx="'+x(i)+'" cy="'+y(v)+'" r="5" fill="#86f1c8"/>').join('');
  const ticks=sizes.map((v,i)=>'<text x="'+x(i)+'" y="278" text-anchor="middle" fill="#8499b3" font-size="11">'+(v>=1000?v/1000+'k':v)+'</text>').join('');
  $('plan-chart').innerHTML=lines+'<polyline fill="none" stroke="#86f1c8" stroke-width="3" points="'+poly+'"/>'+dots+ticks;
  $('plan-summary').innerHTML='At <strong>'+sizes.at(-1).toLocaleString()+' rows</strong>, modeled cost is <strong>'+costs.at(-1).toFixed(2)+' ms</strong>. Real execution plans and latency measurements require the Python CLI.';
}
let seed=7;function rnd(){seed=(seed*1664525+1013904223)>>>0;return(seed+.5)/4294967296}
function normal(){return Math.sqrt(-2*Math.log(rnd()))*Math.cos(2*Math.PI*rnd())}
function percentile(sorted,p){const x=(sorted.length-1)*p,lo=Math.floor(x);return sorted[lo]+(sorted[Math.ceil(x)]-sorted[lo])*(x-lo)}
function chartTail(){
  const fanout=Number($('fanout').value),threshold=Number($('hedge').value);seed=7;
  $('fanout-value').textContent=fanout;$('hedge-value').textContent=threshold;
  const base=[],hedged=[];let extra=0;
  for(let i=0;i<5000;i++){let b=0,h=0;
    for(let j=0;j<fanout;j++){const original=Math.exp(Math.log(20)+normal());let effective=original;if(original>threshold){extra++;effective=Math.min(original,threshold+Math.exp(Math.log(20)+normal()))}b=Math.max(b,original);h=Math.max(h,effective)}
    base.push(b);hedged.push(h);
  }
  base.sort((a,b)=>a-b);hedged.sort((a,b)=>a-b);
  const labels=[50,95,99],max=percentile(base,99)*1.08;
  $('tail-bars').innerHTML=labels.map(p=>{let a=percentile(base,p),b=percentile(hedged,p);return '<div class="bar-line"><span>P'+p+' base</span><div class="track"><div class="fill" style="width:'+100*a/max+'%"></div></div><span>'+a.toFixed(1)+' ms</span></div><div class="bar-line"><span>P'+p+' hedge</span><div class="track"><div class="fill hedged" style="width:'+100*b/max+'%"></div></div><span>'+b.toFixed(1)+' ms</span></div>'}).join('');
  $('tail-summary').innerHTML='Modeled p99 reduction: <strong>'+((1-percentile(hedged,99)/percentile(base,99))*100).toFixed(1)+'%</strong> · Backend work amplification: <strong>'+(1+extra/(5000*fanout)).toFixed(2)+'×</strong>. Assumes independent, unlimited-capacity replicas.';
}
function analyzeLocks(){
  const lines=$('lock-input').value.split(/\n/).map(x=>x.split('>').map(s=>s.trim()).filter(Boolean)).filter(x=>x.length);
  const edges=new Map();for(const line of lines)for(let i=0;i<line.length;i++){if(!edges.has(line[i]))edges.set(line[i],new Set());for(let j=i+1;j<line.length;j++)if(line[j]!==line[i])edges.get(line[i]).add(line[j])}
  let witness=null;const active=new Set(),visited=new Set(),stack=[];
  function dfs(node){visited.add(node);active.add(node);stack.push(node);
    for(const next of edges.get(node)||[]){if(active.has(next)){witness=[...stack.slice(stack.indexOf(next)),next];return true}if(!visited.has(next)&&dfs(next))return true}
    stack.pop();active.delete(node);return false}
  for(const node of edges.keys())if(!visited.has(node)&&dfs(node))break;
  const out=$('lock-results');out.replaceChildren();
  const title=document.createElement('h3');title.className=witness?'warn':'good';title.textContent=witness?'Potential lock-order cycle detected':'No cycles detected';out.append(title);
  const detail=document.createElement('p');detail.textContent=edges.size+' locks observed · '+[...edges.values()].reduce((a,s)=>a+s.size,0)+' directed ordering constraints';out.append(detail);
  const code=document.createElement('code');code.textContent=witness?witness.join(' → '):'Acyclic lock ordering in the supplied sequences';out.append(code);
  const note=document.createElement('p');note.textContent='Structural risk only. Runtime feasibility depends on thread overlap and lock release timing.';out.append(note);
}
$('run-plan').addEventListener('click',chartPlan);$('run-tail').addEventListener('click',chartTail);$('run-lock').addEventListener('click',analyzeLocks);
$('plan-skew').addEventListener('input',()=>{$('skew-value').textContent=$('plan-skew').value+'%'});
$('fanout').addEventListener('input',()=>{$('fanout-value').textContent=$('fanout').value});
$('hedge').addEventListener('input',()=>{$('hedge-value').textContent=$('hedge').value});
chartPlan();chartTail();analyzeLocks();
