/* every stop this train has left, with CTA's predicted arrival at each (Train Tracker "follow this train"),
   fetched when its card opens and every 30 s while it stays open */
const FOLLOW=new Map();let followBusy=false;                            // train id -> {at, stops} or {at, err}
async function fetchFollow(t){const run=t.run&&t.run.no;if(!run||followBusy)return;followBusy=true;
  try{const r=await fetch(WORKER_URL+"/cta/follow?run="+encodeURIComponent(run),{cache:"no-store"});let d=null;try{d=await r.json()}catch(_){}
    FOLLOW.set(t.id,d&&Array.isArray(d.stops)?{at:Date.now(),stops:d.stops}:{at:Date.now(),err:true})}
  catch(_){FOLLOW.set(t.id,{at:Date.now(),err:true})}
  finally{followBusy=false;if(selected===t)renderCard()}}
function renderCard(){
  const t=selected;if(!t)return;
  const r=t.L.routes[t.ri],s=t.lastObsS,n=r.st.length,v=t.cta||{};      // the latest REAL fix, never the animated position
  const near=Math.round(s),atStn=Math.abs(s-near)<0.12,nowMs=serverNow();
  // where it is, from GPS
  let nowRow="",gpsNext=null,lastRec=null;
  if(t.dirSign!==0){
    const lo=Math.floor(s),hi=Math.min(n-1,Math.ceil(s));
    lastRec=t.dirSign>0?stationAt(t,atStn?near:lo):stationAt(t,atStn?near:hi);
    const ni=t.dirSign>0?(atStn?near+1:hi):(atStn?near-1:lo);
    if(ni>=0&&ni<n&&!(atStn&&(ni===near)))gpsNext=stationAt(t,ni);
    nowRow=`<div class="row"><span class="kick2">${atStn?"At":"Passed"}</span><span class="v">${esc(stnName(lastRec))}</span><span></span></div>`;
  }else nowRow=`<div class="row"><span class="kick2">Near</span><span class="v">${esc(stnName(stationAt(t,near)))}</span><span></span></div>`;
  // where it's going next: CTA's own next station and its predicted arrival there
  let nextRow="";const nx=v.next_sta_id&&STN.get(v.next_sta_id);
  if(nx&&nx!==lastRec){const tm=+v.arrives_at||0,m=tm?Math.round((tm-nowMs)/60000):null;
    nextRow=`<div class="row"><span class="kick2">${v.approaching?"Arriving":"Next"}</span><span class="v">${esc(stnName(nx))}</span>`
      +(tm?`<span class="t"><b>${v.approaching||m<=1?"Due":m+" min"}</b> ${fmtClock(tm/1000)}</span>`:"<span></span>")+`</div>`}
  else if(gpsNext)nextRow=`<div class="row"><span class="kick2">Next</span><span class="v">${esc(stnName(gpsNext))}</span><span></span></div>`;
  // the next few stops with their predicted times
  let upRows="";
  if(mode!=="sim"&&t.run&&t.run.no){const f=FOLLOW.get(t.id);
    if(!f||Date.now()-f.at>(f.err?20000:30000))fetchFollow(t);
    const list=f&&f.stops?f.stops.filter(e=>!e.arrives_at||e.arrives_at>nowMs-45000).slice(0,4):[];      // just the next 4
    if(list.length)upRows=`<div class="ups"><span class="kick2 uh">Next stops</span>`+list.map((e,i)=>{
      const rec=STN.get(e.next_sta_id),nm=rec?stnName(rec):shortName(e.station),tm=+e.arrives_at||0,m=tm?Math.round((tm-nowMs)/60000):null;
      const w=e.approaching||(m!=null&&m<=1)?"Due":m!=null?m+" min":"";
      return`<div class="row${e.scheduled?" pred":""}"><span class="kick2">${i===0?(e.approaching?"Arriving":"Next"):""}</span><span class="v">${esc(nm)}</span>`
        +`<span class="t"><b>${w}</b> ${tm?fmtClock(tm/1000):""}</span></div>`}).join("")+`</div>`}
  const headline=v.dest?`to ${esc(v.dest)}`:"Destination not known";
  const age=serverNow()-t.updated;
  const foot=mode==="sim"?`<span>Simulated train, not real</span>`:t.stale?`<span class="wn">No new position for ${ago(age).replace(" ago","")}</span>`
    :v.delayed?`<span class="wn">CTA reports a delay</span>`:`<span>GPS position ${ago(age)}</span>`;
  const sub=[trainLabel(t),r.branch].filter(Boolean).join(" · ");
  const keep=card.querySelector(".ups"),scroll=keep?keep.scrollTop:0;      // the card redraws every second: keep the list where you scrolled it
  card.innerHTML=
   `<div class="hd">${bullet(t.L.key)}<div><div class="ttl">${t.L.name}</div>${sub?`<div class="sub">${esc(sub)}</div>`:""}</div>`
   +`<button class="x" aria-label="Close train details">×</button></div>`
   +`<div class="dest"><b>${headline}</b></div>`
   +`<div class="rows">${nowRow}${upRows?"":nextRow}</div>${upRows}`
   +`<div class="ft">${foot}<button class="fl" aria-pressed="${riding(t)||(reduceMotion()&&following===t)}" title="Ride along behind this train">${riding(t)||(reduceMotion()&&following===t)?"Following":"Follow"}</button></div>`;
  const ups=card.querySelector(".ups");if(ups&&scroll)ups.scrollTop=scroll;
  card.querySelector(".x").onclick=closeCard;
  card.querySelector(".fl").onclick=()=>{if(riding(t))endChase(performance.now(),false);else if(reduceMotion()&&following===t){following=null;renderCard()}else rideAlong(t)};
}
