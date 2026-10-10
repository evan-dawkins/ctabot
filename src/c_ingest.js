function trainNo(x){x=String(x??"").trim();return/^\d{1,5}$/.test(x)?x:""}
function runLabel(v){if(v.sim)return{sim:true,no:String(v.run)};return{no:trainNo(v.run)}}
// CTA says which station each train is heading to next. On its route that gives the direction from the very
// first fix (s counts stations along the route): toward a higher index = +1, lower = -1.
function nextDir(r,s,nextId){if(!nextId)return 0;let best=null;
  r.ids.forEach((id,k)=>{if(id===nextId&&(best==null||Math.abs(k-s)<Math.abs(best-s)))best=k});
  if(best==null||Math.abs(best-s)>3)return 0;
  return best>s+.02?1:best<s-.02?-1:0}
function ingest(data){
  const ml=data.lines||{};const seenAll=new Set();let bad=0;
  for(const key of ORDER){const L=LINES[key],vs=Array.isArray(ml[L.api])?ml[L.api]:[];
    for(const v of vs){
      if(!v||v.run==null||v.run===""){bad++;continue}
      const id=key+":"+v.run;if(seenAll.has(id))continue;                  // run numbers are unique within a line
      const lat=+v.lat,lon=+v.lon;
      if(!isFinite(lat)||!isFinite(lon)||lat===0||lon===0){bad++;continue}
      let fix=+v.predicted_at;fix=isFinite(fix)&&fix>0?(fix<1e12?fix*1000:fix):serverNow();
      let t=live.get(id);
      const loc=locate(L,lat,lon,t?t.ri:null,v.next_sta_id,t?t.lastObsS:null);
      if(!loc){bad++;continue}                                              // fix isn't on this line (yard, bad data)
      seenAll.add(id);
      const hint=nextDir(L.routes[loc.ri],loc.s,v.next_sta_id);
      const now=performance.now();
      if(!t){
        const vis=makeTrainVisual(L),p=poseAt(L.routes[loc.ri],loc.s);
        if(!reduceMotion()){for(const q of[vis.g,vis.trail.g])q.classList.add("born","grow");
          requestAnimationFrame(()=>requestAnimationFrame(()=>{for(const q of[vis.g,vis.trail.g])q.classList.remove("born");
            setTimeout(()=>{for(const q of[vis.g,vis.trail.g])q.classList.remove("grow")},700)}))}
        t={id,L,ri:loc.ri,segFrom:loc.s,segTo:loc.s,segT0:now,segDur:1,lastObsS:loc.s,dirSign:hint,
           updated:fix,lastSeen:Date.now(),stale:false,shown:[p.x,p.y],ang:0,a11y:"",...vis};
        t.run=runLabel(v);t.cta=v;
        bindTrain(t);applyTrainClass(t);trains.push(t);live.set(id,t);
      }else{
        t.run=runLabel(v);t.cta=v;t.lastSeen=Date.now();
        const moved=Math.abs(loc.s-t.lastObsS)>0.02||loc.ri!==t.ri;
        // CTA now and then puts a train a few hundred metres back, then forward again (1-3% of moves, measured
        // Oct 2026; often after placing it at its next station early). A train goes backwards on the map only if CTA
        // keeps saying so for 3 reports in a row (about a minute and a half), or turns it around.
        const exp=hint||t.dirSign;
        if(moved&&loc.ri===t.ri&&exp&&(loc.s-t.lastObsS)*exp<-0.08){t.backN=(t.backN||0)+1;if(t.backN<3)continue}
        t.backN=0;
        if(fix>t.updated||moved){
          const gap=fix>t.updated?Math.max(5000,Math.min(75000,fix-t.updated)):POLL;
          const cs=curS(t,now);
          if(loc.ri===t.ri){
            const dl=loc.s-t.lastObsS;if(Math.abs(dl)>0.03)t.dirSign=dl<0?-1:1;
            // a jump of more than a few stations isn't a train moving along the line (e.g. finishing a lap of the
            // Loop and heading back out): place it there, don't draw a path we don't know
            t.segFrom=Math.abs(loc.s-cs)>4?loc.s:cs;
          }else{
            // branch change: positions are comparable only while one of them is on the shared stretch
            const P=sharedPrefix(L,t.ri,loc.ri);
            if(Math.min(t.lastObsS,loc.s)<=P){const dl=loc.s-t.lastObsS;if(Math.abs(dl)>0.03)t.dirSign=dl<0?-1:1}else t.dirSign=0;
            t.segFrom=cs<=P?cs:loc.s;t.ri=loc.ri;
          }
          t.lastObsS=loc.s;t.segTo=loc.s;t.segT0=now;t.segDur=gap;t.updated=fix;
          if(moved)pingTrain(t);
        }
        if(hint)t.dirSign=hint;                                             // CTA's own next station settles the direction
      }
    }
  }
  for(const t of[...trains])if(!seenAll.has(t.id)&&Date.now()-t.lastSeen>DROP_AFTER)removeTrain(t,true);
  return bad}
