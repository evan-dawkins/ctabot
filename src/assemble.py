"""Builds ctabot/index.html from MetraBot's index.html: MetraBot's engine, CTA's data and wording."""
import os, re, sys
F = os.path.dirname(os.path.abspath(__file__))
# the engine: a pinned copy of MetraBot's index.html (see src/README.md for how to update it)
src = open(os.path.join(F, "engine.html")).read().split("\n")
blk = lambda n: open(os.path.join(F, n)).read().rstrip("\n")
L = lambda a, b: "\n".join(src[a - 1:b])            # 1-indexed inclusive line range of MetraBot's page

def rep(s, old, new, count=1):
    n = s.count(old)
    if n != count:
        sys.exit(f"expected {count} match(es), found {n}: {old[:90]!r}")
    return s.replace(old, new)

# sanity: the line numbers below are for this exact MetraBot version
assert src[664].startswith("<script>") and "NETWORK DATA" in src[674] and "BASE MAP" in src[873] and "CAMERA" in src[963], "MetraBot changed"
assert "TRAINS" in src[1435] and "SERVICE ALERTS" in src[1599] and "STATION TIMES" in src[1840] and "FAVORITE STATIONS" in src[1964]
assert "TRAIN OF THE MOMENT" in src[2233] and "TRAIN CHECK-INS" in src[2320] and "MAIN LOOP" in src[2406]

# ---------------------------------------------------------------- head, styles, page markup
head = L(1, 664)
head = re.sub(r'<link rel="apple-touch-icon"[^\n]*\n', "", head)
import base64, urllib.parse
_svg = open(os.path.join(F, "icon.svg")).read().strip()
_png = base64.b64encode(open(os.path.join(F, "icon180.png"), "rb").read()).decode()
head = re.sub(r'<link rel="icon"[^\n]*>', lambda m: '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,' + urllib.parse.quote(_svg, safe=" =:/\"") .replace('"', "%22") + '">\n<link rel="apple-touch-icon" href="data:image/png;base64,' + _png + '">', head, count=1)
head = rep(head, "<title>MetraBot</title>", "<title>CTABot</title>")
head = rep(head, 'content="MetraBot"', 'content="CTABot"')
# colours: towns, city, street grid (CTA's map: city light, suburbs darker)
head = rep(head, "  --term:#22384A;\n", "  --term:#22384A;\n  --city:#1E3242;--town:#162634;--townedge:#2B4356;--grid:rgba(150,180,205,.07);\n")
head = rep(head, "  --term:#FFFFFF;\n", "  --term:#FFFFFF;\n  --city:#F7F9FB;--town:#DCE3E9;--townedge:#C3CED8;--grid:rgba(40,62,84,.07);\n")
head = rep(head, ".dim{opacity:.13}", ".dim{opacity:.07}")          # focus a line: the others nearly vanish (solo)
head = rep(head, "/* ---------- map ---------- */", "/* ---------- map ---------- */\n"
           ".city{fill:var(--city)}\n.town{fill:var(--town);stroke:var(--townedge);stroke-width:1;vector-effect:non-scaling-stroke}\n"
           ".grid{fill:none;stroke:var(--grid);stroke-width:1;vector-effect:non-scaling-stroke}")
head = rep(head, 'aria-label="Schematic map of Metra commuter rail with live train positions"', 'aria-label="Map of the CTA L with live train positions"')
head = rep(head, '<div class="mark"><b>MetraBot</b><span><i class="slogan">The way to really fly</i> · Unofficial Chicagoland live map</span>',
           '<div class="mark"><b>CTABot</b><span><i class="slogan">Enjoy the ride</i> · Unofficial Chicago L live map</span>')
head = re.sub(r'\s*<button id="rcBtn"[^\n]*</button>', "", head)
head = re.sub(r'<section id="rcard"[^\n]*</section>\n', "", head)
head = rep(head, 'title="Metra service alerts"', 'title="CTA service alerts"')
head = rep(head, "Every Metra train, right now", "Every L train, right now")
head = rep(head, "A live map of Metra trains around Chicago. Leave it on like a fish tank and watch them go.",
           "A live map of CTA &lsquo;L&rsquo; trains around Chicago. Leave it on like a fish tank and watch them go.")
head = re.sub(r'\s*<li><span class="ic" style="--c:#93C94F">.*?Check the report card.*?</li>', "", head)
for a, b in (("#3FAE5A", "#C60C30"), ("#F2BE2E", "#00A1DE"), ("#EE87AE", "#E27EA6")):   # intro art in L colours
    head = head.replace(a, b)
head = rep(head, "<small>See the next trains. Tap ☆ to save it.</small>", "<small>See the next arrivals. Tap ☆ to save it.</small>")
# ---- lake: reads as water, like CTA's map (deeper blue at night, poster blue by day)
head = rep(head, "  --lake:#050C14;\n", "  --lake:#0F2B45;\n")
head = rep(head, "  --lakelbl:#2A4A62;\n", "  --lakelbl:#3F77A0;\n")
head = rep(head, "  --lake:#B9D1E4;\n", "  --lake:#BCDCF1;\n")
head = rep(head, "  --lakelbl:#7E9DB5;\n", "  --lakelbl:#3E86BD;\n")
head = rep(head, ".lakelbl{font-family:var(--sans);font-size:26px;font-weight:500;fill:var(--lakelbl);letter-spacing:.3em}",
           ".lakelbl{font-family:var(--sans);font-size:30px;font-weight:600;fill:var(--lakelbl);letter-spacing:.42em}")
# ---- lines that share track: a hairline gap so colours never bleed together; trails stay inside their own line
head = rep(head, ".trail .tband{stroke-width:calc(var(--tw) + 10px)}", ".trail .tband{display:none}")
head = rep(head, ".trail .tcore{stroke-width:2.8px}", ".trail .tcore{stroke-width:1.5px}")
head = rep(head, ':root[data-theme="light"] .trail .tcore{stroke-width:2.4px}', ':root[data-theme="light"] .trail .tcore{stroke-width:1.4px}')
head = rep(head, ".train .glow{opacity:.15}", ".train .glow{opacity:0}")
head = rep(head, ".city{fill:var(--city)}", ".city{fill:var(--city)}\n.track.case{stroke:var(--city);stroke-width:calc(var(--tw) + 1.6px)}")
# ---- not affiliated, in the welcome guide
head = rep(head, "  </ul>\n  <div class=\"foot\">", "  </ul>\n  <p class=\"sib\">Like this? Try <a href=\"https://evan-dawkins.github.io/metrabot/\">MetraBot</a>, the same kind of live map for Metra commuter rail.</p>\n  <p class=\"nota\">Not affiliated with the Chicago Transit Authority (CTA). Train positions and arrival times come from CTA's public Train Tracker data.</p>\n  <div class=\"foot\">")
head = rep(head, "#card .ft .wn{color:var(--warn)}", "#card .ft .wn{color:var(--warn)}\n#card .ups{border-top:1px solid var(--edge);padding:7px 12px 8px;display:grid;gap:5px;max-height:214px;overflow-y:auto;overscroll-behavior:contain}\n#card .ups .uh{margin-bottom:1px}\n#card .ups .row{grid-template-columns:66px 1fr auto;gap:6px}\n#card .ups .row .v{white-space:normal;overflow-wrap:anywhere;line-height:1.2}\n#card .ups .row.pred{opacity:.55}")
head = rep(head, "#intro .foot{display:flex;", "#intro .nota{font-size:12.5px;line-height:1.4;color:var(--muted);margin:0 0 12px}\n#intro .foot{display:flex;")
if "Metra" in head.replace("MetraBot", "").replace("for Metra commuter rail", ""):   # (the link to MetraBot names it on purpose)
    sys.exit("Metra wording left in the page markup: " + re.search(r".{40}Metra.{40}", head).group(0))

