/* ---- the line under the title: what the L is doing right now (Chicago time) ----
   A new line every 10 minutes, drifting across the top bar like a calm ticker. Two kinds take turns:
   numbers read live off the map (how many trains, which line has the most, trains around the Loop...) and lines
   about the time of day that are true by CTA's schedule (Purple Line Express runs only at weekday rush;
   the Red and Blue Lines run all night). Delays CTA reports always come first. Nothing here is guessed. */
const MOOD_WEEKDAY=[
  [240,330,["The first trains of the morning are rolling out.", "Most lines are making their first runs of the day.", "Early trains, quiet platforms.", "The Red and Blue Lines ran all night. Everything else is waking up."]],
  [330,420,["The morning rush is building.", "More trains joining the map every few minutes.", "Commuters are starting to head downtown.", "Purple Line Express is starting its morning runs."]],
  [420,570,["Rush hour: Purple Line Express is running to the Loop.", "Brown Line trains are lining up into the Loop.", "Rush hour: trains every few minutes on the Red and Blue.", "Morning rush. Packed trains headed downtown.", "The busiest part of the morning on the L."]],
  [570,630,["The morning rush is easing off.", "Purple Line Express is wrapping up for the morning.", "Fewer trains now as the rush winds down."]],
  [630,870,["Purple Line is shuttling between Linden and Howard.", "A calmer stretch between the rushes.", "Midday on the L. Easier to find a seat.", "Steady trains in both directions."]],
  [870,960,["The evening rush is starting to build.", "Purple Line Express is starting its evening runs.", "People are starting to head home."]],
  [960,1110,["Purple Line Express is heading back to Evanston.", "Loop trains are circling and heading home.", "Evening rush. Crowded trains leaving the Loop.", "Rush hour: trains every few minutes on the Red and Blue."]],
  [1110,1170,["The evening rush is winding down.", "Fewer trains now as the rush fades.", "The last Purple Line Express runs are heading out."]],
  [1170,1380,["A quieter evening on the L.", "Longer gaps between trains tonight.", "Purple Line is back to Linden–Howard shuttles.", "Evening trains, easy rides home."]],
  [1380,1470,["Most lines are wrapping up for the night.", "The last trains on several lines are heading out.", "Owl service soon: only the Red and Blue Lines run all night."]]];   // [from, to) in minutes after midnight
const MOOD_WEEKEND=[
  [240,540,["Weekend morning on the L.", "A slow weekend start.", "Purple Line is shuttling between Linden and Howard.", "Weekend trains are getting going."]],
  [540,1080,["Weekend service on the L.", "A good day for a trip downtown.", "Weekend trains, roomier rides.", "Purple Line is shuttling between Linden and Howard."]],
  [1080,1380,["A weekend evening on the L.", "Trains heading in for the night out.", "Evening trains, lighter service."]],
  [1380,1470,["Late weekend night. Most lines wrap up soon.", "Owl service soon: only the Red and Blue Lines run all night.", "The last trains on several lines are heading out."]]];
const MOOD_NIGHT=["Owl service: only the Red and Blue Lines run all night.", "Overnight on the L: the Red and Blue are still running.", "Everything else is parked until morning.", "A quiet night on the L."];
const moodEl=$("mood"),moodPick={},dayFmt=new Intl.DateTimeFormat("en-US",{timeZone:"America/Chicago",weekday:"short"});
let moodText="";
const chiFmt=new Intl.DateTimeFormat("en-US",{timeZone:"America/Chicago",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"});
function chiParts(ms){const p={};for(const x of chiFmt.formatToParts(new Date(ms)))p[x.type]=x.value;return p}
const SIT={
  nothing:["No trains reporting right now.","Quiet tracks until the first trains.","Most lines are parked for the night."],
  late:["Delays on several lines right now.","CTA is reporting delays across the system.","A slow stretch. Several lines are running late."],
  line:["Delays on the {L} right now.","The {L} is running behind. Other lines look normal.","Heads up: CTA reports delays on the {L}."]};
const LOOP_C=(()=>{const c=geo(41.8818,-87.6298),e=geo(41.8818,-87.6250);return{c,r:Math.hypot(e[0]-c[0],e[1]-c[1])*1.25}})();
let moodSit={key:"",why:""},sitCache=null,sitAt=0,statSlot=-1,statLines=null;
// numbers straight off the live map, worked out once per 10-minute slot so the line doesn't flicker
function liveStats(live){
  const by={};for(const t of live)by[t.L.key]=(by[t.L.key]||0)+1;
  const top=ORDER.filter(k=>by[k]).sort((a,b)=>by[b]-by[a])[0];
  const loop=live.filter(t=>Math.hypot(t.shown[0]-LOOP_C.c[0],t.shown[1]-LOOP_C.c[1])<LOOP_C.r).length;
  const ohare=live.filter(t=>t.L.key==="blue"&&t.cta&&/o'?hare/i.test(t.cta.dest||"")).length;
  const out=[`${live.length} trains on the L right now.`];
  if(top&&by[top]>=3)out.push(`The ${LINES[top].name} has the most trains out: ${by[top]}.`);
  if(loop>=12)out.push(`A busy moment in the Loop: ${loop} trains circling it.`);else if(loop>=4)out.push(`${loop} trains around the Loop right now.`);
  if(ohare>=2)out.push(`${ohare} Blue Line trains heading to O'Hare.`);
  return out}
function liveSituation(now){
  if(mode==="sim"||!feedHealthy())return null;
  const hr=+chiParts(now).hour,live=trains.filter(t=>!t.stale),N=live.length;
  if(N===0)return hr>=1&&hr<5?{key:"nothing"}:null;                    // no trains in the day: don't trust it, use the clock
  // 1. delays CTA reports
  const dl=live.filter(t=>t.cta&&t.cta.delayed);
  if(N>=20&&dl.length/N>=.25)return{key:"late"};
  const by={};for(const t of dl)by[t.L.key]=(by[t.L.key]||0)+1;let worst=null;
  for(const k in by){const tot=live.filter(t=>t.L.key===k).length;if(by[k]>=3&&by[k]/tot>=.3&&(!worst||by[k]>by[worst]))worst=k}
  if(worst)return{key:"line",line:LINES[worst].name};
  // 2. every other 10 minutes: what the live map shows
  const slot=Math.floor(now/600e3);if(slot%2)return null;
  if(slot!==statSlot||!statLines){statSlot=slot;statLines=liveStats(live)}
  return{key:"stats"+slot,lines:statLines}}