async function poll(){
  clearTimeout(pollTimer);
  if(inflight)return;
  if(document.hidden&&mode==="live"){nextPollAt=Date.now()+POLL;pollTimer=setTimeout(poll,POLL);return}   // tab in the background: don't ask (it catches up the moment you look)
  inflight=true;refreshStatus();const pollT0=performance.now();
  const ac=new AbortController(),to=setTimeout(()=>ac.abort(),FETCH_TIMEOUT);
  try{
    const resp=await fetch(WORKER_URL+"/cta/positions",{cache:"no-store",signal:ac.signal});
    let data=null;try{data=await resp.json()}catch(_){}
    if(!data||typeof data!=="object")throw new Error(resp.ok?"The feed relay sent something unreadable":"The feed relay answered with an error ("+resp.status+")");
    if(data.error)throw new Error("CTA's feed returned an error: "+data.error);
    if(!resp.ok)throw new Error("The feed relay answered with an error ("+resp.status+")");
    let fa=+data.fetched_at;if(isFinite(fa)&&fa>0){if(fa<1e12)fa*=1000;clockOffset=Date.now()-fa;lastFeedAt=fa}else{clockOffset=0;lastFeedAt=Date.now()}
    if(mode==="sim"){liveBack=true}                 // live works again: offer to switch, don't mix it with simulated trains
    else{ingest(data);everLoaded=true}
    sonarPing();
    if(fails&&alertsErr)pollAlerts();                // the relay is back: fetch alerts now instead of in up to 2 minutes
    fails=0;lastOkAt=Date.now();lastError="";
  }catch(e){fails++;lastError=e&&e.name==="AbortError"?"The feed took too long to answer":(e&&e.message)||"Network error"}
  finally{clearTimeout(to);inflight=false;radarLanded(pollT0);const wait=fails?Math.min(POLL,10000*fails):POLL;   // after a miss, try again sooner
    nextPollAt=Date.now()+wait;pollTimer=setTimeout(poll,wait);refreshStatus()}
}
// service alerts come from CTA's Customer Alerts feed (through the Worker), checked every 2 minutes
let alertTimer=0,alertsAt=0;
async function pollAlerts(){clearTimeout(alertTimer);
  if(document.hidden){alertTimer=setTimeout(pollAlerts,120000);return}
  alertsAt=Date.now();
  try{const r=await fetch(WORKER_URL+"/cta/alerts",{cache:"no-store"});let d=null;try{d=await r.json()}catch(_){}
    if(d&&Array.isArray(d.alerts))takeAlerts({alerts:d.alerts});else takeAlerts({alerts_error:(d&&d.error)||"No answer"})}
  catch(e){takeAlerts({alerts_error:(e&&e.message)||"Network error"})}
  alertTimer=setTimeout(pollAlerts,120000)}
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&Date.now()-alertsAt>120000)pollAlerts()});