# ---------------------------------------------------------------- script
camera_etc = L(963, 1247)
camera_etc = rep(camera_etc, "function maxW(){return FIT_W*1.35} const MIN_W=95;", "function maxW(){return FIT_W*1.12} const MIN_W=10;   // fully in: the Loop fills the screen")
camera_etc = rep(camera_etc, 'else if(focusKey)setFocus(null);else if(rcard.classList.contains("on"))closeReport()}', "else if(focusKey)setFocus(null)}")
camera_etc = re.sub(r"// settings were saved as metraLive\.\* before the rename to MetraBot: carry them over once\ntry\{.*?\n", "", camera_etc)
camera_etc = rep(camera_etc, """const RADAR_C=(()=>{const at=id=>{const r=STN.get(id);if(!r||!r.inst.length)return null;let x=0,y=0;for(const q of r.inst){x+=q.xy[0];y+=q.xy[1]}return[x/r.inst.length,y/r.inst.length]};
  const u=at("Union Station"),m=at("Millennium"),l=at("LaSalle St");if(!u||!m||!l)return null;
  return[(u[0]+m[0])/2,l[1]-.25*(l[1]-u[1])]})();   // the open area between Union and Millennium, just north of LaSalle St""",
  """const RADAR_C=geo(41.8818,-87.6298);   // the middle of the Loop""")
camera_etc = rep(camera_etc, "if(RADAR_C){let m=0;for(const r of STN.values())for(const q of r.inst)m=Math.max(m,Math.hypot(q.xy[0]-RADAR_C[0],q.xy[1]-RADAR_C[1]));RADAR_R=Math.ceil(m*2.6)}   // reaches past every edge of the page",
  "if(RADAR_C)RADAR_R=Math.ceil(Math.hypot(Math.max(RADAR_C[0],WORLD.x1-RADAR_C[0]),Math.max(RADAR_C[1],WORLD.y1-RADAR_C[1]))*1.6);   // reaches past every edge of the page")
camera_etc = rep(camera_etc, "Sonar shows a radar over the Loop", "Sonar shows a radar over the Loop")

labels = L(1248, 1383)
labels = rep(labels, 'for(const r of STATIONS){const alt=r.full.match(/\\((.*)\\)$/);r.alt=primCount[r.label]>1&&alt&&!TERMINALS[r.id]?alt[1]:""}',
             "for(const r of STATIONS)r.alt=\"\";   // same-named stations (Western, Damen, ...) are told apart by their line colours, as on CTA's map")
labels = rep(labels, 'const SHORT={"LaSalle St":"LaSalle"};', "const SHORT={};")
labels = rep(labels, """  for(const q of STATE_LBL){q.t.style.visibility="";const r=q.t.getBoundingClientRect();
    q.t.style.visibility=lb.some(b=>b.left<r.right&&b.right>r.left&&b.top<r.bottom&&b.bottom>r.top)?"hidden":""}}""",
"""  for(const q of STATE_LBL){q.t.style.visibility="";const r=q.t.getBoundingClientRect();   // town names: never on a station name or each other
    const hide=lb.some(b=>b.left<r.right+6&&b.right+6>r.left&&b.top<r.bottom&&b.bottom>r.top);q.t.style.visibility=hide?"hidden":"";if(!hide)lb.push(r)}}""")
labels = rep(labels, 'for(const q of[$("card"),$("notice"),$("spop"),$("board"),$("fstrip"),$("rcard")])', 'for(const q of[$("card"),$("notice"),$("spop"),$("board"),$("fstrip")])')

focus = L(1384, 1434)
focus = rep(focus, "const pad=60;return{x0:x0-pad,y0:y0-pad,x1:x1+pad+50,y1:y1+pad}", "const pad=15;return{x0:x0-pad,y0:y0-pad,x1:x1+pad+15,y1:y1+pad}")
focus = rep(focus, 'allChip.title="Show all lines and fold this bar";', 'allChip.title="Show all lines and fold this bar";')
focus = rep(focus, "b.className=\"chip\";b.setAttribute(\"aria-pressed\",\"false\");b.title=`Focus the ${L.name} line`;",
            "b.className=\"chip\";b.setAttribute(\"aria-pressed\",\"false\");b.title=`Show only the ${L.name}`;")
focus = rep(focus, '$("focusnote").innerHTML=key?`Showing <b>${LINES[key].name}</b> only`:"";', '$("focusnote").innerHTML=key?`Showing the <b>${LINES[key].name}</b> only`:"";')

trains_s = L(1435, 1524)
trains_s = rep(trains_s, "const POLL=30000,STALE_AFTER=95000,", "const POLL=30000,STALE_AFTER=150000,")
# ---- stops at stations: L trains stop at every station on their route. When the glide from one CTA report to the
#      next passes a station, the train eases in, waits (up to 20 s, only as long as the gap allows at a believable
#      speed) and eases out, and still reaches CTA's reported spot when the glide ends. Positions stay CTA's own.
trains_s = rep(trains_s, "function curS(t,now){const k=Math.max(0,Math.min(1,(now-t.segT0)/t.segDur));return t.segFrom+(t.segTo-t.segFrom)*k}",
"""const DWELL=20000,VAVG=0.5,DWELL_MIN=3000;   // ms at a stop; top average speed between stops (map units/s, ~15 m/s); shortest stop worth showing
const easeIn=u=>u*u*(2-u),easeOut=u=>1-(1-u)*(1-u)*(1+u),easeBoth=u=>u*u*(3-2*u);
function trackD(r,s){const n=r.ds.length,c=Math.max(0,Math.min(n-1,s)),i=Math.min(n-2,Math.floor(c));return r.ds[i]+(r.ds[i+1]-r.ds[i])*(c-i)}
function glidePlan(t){
  const key=t.segFrom+","+t.segTo+","+t.segT0+","+t.segDur+","+t.ri;if(t.planKey===key)return t.plan;t.planKey=key;
  const a=t.segFrom,b=t.segTo,r=t.L.routes[t.ri],dir=b>a?1:-1,isStn=s=>Math.abs(s-Math.round(s))<.02;
  let stops=[];
  if(Math.abs(b-a)>1e-3)for(let k=dir>0?Math.floor(a+.02)+1:Math.ceil(a-.02)-1;dir>0?k<b-.02:k>b+.02;k+=dir)stops.push(k);   // stations strictly between
  const dist=Math.abs(trackD(r,b)-trackD(r,a)),spare=Math.max(0,t.segDur-dist/VAVG*1000);
  let end=isStn(b)&&Math.abs(b-a)>.02;                                  // CTA puts it at a station: it gets there, then waits
  const nS=stops.length+(end?1:0);let dw=nS?Math.min(DWELL,spare/nS):0;
  if(dw<DWELL_MIN){dw=0;stops=[];end=false}                             // no time to stop: it flows through
  const pts=[a,...stops,b],moveT=t.segDur-dw*(stops.length+(end?1:0)),legs=[];let tt=0;
  for(let i=1;i<pts.length;i++){const p0=pts[i-1],p1=pts[i],len=Math.abs(trackD(r,p1)-trackD(r,p0));
    const st0=i>1||isStn(p0),st1=i<pts.length-1||isStn(p1),dur=dist>0?moveT*len/dist:moveT/(pts.length-1);
    legs.push({s0:p0,s1:p1,t0:tt,dur,f:st0&&st1?easeBoth:st0?easeIn:st1?easeOut:u=>u});tt+=dur;
    if(i<pts.length-1||end){legs.push({s0:p1,s1:p1,t0:tt,dur:dw,stop:true});tt+=dw}}
  return t.plan=legs}
function curS(t,now){const e=now-t.segT0;t.dwell=false;
  if(e>=t.segDur||Math.abs(t.segTo-t.segFrom)<1e-4)return t.segTo;if(e<=0)return t.segFrom;
  for(const l of glidePlan(t)){if(e<l.t0+l.dur||l===t.plan[t.plan.length-1]){if(l.stop){t.dwell=true;return l.s0}
      const u=l.dur>0?Math.max(0,Math.min(1,(e-l.t0)/l.dur)):1;return l.s0+(l.s1-l.s0)*l.f(u)}}
  return t.segTo}""")
