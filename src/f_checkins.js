// the voice clips are named after the words they say: "Howard" -> howard, "95th/Dan Ryan" -> 95th_dan_ryan
const vslug=s=>String(s||"").toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"");
// what the check-in can honestly say about this train, from the same data as its card
function ciFacts(t){
  const r=t.L.routes[t.ri],s=t.lastObsS,n=r.st.length,near=Math.round(s),atStn=Math.abs(s-near)<0.12,v=t.cta||{};
  const lo=Math.floor(s),hi=Math.min(n-1,Math.ceil(s));
  const last=t.dirSign>0?stationAt(t,atStn?near:lo):stationAt(t,atStn?near:hi);
  const nx=v.next_sta_id&&STN.has(v.next_sta_id)&&STN.get(v.next_sta_id)!==last?{id:v.next_sta_id,tm:v.arrives_at?v.arrives_at/1000:0}:null;
  return{t,last,atStn,next:nx,dest:v.dest||"",delayed:!!v.delayed}}
// each sentence: [[pack,key],...] pieces plus the caption text
function ciLines(kind,f){
  const M=VO.man,L=[],nowSec=serverNow()/1000,lk=f.t.L.key,nm=id=>{const r=STN.get(id);return r?stnName(r):""};
  const tail=tm=>{if(!tm)return["t_up","coming up."];const m=Math.round((tm-nowSec)/60);
    return m<=0?["t_now","coming up now."]:m===1?["t_1","in about a minute."]:m<=90?["t_"+m,`in about ${m} minutes.`]:["t_up","coming up."]};
  const stop=(pre,word,p)=>{if(!p||!p.id||!STN.get(p.id))return;const[k,tx]=tail(p.tm);
    L.push({p:[[lk,pre+"_"+vslug(nm(p.id))],["core",k]],tx:`${word} ${nm(p.id)}, ${tx}`})};
  if(kind==="start"){
    const v=Math.random()<.5?0:1;
    L.push({p:[["core",`op_${lk}_${v}`]],tx:`${v?"Let's ride along with":"Checking in on"} a ${f.t.L.name} train.`});
    if(f.dest)L.push({p:[[lk,"to_"+vslug(shortName(f.dest))]],tx:`It's headed to ${shortName(f.dest)}.`});
    if(f.delayed)L.push({p:[["core","s_dly"]],tx:"CTA says it's running with a delay."});
    stop("nx","Next up,",f.next);
  }else if(kind==="mid"){
    if(f.last&&STN.get(f.last.id))L.push(f.atStn?{p:[[lk,"at_"+vslug(nm(f.last.id))]],tx:`Now at ${nm(f.last.id)}.`}
      :{p:[[lk,"ps_"+vslug(nm(f.last.id))]],tx:`Just passed ${nm(f.last.id)}.`});
    stop("nx","Next up,",f.next);
  }else{const v=Math.floor(Math.random()*3);
    L.push({p:[["core","end_"+v]],tx:["That's the check-in. Back out to the full map.","That's all for this one. Back to the whole system.","Okay, that wraps it up. Back out to the map."][v]})}
  // a sentence whose clip wasn't recorded (a destination CTA names some new way) is left out, not the whole check-in
  return M?L.filter(l=>l.p.every(([pk,k])=>pk==="core"?M.core&&M.core[k]:M.lines&&M.lines[pk]&&M.lines[pk][k])):L}
