# shared edits: shorter rides, check-ins keep going in a background tab
EDITS = [
 ("const CH={IDLE:120000,IN:3200,RIDE:60000,", "const CH={IDLE:120000,IN:3200,RIDE:50000,"),
 ("if(Date.now()-lastInput>(isTouch()?PHONE_IDLE:CH.IDLE)&&!chaseBusy()&&!reduceMotion()&&!document.hidden&&trains.length)startRide(now);",
  "if(Date.now()-lastInput>(isTouch()?PHONE_IDLE:CH.IDLE)&&!chaseBusy()&&!reduceMotion()&&(!document.hidden||bgVoice())&&trains.length)startRide(now);"),
 ('document.addEventListener("visibilitychange",()=>{if(!document.hidden||!chase)return;',
  'document.addEventListener("visibilitychange",()=>{if(!document.hidden||!chase||bgVoice())return;'),
 ('let voice=!!(VO.man&&actx&&actx.state==="running"&&!document.hidden);', 'let voice=!!(VO.man&&actx&&actx.state==="running");'),
 ('document.addEventListener("visibilitychange",()=>{if(document.hidden)ciStop()});',
  '// in a background tab (sound on, check-ins on) rides and check-ins carry on: the ride clock ticks once a second\n'
  '// without drawing, so you can listen while you work in another tab\n'
  'function bgVoice(){return ciOn&&!!actx&&actx.state==="running"}\n'
  'setInterval(()=>{if(!document.hidden||!bgVoice())return;const now=performance.now(),t=chase&&chase.t;\n'
  '  if(t&&!t.gone&&t.L){const p=poseAt(t.L.routes[t.ri],curS(t,now));t.shown=[p.x,p.y]}\n'
  '  chaseFrame(now,1)},1000);\n'
  'document.addEventListener("visibilitychange",()=>{if(document.hidden&&!bgVoice())ciStop()});'),
]