# ---- CTA positions aren't GPS: they come from the signal system (measured Oct 2026: within ~2 m of the real track,
#      each train refreshed about every 30 s). Trains are matched on the real track shape, and CTA's "next station"
#      picks the right pass where a line runs over the same track twice (the Loop), instead of MetraBot's
#      straight lines between stations (which put 0.4% of Loop-line trains 3-5 km away).
trains_s = rep(trains_s, """   TRAINS — real GPS fixes decide WHERE; interpolation only decides HOW
   the marker gets there.""", """   TRAINS — real reported positions decide WHERE (CTA's come from its signal system, not GPS);
   interpolation only decides HOW the marker gets there.""")
trains_s = rep(trains_s, """function locate(L,lat,lon,prefRi){
  const g=geo(lat,lon);let best=null;const per=[];
  L.routes.forEach((r,ri)=>{const P=r.geoPts;let b=null;
    for(let i=1;i<P.length;i++){const a=P[i-1],c=P[i],dx=c[0]-a[0],dy=c[1]-a[1],l2=dx*dx+dy*dy||1;
      let t=((g[0]-a[0])*dx+(g[1]-a[1])*dy)/l2;t=Math.max(0,Math.min(1,t));
      const d=(a[0]+dx*t-g[0])**2+(a[1]+dy*t-g[1])**2;if(!b||d<b.d)b={d,ri,s:(i-1)+t}}
    per[ri]=b;if(!best||b.d<best.d)best=b});
  if(!best||best.d>MAX_MATCH_D2)return null;
  // stay on the branch we already know unless the fix clearly belongs to another one
  if(prefRi!=null&&per[prefRi]&&per[prefRi].d<=best.d+1.5)best=per[prefRi];
  return best}""", """// distance along a route's track -> station index (2.5 = halfway between its 3rd and 4th stations)
function sAtD(r,d){const ds=r.ds,n=ds.length;if(d<=ds[0])return 0;if(d>=ds[n-1])return n-1;
  let i=1;while(i<n-1&&ds[i]<d)i++;return(i-1)+(d-ds[i-1])/((ds[i]-ds[i-1])||1)}
/* Where a reported position sits on its line: on the real track. Where the same spot is on the route more
   than once (the track into the Loop, a terminal loop), CTA's next station picks the pass: the one whose next
   stop it is. Without one: the branch and place we already know. */
function locate(L,lat,lon,prefRi,nextId,prevS){
  const g=geo(lat,lon);let best=null;
  L.routes.forEach((r,ri)=>{const A=r.anc,c=r.ac,pr=[];let mn=Infinity;
    for(let i=1;i<A.length;i++){const a=A[i-1],b=A[i],dx=b[0]-a[0],dy=b[1]-a[1],l2=dx*dx+dy*dy;
      const t=l2?Math.max(0,Math.min(1,((g[0]-a[0])*dx+(g[1]-a[1])*dy)/l2)):0;
      const d2=(a[0]+dx*t-g[0])**2+(a[1]+dy*t-g[1])**2;pr.push([d2,c[i-1]+t*(c[i]-c[i-1])]);if(d2<mn)mn=d2}
    const lim=(Math.sqrt(mn)+.6)**2,occ=[];                          // within ~20 m of the closest: the same physical spot
    if(nextId)r.ids.forEach((id,k)=>{if(id===nextId)occ.push(r.ds[k])});
    for(const[d2,d]of pr){if(d2>lim)continue;const s=sAtD(r,d);
      let score=Math.sqrt(d2)*3+(ri===prefRi?0:1.5);
      if(occ.length)score+=Math.min(...occ.map(x=>Math.abs(x-d)));
      else score+=1e3+(prevS!=null&&ri===prefRi?Math.abs(s-prevS)*5:0);
      if(!best||score<best.score)best={score,d:d2,ri,s}}});
  if(!best||best.d>MAX_MATCH_D2)return null;
  return best}""")
trains_s = rep(trains_s, "\n".join(src[1472:1486]), blk("h_car.js"))   # the little trains: CTA 7000-series cars
trains_s = rep(trains_s, """function poseAt(r,s){const n=r.ds.length;s=Math.max(0,Math.min(n-1,s));
  const i=Math.min(n-2,Math.floor(s)),t=s-i,d=r.ds[i]+(r.ds[i+1]-r.ds[i])*t,p=along(r.anc,r.ac,d);
  const g=segAt(r.ac,d),a=r.anc[g],b=r.anc[g+1];
  return{x:p[0],y:p[1],d,ang:Math.atan2(b[1]-a[1],b[0]-a[0])}}""",
"""function poseAt(r,s){const n=r.ds.length;s=Math.max(0,Math.min(n-1,s));
  const i=Math.min(n-2,Math.floor(s)),t=s-i,d=r.ds[i]+(r.ds[i+1]-r.ds[i])*t,p=alongOff(r,d);   // on its own colour in a bundle
  return{x:p[0],y:p[1],d,ang:angAt(r,segAt(r.ac,d))}}""")
trains_s = rep(trains_s, """  const pts=[along(r.anc,r.ac,lo)];for(let i=1;i<r.ac.length-1;i++)if(r.ac[i]>lo&&r.ac[i]<hi)pts.push(r.anc[i]);
  pts.push(along(r.anc,r.ac,hi));return pts}""", """  const pts=[alongOff(r,lo)];for(let i=1;i<r.ac.length-1;i++)if(r.ac[i]>lo&&r.ac[i]<hi)pts.push(r.off[i]);
  pts.push(alongOff(r,hi));return pts}""")
trains_s = rep(trains_s, "  const tail=along(r.anc,r.ac,d0);", "  const tail=alongOff(r,d0);")
trains_s = rep(trains_s, "\nfunction trainNo(x){x=String(x??\"\").trim();return/^\\d{1,5}$/.test(x)?x:\"\"}", "")

alerts = L(1599, 1702)
alerts = rep(alerts, """   SERVICE ALERTS — straight from Metra's alerts feed via the Worker.
   Metra: an alert that's in the feed is active; one that's gone is over.""", """   SERVICE ALERTS — straight from CTA's Customer Alerts feed via the Worker (L lines and stations only).
   An alert that's in the feed is active; one that's gone is over.""")
