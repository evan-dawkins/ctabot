# shared fix: the ride camera turned the whole map to match the train icon's exact angle, so any sudden change
# (a direction flip from a CTA/Metra report, a kink in the track) spun the map. Now it looks a little way ahead
# along the track, turns with a gentle speed limit, and a train that reverses ends the ride instead of spinning.
# Also: a ride that ended early (train went quiet, you opened something) used to snap straight to the flat map,
# because the pull-back started with the ride's old clock; it now glides out like a normal ending.
EDITS = [
 ('const want=headingOf(t);\n    chase.a+=angDiff(chase.a,want)*(1-Math.exp(-dt/1.1));            // ease round the bends over about a second',
  'const want=chaseHeading(t,now);\n'
  '    {const d=angDiff(chase.a,want),w0=1.6;chase.av=(chase.av||0)+(w0*w0*d-2*w0*(chase.av||0))*dt;   // a soft spring, never faster than ~25 degrees a second\n'
  '     chase.av=Math.max(-.45,Math.min(.45,chase.av));chase.a+=chase.av*dt}'),
 ('if((chase.phase==="in"||chase.phase==="ride")&&(!chaseOk(t)||chaseBusy()))endChase(now,false);',
  'if((chase.phase==="in"||chase.phase==="ride")&&(!chaseOk(t)||chaseBusy())){endChase(now,false);return true}   // (next frame starts the pull-back from here, instead of snapping)\n'
  '  if((chase.phase==="in"||chase.phase==="ride")&&!chase.manual){if(chase.dir==null)chase.dir=t.dirSign;else if(t.dirSign!==chase.dir){endChase(now,false);return true}}   // it turned round: end the ride, don\'t spin the map'),
 ('const headingOf=t=>-Math.PI/2-t.rot*Math.PI/180;                     // the world turn that points this train up the screen',
  'const headingOf=t=>-Math.PI/2-t.rot*Math.PI/180;                     // the world turn that points this train up the screen\n'
  '// the same, but from where the track goes over the next stretch (about a quarter of the screen ahead), so the\n'
  '// camera starts round a bend smoothly and ignores small kinks\n'
  'function chaseHeading(t,now){const r=t.L.routes[t.ri],p=poseAt(r,curS(t,now)),L=vb.w*.22,tot=r.ac[r.ac.length-1];\n'
  '  const d1=Math.max(0,Math.min(tot,p.d+t.dirSign*L)),d0=Math.max(0,Math.min(tot,p.d-t.dirSign*L*.25));\n'
  '  if(!(Math.abs(d1-d0)>L*.3))return headingOf(t);\n'
  '  const a=along(r.anc,r.ac,d0),b=along(r.anc,r.ac,d1);return angDiff(0,-Math.PI/2-Math.atan2(b[1]-a[1],b[0]-a[0]))}   // the short way round'),
]