alerts = rep(alerts, "const ROUTE_KEY={};for(const k of ORDER)ROUTE_KEY[LINES[k].routeId]=k;", "const ROUTE_KEY=API_KEY;")
alerts = rep(alerts, """      const keys=[...new Set((Array.isArray(a.routes)?a.routes:[]).map(r=>ROUTE_KEY[r]).filter(Boolean))];
      list.push({id,keys,header:String(a.header||"").trim(),desc:String(a.description||"").trim(),
        url:/^https:\\/\\//i.test(a.url||"")?a.url:"",effect:EFFECT[a.effect]||"",
        end:(Array.isArray(a.periods)?a.periods:[]).map(p=>+(p&&p.end)).filter(x=>x>0).sort((x,y)=>y-x)[0]||0})}""",
"""      const keys=[...new Set((Array.isArray(a.lines)?a.lines:[]).map(r=>ROUTE_KEY[r]).filter(Boolean))];
      const where=[...new Set((Array.isArray(a.stations)?a.stations:[]).map(s=>STN.get(String(s))).filter(Boolean).map(r=>r.label))].join(", ");
      list.push({id,keys,where,header:String(a.header||a.short||"").trim(),desc:String(a.description||a.short||"").trim(),
        url:/^https:\\/\\//i.test(a.url||"")?a.url:"",effect:String(a.impact||"").trim(),
        end:+a.end>0?Math.round(+a.end/1000):0})}""")
alerts = rep(alerts, '    const tags=[a.keys.length?a.keys.map(k=>LINES[k].code).join(", "):"All lines"];', '    const tags=[a.keys.length?a.keys.map(k=>LINES[k].code).join(", "):a.where||"All lines"];')
alerts = rep(alerts, "btn.title=n?`${n} Metra service alert${n>1?\"s\":\"\"}${focusKey?\" for \"+LINES[focusKey].code:\"\"}`:\"No active Metra service alerts\";",
             "btn.title=n?`${n} CTA service alert${n>1?\"s\":\"\"}${focusKey?\" for the \"+LINES[focusKey].name:\"\"}`:\"No active CTA service alerts\";")
alerts = rep(alerts, "Metra's alerts feed isn't answering right now.", "CTA's alerts feed isn't answering right now.")
alerts = rep(alerts, '>Details on metra.com</a>', '>Details on transitchicago.com</a>')
alerts = rep(alerts, """function startSim(){
  mode="sim";liveBack=false;document.body.classList.add("simmode");clearTrains();trips=null;""", """function startSim(){
  mode="sim";liveBack=false;document.body.classList.add("simmode");clearTrains();""")
alerts = rep(alerts, """function simTick(){
  const out={},t=Date.now()/1000;
  for(const q of simTrains){const r=LINES[q.key].routes[q.ri],last=r.st.length-1;
    q.s+=q.dir*q.v;if(q.s<=0){q.s=0;q.dir=1}else if(q.s>=last){q.s=last;q.dir=-1}
    const i=Math.min(last-1,Math.floor(q.s)),f=q.s-i,a=r.st[i],b=r.st[i+1];
    (out[LINES[q.key].routeId]||=[]).push({vehicle_id:"sim-"+q.run,label:q.run,sim:true,
      latitude:a[1]+(b[1]-a[1])*f,longitude:a[2]+(b[2]-a[2])*f,updated_at:t})}
  clockOffset=0;ingest({metra_lines:out});refreshStatus();
}""", """function simTick(){
  const out={},now=Date.now();
  for(const q of simTrains){const r=LINES[q.key].routes[q.ri],last=r.st.length-1;
    q.s+=q.dir*q.v;if(q.s<=0){q.s=0;q.dir=1}else if(q.s>=last){q.s=last;q.dir=-1}
    const i=Math.min(last-1,Math.floor(q.s)),f=q.s-i,a=STOPS[r.st[i]],b=STOPS[r.st[i+1]];
    (out[LINES[q.key].api]||=[]).push({run:q.run,sim:true,lat:a.lat+(b.lat-a.lat)*f,lon:a.lon+(b.lon-a.lon)*f,predicted_at:now,
      next_sta_id:q.dir>0?r.st[i+1]:r.st[i],dest:shortName(STOPS[q.dir>0?r.st[last]:r.st[0]].name)})}
  clockOffset=0;ingest({lines:out});refreshStatus();
}""")
# the alerts section ends where the train-moving code above starts; keep MetraBot's poll-free sim/visibility code

status = L(1703, 1787)
status = rep(status, 'notice(`No Metra trains are reporting right now. <span>Normal overnight. The map fills in when service starts.</span>`)',
             'notice(`No L trains are reporting right now. <span>Overnight only the Red and Blue Lines run. The map fills in as service starts.</span>`)')
status = rep(status, "notice(`Metra's feed is answering, but no train has reported a new position recently.`)", "notice(`CTA's feed is answering, but no train has reported a new position recently.`)")
status = rep(status, '+" Metra publishes new positions about every 30 seconds.";', '+" CTA publishes new positions about every 30 seconds.";')
status = rep(status, """function showTrainTip(t,e){
  const tr=tripFor(t),dest=tr&&tr.last_stop?destName(tr.last_stop):"";
  tip.innerHTML=`<div><span class="lc" style="background:${t.L.color}"></span>${t.L.code}${trainLabel(t)?" · "+trainLabel(t):""}${dest?" to "+esc(dest):""}</div>`
   +`<div class="s">${dirText(t)}${t.stale?" · position out of date":""}</div>`;placeTip(e)}
function trainLabel(t){return t.run.sim?"Simulated "+t.run.no:t.run.no?"Train "+t.run.no:""}""", """function showTrainTip(t,e){
  const v=t.cta||{},nx=v.next_sta_id&&STN.get(v.next_sta_id);
  tip.innerHTML=`<div><span class="lc" style="background:${t.L.color}"></span>${t.L.code}${trainLabel(t)?" · "+trainLabel(t):""}${v.dest?" to "+esc(v.dest):""}</div>`
   +`<div class="s">${nx?(v.approaching?"Arriving at ":"Next: ")+esc(nx.label):dirText(t)}${v.delayed?" · delayed":""}${t.stale?" · position out of date":""}</div>`;placeTip(e)}
function trainLabel(t){return t.run.sim?"Simulated "+t.run.no:t.run.no?"Run "+t.run.no:""}""")
status = rep(status, 'function dirText(t){return t.dirSign===0?"Direction not known yet":t.dirSign<0?"Inbound to Chicago":"Outbound from Chicago"}',
             'function dirText(t){const d=t.cta&&t.cta.dest;return d?"to "+d:t.dirSign===0?"Direction not known yet":"Direction known"}')
status = rep(status, "  const r=cw()/ch(),tw=vb.w>FIT_W*0.55?Math.max(MIN_W,vb.w/2):vb.w;    // zoom in a step only if we're far out",
             "  const r=cw()/ch(),tw=vb.w>FIT_W*0.2?Math.max(MIN_W,FIT_W/9):vb.w;    // zoom in to the neighbourhood only if we're far out")
card_place = L(1826, 1838)

fav = L(1964, 2000)
fav = rep(fav, "   Saved in this browser only (localStorage key metrabot.favorites).", "   Saved in this browser only (localStorage key ctabot.favorites).")
fav = rep(fav, "  spopRec=rec;spop.classList.add(\"on\");document.body.classList.add(\"pop\");renderStationPop();placeStationPop();labelsDirty=true}",
             "  spopRec=rec;spop.classList.add(\"on\");document.body.classList.add(\"pop\");renderStationPop();placeStationPop();labelsDirty=true;arrivalsTick()}")
fav = rep(fav, "  saveFav();boardSig=\"\";renderBoard();renderStationPop();refit()}", "  saveFav();boardSig=\"\";renderBoard();renderStationPop();refit();arrivalsTick()}")
fav = rep(fav, "const lines=ORDER.filter(k=>rec.lines.has(k)),on=isFav(rec.id),full=!on&&FAV.ids.length>=FAV_MAX;",
             "const lines=ORDER.filter(k=>rec.lines.has(k)),on=isFav(rec.id),full=!on&&FAV.ids.length>=FAV_MAX;   // CTA's full station name in the title")

board = L(2048, 2115)
board = rep(board, """function boardRows(rec){
  if(mode!=="sim"&&!everLoaded)return{msg:"Waiting for live data…"};
  if(mode!=="sim"&&!feedHealthy())return{msg:"Live feed not answering, so no times right now."};
  const term=DOWNTOWN.has(rec.id),d=dirRows(rec,term?3:2);return{src:d.src==="board"?"pred":d.src,html:dirSections(term,d)}}""",
"""function boardRows(rec){return arrivalSections(rec,2)}""")
board = rep(board, """  const foot=!favs.length?"":mode==="sim"?"Simulated trains, not real.":src==="pred"?"Times are Metra's live predictions. Faded line = train not reporting GPS yet."
    :src==="gps"?"No times in the feed right now. Based on live train positions.":"";""",
"""  const foot=!favs.length?"":mode==="sim"?"Simulated trains, not real.":src==="pred"?"Times are CTA's live predictions. Faded = scheduled, no train reporting for it yet.":"";""")
board = rep(board, """  if(++stripT>=8){stripT=0;stripIdx++}const rec=favs[stripIdx%favs.length],nowSec=serverNow()/1000;let info="";
  if(mode!=="sim"&&feedHealthy()&&trips){const b=DOWNTOWN.has(rec.id)&&departuresAt(rec,nowSec,1),p=b&&b.length?b[0]:predictionsAt(rec,nowSec).filter(x=>!(DOWNTOWN.has(rec.id)&&x.ends))[0];info=p?`<b>${minsTo(p.tm,nowSec)}</b> · ${LINES[p.key].code} ${p.ends?"arriving":"to "+esc(p.dest)}`:"No trains on the way"}
  else{const r=arrivalRows(rec,1);info=r.msg||r.html.replace(/<[^>]+>/g," ").replace(/\\s+/g," ").trim()}""",
"""  if(++stripT>=8){stripT=0;stripIdx++}const rec=favs[stripIdx%favs.length],a=upcoming(rec),nowMs=serverNow();let info="";
  if(mode==="sim")info="Arrival times show for live trains only";
  else if(!a)info="Getting arrival times…";else if(a.err)info="Arrival times aren't answering";
  else{const e=a.etas[0],k=e&&API_KEY[e.line];info=e&&k?`<b>${etaWhen(e,nowMs)}</b> · ${LINES[k].code} to ${esc(e.dest||"")}`:"No trains on the way"}""")

mood_tail = L(2207, 2231)
mood_tail = rep(mood_tail, 'if(sit){key="s:"+sit.key+(sit.line||"");lines=SIT[sit.key].map(x=>x.replaceAll("{L}",sit.line||""));moodSit=sit}',
                'if(sit){key="s:"+sit.key+(sit.line||"");lines=sit.lines||SIT[sit.key].map(x=>x.replaceAll("{L}",sit.line||""));moodSit=sit}')
chase_s = L(2233, 2319)
chase_s = rep(chase_s, "function rideVB(t){const W=cw(),H=ch(),w=Math.max(MIN_W*1.3,FIT_W/6),", "function rideVB(t){const W=cw(),H=ch(),w=Math.max(MIN_W*3,FIT_W/14),")
ci_head = L(2320, 2340)
ci_tail = L(2384, 2405)
main = L(2406, 2461)
main = rep(main, "  statusT-=dt;if(statusT<=0){statusT=1;refreshStatus();tickHeader();tickIdle();tickStrip();renderReport();tickMood()}",
           "  statusT-=dt;if(statusT<=0){statusT=1;refreshStatus();tickHeader();tickIdle();tickStrip();tickMood();arrivalsTick()}")
main = rep(main, "    const z=FIT_W/vb.w;document.documentElement.style.setProperty(\"--tw\",Math.max(2.4,Math.min(6.5,2.6+1.5*Math.log2(Math.max(1,z)))).toFixed(2)+\"px\");",
           "    document.documentElement.style.setProperty(\"--tw\",twPx().toFixed(2)+\"px\");")
main = rep(main, 'if(GEO_ISSUES.length)console.warn("Schematic ordering issues:",GEO_ISSUES);', 'if(GEO_ISSUES.length)console.warn("Map ordering issues:",GEO_ISSUES);')
main = re.sub(r"window\.__metra=\{.*?\};", "window.__cta={ciSay,ciFacts,ciLines,get VO(){return VO},setCheckins,get ciOn(){return ciOn},FAV,openStationPop,renderBoard,get introOpen(){return introOpen},get actx(){return actx},get sndOn(){return sndOn},get sndMode(){return sndMode},setSndMode,get RADAR_C(){return RADAR_C},tickMood:()=>{sitAt=0;tickMood()},get moodSit(){return moodSit},liveSituation,get chase(){return chase},startRide:()=>startRide(performance.now()),get ROT(){return ROT},takeAlerts,get alerts(){return alerts},startSim,stopSim,get mode(){return mode},poll,LINES,STN,STATIONS,GEO_ISSUES,layoutLabels,ingest,get trains(){return trains},get vb(){return vb},set vb(v){vb=v},renderLabels,setFocus,selectTrain,fitAll,ARR,arrivalsTick,get FIT_W(){return FIT_W},updateMarkers,closeCard,locate,sAtD,glidePlan,curS};", main, flags=re.S)
main = rep(main, "  const sNow=serverNow(),k=vb.w/cw();",
           "  const sNow=serverNow(),k=vb.w/cw();\n"
           "  // trains shrink when you zoom out (so the whole map isn't buried under them) and reach full size ~3 zoom steps in\n"
           "  const zf=Math.log2(Math.max(1,FIT_W/vb.w)),tsz=cuteTrains?Math.min(1,.6+.4*zf/3):Math.min(1,.75+.25*zf/3),ks=k*tsz;")
main = rep(main, "    const tf=`translate(${p.x.toFixed(2)},${p.y.toFixed(2)}) scale(${k.toFixed(4)})`;", "    const tf=`translate(${p.x.toFixed(2)},${p.y.toFixed(2)}) scale(${ks.toFixed(4)})`;")
main = rep(main, "applyStyle();tickHeader();poll();requestAnimationFrame(frame);", "applyStyle();tickHeader();poll();pollAlerts();requestAnimationFrame(frame);")

out = "\n".join([
    head,
    blk("a_network.js"), "",
    blk("b_basemap.js"), "",
    camera_etc, labels, focus,
    trains_s, blk("c_ingest.js"),
    "/* ---- simulated mode: only on request, always labelled, never mixed with live data ----",
    "   Fake trains are fed through the same pipeline as real reports (so they move the same way),",
    "   every 8 s, at a sped-up pace so there's something to watch. */",
    "let mode=\"live\",liveBack=false,simTimer=0,simTrains=[];",
    "function clearTrains(){closeCard();for(const t of[...trains])removeTrain(t,false)}",
    alerts, "",
    status, blk("g_card.js"), card_place, "",
    blk("d_times.js"), "",
    fav, board, blk("e_mood.js"), mood_tail, "", chase_s, ci_head, blk("f_checkins.js"), ci_tail, blk("i_ats.js"), blk("j_sat.js"), main])
# (leaving the tab mid-ride: the reset now comes from MetraBot itself)

# ================================================================ CTABot-only fixes (Oct 2026 audit)
# ---- touch: a finger that starts on a train can still drag or pinch the map; a tap still picks the train.
#      On a phone a tap covers a 22 px circle: one train in it is picked, several zoom in on them instead of guessing.
out = rep(out, 'svg.addEventListener("pointerdown",e=>{if(e.button!==0||e.target.closest(".train"))return;',
               'svg.addEventListener("pointerdown",e=>{if(e.button!==0)return;')
out = rep(out, 'if(ptrs.size===1)drag={x:e.clientX,y:e.clientY,vb:{...vb},moved:false,target:e.target}});',
               'if(ptrs.size===1)drag={x:e.clientX,y:e.clientY,vb:{...vb},moved:false,target:e.target,touch:e.pointerType!=="mouse"}});')
out = rep(out, 'if(!drag)return;const wasClick=!drag.moved,tgt=drag.target;drag=null;',
               'if(!drag)return;const wasClick=!drag.moved,tgt=drag.target,touchy=drag.touch;drag=null;')
out = rep(out, '  const g=tgt&&tgt.closest&&tgt.closest("g"),rec=g&&gRec.get(g);',
               '  if(tapPick(tgt,e,touchy))return;\n  const g=tgt&&tgt.closest&&tgt.closest("g"),rec=g&&gRec.get(g);')
out = rep(out, "svg.addEventListener(\"pointerup\",endDrag);",
  "let lastPick=0;\n"
  "function tapPick(tgt,e,touchy){\n"
  "  const R=touchy&&!rideCard()?22:0,x=e.clientX,y=e.clientY,own=tgt&&tgt.closest&&tgt.closest(\".train\"),ownT=own&&trains.find(t=>t.g===own);\n"
  "  const near=[];if(R)for(const t of trains){if(t.gone||t.g.classList.contains(\"dim\"))continue;const r=t.g.getBoundingClientRect();if(!r.width)continue;\n"
  "    const d=Math.hypot(r.x+r.width/2-x,r.y+r.height/2-y);if(d<=R)near.push([d,t])}\n"
  "  near.sort((a,b)=>a[0]-b[0]);\n"
  "  if(!ownT&&(!near.length||(tgt&&tgt.closest&&gRec.get(tgt.closest(\"g\")))))return false;   // a station right under the finger wins over a nearby train\n"
  "  lastPick=performance.now();\n"
  "  if(near.length>=2&&near[1][0]-near[0][0]<9&&vb.w>MIN_W*2.2&&!rideCard()){   // two trains equally under the finger: zoom in on them instead of guessing\n"
  "    const p=toWorld(x,y),nw=Math.max(MIN_W,vb.w/2.6),k=nw/vb.w;stopFollowing();\n"
  "    flyTo({x:p[0]-(p[0]-vb.x)*k,y:p[1]-(p[1]-vb.y)*k,w:nw,h:vb.h*k},380);return true}\n"
  "  const t=ownT||near[0][1];hideTip();if(selected===t){if(!rideCard())closeCard();return true}selectTrain(t);return true}\n"
  "svg.addEventListener(\"pointerup\",endDrag);")
out = rep(out, 't.g.addEventListener("click",e=>{e.stopPropagation();pick()});',
               't.g.addEventListener("click",e=>{e.stopPropagation();if(performance.now()-lastPick>500)pick()});   // the map already handled a real tap')
# bigger touch targets, same look
out = rep(out, "</style>",
  "@media (pointer:coarse){#helpBtn,.ibtn,#card .x,.fl{position:relative}\n"
  "  #helpBtn::after,.ibtn::after{content:\"\";position:absolute;inset:-8px -3px}\n"
  "  #card .x::after,#spop .x::after{content:\"\";position:absolute;inset:-11px}\n"
  "  .fl::after{content:\"\";position:absolute;inset:-10px -4px}}\n"
  "</style>")
# ---- during a ride: + and − zoom the ride itself, and \"show the whole network\" ends it (they did nothing before)
ride_on = '(chase&&(chase.phase==="in"||chase.phase==="ride"))'
out = rep(out, "w=Math.max(MIN_W*3,FIT_W/14)", "w=Math.max(MIN_W,Math.min(maxW(),Math.max(MIN_W*3,FIT_W/14)*(chase&&chase.zf||1)))")
out = rep(out, "function zoomBy(f){", f"function zoomBy(f){{if{ride_on}{{chase.zf=Math.max(.3,Math.min(6,(chase.zf||1)*f));return}}")
out = rep(out, "function zoomAround(f,mx,my){camAnim=null;", f"function zoomAround(f,mx,my){{if{ride_on}{{chase.zf=Math.max(.3,Math.min(6,(chase.zf||1)*f));return}}camAnim=null;")
out = rep(out, "const d=Math.hypot(a.x-b.x,a.y-b.y)||1,nw=Math.max(MIN_W,Math.min(maxW(),pinch.vb0.w*pinch.d0/d)),k=nw/pinch.vb0.w;",
               f"const d=Math.hypot(a.x-b.x,a.y-b.y)||1;if{ride_on}{{if(pinch.zf0==null)pinch.zf0=chase.zf||1;chase.zf=Math.max(.3,Math.min(6,pinch.zf0*pinch.d0/d));return}}\n"
               "    const nw=Math.max(MIN_W,Math.min(maxW(),pinch.vb0.w*pinch.d0/d)),k=nw/pinch.vb0.w;")
out = rep(out, "function resetView(){stopFollowing();flyTo(fitAll())}",
               f"function resetView(){{if{ride_on}{{chase.stop=true;endChase(performance.now(),false);return}}stopFollowing();flyTo(fitAll())}}")

# ---- keyboard and screen readers: the controls come first in tab order (the map used to put 50+ trains ahead
#      of them), stations can be reached and opened from the keyboard, and trains read naturally
_stage = '<div id="stage">\n  <svg id="map" role="group" aria-label="Map of the CTA L with live train positions"></svg>\n  <svg id="labels" aria-hidden="true"></svg>\n</div>\n<div id="horizon"></div>\n'
out = rep(out, _stage, "")
out = rep(out, '<div id="card"', _stage + '<div id="card"')
out = rep(out, "</style>", ".top,.console,.zoom{z-index:1}\n.sg:focus{outline:none}.sg:focus-visible .stnhit{fill:none;stroke:var(--ink);stroke-width:2px;vector-effect:non-scaling-stroke}\n</style>")
out = rep(out, 'rec.hit=el("rect",{class:"stnhit"},g);gRec.set(g,rec);',
               'rec.hit=el("rect",{class:"stnhit",rx:4},g);gRec.set(g,rec);\n'
               '  g.setAttribute("tabindex","0");g.setAttribute("role","button");\n'
               '  g.setAttribute("aria-label",`${rec.full} station, ${ORDER.filter(k=>rec.lines.has(k)).map(k=>LINES[k].name).join(", ")}. Press Enter for arrivals.`);\n'
               '  g.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();openStationPop(rec)}});')
out = rep(out, 'const a=`${t.L.name} line${trainLabel(t)?", "+trainLabel(t).toLowerCase():""}, ${dirText(t).toLowerCase()}',
               'const a=`${t.L.name} train${trainLabel(t)?", "+trainLabel(t).toLowerCase():""}, ${dirText(t)}')

# ---- times are Chicago time wherever you are (the ticker already was)
out = rep(out, 'const fmtClock=sec=>new Date(sec*1000).toLocaleTimeString([],{hour:"numeric",minute:"2-digit"});',
               'const fmtClock=sec=>new Date(sec*1000).toLocaleTimeString([],{hour:"numeric",minute:"2-digit",timeZone:"America/Chicago"});')
out = rep(out, '$("clock").textContent=now.toLocaleTimeString([],{hour:"numeric",minute:"2-digit",second:"2-digit"});',
               '$("clock").textContent=now.toLocaleTimeString([],{hour:"numeric",minute:"2-digit",second:"2-digit",timeZone:"America/Chicago"});$("clock").title="Chicago time";')
out = rep(out, 'same?d.toLocaleTimeString([],{hour:"numeric",minute:"2-digit"}):d.toLocaleDateString([],{month:"short",day:"numeric"})',
               'same?d.toLocaleTimeString([],{hour:"numeric",minute:"2-digit",timeZone:"America/Chicago"}):d.toLocaleDateString([],{month:"short",day:"numeric",timeZone:"America/Chicago"})')

# ---- readable colours: "Delayed" in light mode, and the green "Live"
out = rep(out, "</style>", ':root[data-theme="light"] .st.late{color:#9A5300}\n</style>')
out = rep(out, "--live:#1B8752;", "--live:#157346;")


# ---- the station card: "Add to your board" right under the name (it used to be below every arrival, off-screen on phones)
out = rep(out, '+stationSchedule(rec,3)\n    +`<button class="star" aria-pressed="${on}" ${full?"disabled":""}>${on?"★ On your board":"☆ Add to your board"}</button>`\n'
               '    +(full?`<div class="note">Your board holds ${FAV_MAX} stations. Remove one to add this.</div>`:on?`<div class="note">Click again to remove it.</div>`:"");',
               '+`<button class="star" aria-pressed="${on}" ${full?"disabled":""}>${on?"★ On your board":"☆ Add to your board"}</button>`\n'
               '    +(full?`<div class="note">Your board holds ${FAV_MAX} stations. Remove one to add this.</div>`:on?`<div class="note">Click again to remove it.</div>`:"")\n'
               '    +stationSchedule(rec,3);')
out = rep(out, "</style>", "@media (max-width:420px){#spop .arr .to,#board .arr .to{white-space:normal;overflow-wrap:anywhere;line-height:1.2}}\n</style>")

# ---- lake water: half as many glints, updated half as often (it was a quarter of the page's idle CPU)
out = rep(out, "steps(48)", "steps(24)")

# ---- link previews, and the browser bar follows the theme
out = rep(out, '<meta name="theme-color" content="#1B2C3A">',
  '<meta name="theme-color" content="#1B2C3A">\n'
  '<meta name="description" content="Unofficial live map of every CTA \'L\' train in Chicago. Enjoy the ride.">\n'
  '<meta property="og:title" content="CTABot">\n'
  '<meta property="og:description" content="Unofficial live map of every CTA \'L\' train in Chicago. Enjoy the ride.">\n'
  '<meta property="og:type" content="website">\n<meta property="og:url" content="https://evan-dawkins.github.io/ctabot/">')
out = rep(out, "function setTheme(t){\n  document.documentElement.dataset.theme=t;",
               "function setTheme(t){\n  document.documentElement.dataset.theme=t;{const m=document.querySelector('meta[name=\"theme-color\"]');if(m)m.content=t===\"light\"?\"#EEF2F5\":\"#1B2C3A\"}")
# ================================================================ O'Hare's Airport Transit System (src/i_ats.js)
# drawn and moved every frame (it shows only when you're zoomed in at the airport)
out = rep(out, "  const chasing=chaseFrame(now,dt);\n  applyVB();", "  const chasing=chaseFrame(now,dt);\n  applyVB();atsFrame();")
# taps: a direct hit on an ATS train or station first, then the L trains, then an ATS train near the finger
out = rep(out, "  if(tapPick(tgt,e,touchy))return;\n", "  if(atsTap(tgt,e,touchy,0)||tapPick(tgt,e,touchy)||atsTap(tgt,e,touchy,1))return;\n")
# its stations and trains open in the station card; clicking O'Hare zooms in on the airport
out = rep(out, 'renderStationPop();placeStationPop();labelsDirty=true;arrivalsTick()}', 'renderStationPop();placeStationPop();labelsDirty=true;arrivalsTick();atsOnStation(rec)}')
out = rep(out, "function renderStationPop(){const rec=spopRec;if(!rec)return;",
  "function renderStationPop(){const rec=spopRec;if(!rec)return;\n"
  "  if(rec.ats){const html=atsPopHTML(rec);if(html!==spopSig){spopSig=html;spop.innerHTML=html;labelsDirty=true;spop.querySelector(\".x\").onclick=closeStationPop}return}")
out = rep(out, "if(spopRec)want.add(spopRec.id);", "if(spopRec&&!spopRec.ats)want.add(spopRec.id);")
out = rep(out, "let x=px+18,y=py-24;if(x+w>W-12)x=px-18-w;", "let x=px+18,y=py-24;if(x+w>W-12)x=px-18-w;if(ATS&&spopRec.id===ATS.hub&&atsAlpha>.5)x=12;   // at the airport: out of the way, on the left")
out = rep(out, "</style>",
  ".ats{display:none}\n"
  ".atscase{fill:none;stroke:var(--city);stroke-width:5px;vector-effect:non-scaling-stroke;stroke-linejoin:round}\n"
  ".atstrk{fill:none;stroke-width:2.2px;vector-effect:non-scaling-stroke;stroke-linejoin:round}\n"
  ".atsdot{fill:var(--bg)}.atshit{fill:transparent;cursor:pointer}.atss,.atst{cursor:pointer}\n"
  ".atss:focus{outline:none}.atss:focus-visible .atsdot{stroke:var(--ink)}\n"
  ".atsl{font-family:var(--sans);font-weight:600;fill:var(--ink);paint-order:stroke;stroke:var(--bg);stroke-linejoin:round;pointer-events:none}\n"
  ".atsnum{font-family:var(--sans);font-weight:700;pointer-events:none}.atsbadge{pointer-events:none}\n"
  ".atsarrow{fill:var(--bg);stroke-width:1.8;stroke-linejoin:round}.atst.sel .atsarrow{fill:#FFD9D6}\n"
  ".atscar{display:none}body.cute .atscar{display:inline}body.cute .atsarrow{display:none}\n"
  "#spop .atsb{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;font-size:13px;font-weight:700;margin-right:7px;vertical-align:-2px}\n"
  "#spop .atssub{font-size:12.5px;color:var(--muted);align-self:center;margin-left:4px}\n"
  "#spop .atsnote{margin-top:10px}\n"
  "</style>")

# ---- train card: "Arriving" (the widest label) fits beside the station name in both lists
out = rep(out, "#card .row{display:grid;grid-template-columns:50px 1fr auto;gap:8px;align-items:baseline}",
               "#card .row{display:grid;grid-template-columns:66px 1fr auto;gap:8px;align-items:baseline}")

# the sister-site link folds into a chevron: open on hover (mouse) or tap (touch)
SIB_MARKUP = '  <span class="sibw" id="sibw"><button class="sibt" id="sibt" aria-expanded="false" aria-controls="sibl" title="Like this? Try MetraBot" aria-label="Show the link to MetraBot"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5 5.5 8l4.5 4.5"/></svg></button><a class="sib" id="sibl" href="https://evan-dawkins.github.io/metrabot/" title="MetraBot: the same live map for Metra commuter rail" tabindex="-1"><span class="lt">Like this?&nbsp;</span>Try MetraBot&nbsp;→</a></span><span class="sep"></span>\n'
SIB_CSS = '.zoom .sibw{display:flex;align-items:center}\n.zoom button.sibt{display:inline-flex;align-items:center;justify-content:center;min-width:26px;padding:0 5px;color:var(--muted)}\n.zoom button.sibt svg{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;transition:transform var(--t-base,.25s) ease}\n.zoom .sibw.open button.sibt svg{transform:rotate(180deg)}\n.zoom a.sib{display:flex;align-items:center;padding:0;max-width:0;opacity:0;visibility:hidden;overflow:hidden;border-radius:7px;font-size:13.5px;color:var(--muted);text-decoration:none;white-space:nowrap;\n  transition:max-width .35s ease,opacity .25s ease,padding .35s ease,visibility 0s linear .35s}\n.zoom .sibw.open a.sib{max-width:240px;opacity:1;visibility:visible;padding:0 8px;transition:max-width .35s ease,opacity .3s ease .05s,padding .35s ease,visibility 0s}\n.zoom a.sib:hover,.zoom a.sib:focus-visible{background:var(--hover);color:var(--ink)}\n@media (max-width:400px){.zoom a.sib .lt{display:none}}\n'
SIB_JS = '<script>\n/* "Like this? Try MetraBot" folds into a small chevron beside the zoom buttons.\n   Mouse: it slides open while you hover over it and folds away when you leave. Touch or keyboard: tap the chevron. */\n(function(){const w=document.getElementById("sibw"),b=document.getElementById("sibt"),a=document.getElementById("sibl");if(!w)return;\n  let t=0,hov=false;const set=o=>{clearTimeout(t);w.classList.toggle("open",o);b.setAttribute("aria-expanded",String(o));\n    b.setAttribute("aria-label",(o?"Hide":"Show")+" the link to MetraBot");a.tabIndex=o?0:-1};\n  w.addEventListener("pointerenter",e=>{if(e.pointerType==="mouse"){hov=true;set(true)}});\n  w.addEventListener("pointerleave",e=>{if(e.pointerType==="mouse"){hov=false;clearTimeout(t);t=setTimeout(()=>set(false),300)}});\n  w.addEventListener("focusout",e=>{if(!w.contains(e.relatedTarget))set(false)});\n  b.addEventListener("click",e=>{e.stopPropagation();if(!hov)set(!w.classList.contains("open"))});\n  set(false)})();\n</script>\n'
# ---- links to the sister map (MetraBot): beside the zoom buttons, and in the welcome guide
out = rep(out, '<div class="zoom">\n  <button id="zout"', '<div class="zoom">\n'+SIB_MARKUP+'  <button id="zout"')
_i = out.index(SIB_MARKUP); _j = out.index("</div>\n", _i) + len("</div>\n"); out = out[:_j] + SIB_JS + out[_j:]
out = rep(out, "</style>", SIB_CSS+
  "#intro .sib{font-size:14.5px;color:var(--muted);margin:0 0 14px}\n"
  "#intro .sib a{color:var(--ink);font-weight:700;text-decoration:none;border-bottom:1px solid var(--faint)}\n"
  "#intro .sib a:hover{border-bottom-color:var(--ink)}\n</style>")

# ---- satellite map (src/j_sat.js): a button by the title (S), the photo's credit, styles, and a per-frame update
_globe = ('<button id="satBtn" class="ibtn" aria-pressed="false" aria-label="Switch to the satellite map" title="Satellite map (S)">'
          '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6.6"/><path d="M3.4 10h13.2M10 3.4c2 2 2.9 4.2 2.9 6.6s-.9 4.6-2.9 6.6M10 3.4c-2 2-2.9 4.2-2.9 6.6s.9 4.6 2.9 6.6"/></svg></button>\n      ')
out = rep(out, '<button id="theme" class="ibtn theme"', _globe + '<button id="theme" class="ibtn theme"')
out = rep(out, '<div id="card" class="pnl" role="dialog"', '<div id="satcred" hidden>Imagery: USDA, USGS The National Map</div>\n<div id="card" class="pnl" role="dialog"')
out = rep(out, "applyVB();atsFrame();", "applyVB();atsFrame();satFrame();")
out = rep(out, "</style>", ".sat{display:none;filter:brightness(.72) saturate(.85)}\nbody.satmode .sat{display:inline}\n"
  ':root[data-theme="light"] .sat{filter:brightness(.97) saturate(.9)}\n'
  ".river{fill:var(--lake);stroke:var(--shore);stroke-width:.6px;vector-effect:non-scaling-stroke}\n"
  "body.satmode .town,body.satmode .city,body.satmode .grid,body.satmode .river{display:none}\n"   # (the drawn lake, its glints and the sonar stay on top of the photos)
  "#satBtn svg *{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}\n"
  '#satBtn[aria-pressed="true"]{color:var(--ink);background:var(--pressed)}\n'
  "#satcred{position:absolute;left:50%;transform:translateX(-50%);bottom:calc(64px + env(safe-area-inset-bottom,0px));z-index:1;pointer-events:none;"
  "font-size:11px;color:var(--muted);background:var(--panel);padding:2px 8px;border-radius:6px;white-space:nowrap}\n#satcred[hidden]{display:none}\n"
  "@media (max-width:760px){#satcred{left:10px;transform:none;bottom:calc(116px + env(safe-area-inset-bottom,0px))}}\n"
  "@media (max-width:360px){#satBtn{display:none}}\n</style>")

# ---- the tilted ride view stays sharp when something repaints (same edits as MetraBot: src/tiltfix.py)
exec(open(os.path.join(F, "tiltfix.py")).read())
for _a, _b in EDITS:
    out = rep(out, _a, _b)

# ---- check-ins: shorter rides (50 s), and they carry on in a background tab (same edits as MetraBot)
exec(open(os.path.join(F, "bgvoice.py")).read())
for _a, _b in EDITS:
    out = rep(out, _a, _b)

# ---- a train stopped at a station doesn't turn its wheels (cute style)
out = rep(out, "const roll=known&&!stale&&now-t.segT0<t.segDur&&Math.abs(t.segTo-t.segFrom)>.01&&!reduceMotion();",
               "const roll=known&&!stale&&now-t.segT0<t.segDur&&Math.abs(t.segTo-t.segFrom)>.01&&!t.dwell&&!reduceMotion();")

# ---- the Loop, cleaned up: a dimmed line's casing dims with it (casings now sit in their own layer under the colours)
out = rep(out, 'lineEls[k].track.classList.toggle("dim",!!key&&k!==key)}', 'lineEls[k].track.classList.toggle("dim",!!key&&k!==key);if(lineEls[k].cases)lineEls[k].cases.classList.toggle("dim",!!key&&k!==key)}')

# whole-page wording and storage names
out = out.replace('"metrabot.', '"ctabot.').replace("metrabot.favorites", "ctabot.favorites")
left = [m.group(0) for m in re.finditer(r".{30}\bMetra\b.{30}", out.replace(blk("i_ats.js"), "").replace("for Metra commuter rail", ""))]   # the ATS card names Metra's airport stop on purpose
if left:
    sys.exit("Metra wording left: " + " | ".join(left[:5]))
open(os.path.join(F, "..", "index.html"), "w").write(out)
print("wrote", len(out) // 1024, "KB")
