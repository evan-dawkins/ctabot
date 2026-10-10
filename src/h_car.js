  // A CTA 7000-series car, seen from above, facing +x: brushed stainless with ribbed sides, a blue cab end with a
  // black windshield and pink-ringed headlights, and AC units on the roof. Real cars don't carry their line's colour;
  // here a thin stripe down each side does, so the lines stay easy to tell apart.
  if(!window.__cg){window.__cg=1;
    const steel=el("linearGradient",{id:"cta-steel",x1:0,y1:0,x2:0,y2:1},defs);
    for(const[o,c]of[[0,"#8E99A3"],[.18,"#D9DFE4"],[.5,"#F2F5F7"],[.82,"#C9D0D6"],[1,"#7F8A94"]])el("stop",{offset:o,"stop-color":c},steel);
    const blue=el("linearGradient",{id:"cta-blue",x1:0,y1:0,x2:0,y2:1},defs);
    for(const[o,c]of[[0,"#0B4FA8"],[.5,"#2F86E6"],[1,"#0A4596"]])el("stop",{offset:o,"stop-color":c},blue)}
  const carFlip=el("g",{class:"car"},inner),cz=el("g",{},carFlip);
  el("rect",{x:-13.6,y:-3.6,width:29,height:9.2,rx:3,fill:"#000",opacity:.22},cz);                                     // shadow underneath
  const cb=el("g",{class:"cb"},cz);
  el("path",{d:"M15.5,0 L27,-4.2 L27,4.2 Z",fill:"#FFE7A3",opacity:.16},cb);                                         // headlight beam
  el("path",{d:"M-13,-4.6 L12.4,-4.6 Q15.4,-4.6 15.6,-2.2 L15.6,2.2 Q15.4,4.6 12.4,4.6 L-13,4.6 Q-14.6,4.6 -14.6,3 L-14.6,-3 Q-14.6,-4.6 -13,-4.6 Z",
    fill:"url(#cta-steel)",stroke:"var(--bg)","stroke-width":1.1,"stroke-linejoin":"round"},cb);                        // stainless body, squared off like the 7000s
  for(const y of[-4.3,3.2])el("rect",{x:-13.2,y,width:23.4,height:1.1,rx:.55,fill:L.color},cb);                          // the line's colour, down each side
  el("path",{d:"M-12.6,-2.9H9.4M-12.6,2.9H9.4",stroke:"#9AA5AF","stroke-width":.35,fill:"none"},cb);                     // ribbed stainless edges
  for(const x of[-10.4,-1.6])el("rect",{x,y:-1.9,width:5.4,height:3.8,rx:.8,fill:"#6E7A85"},cb);                        // roof AC units
  el("path",{d:"M-9.6,-.9h3.8M-9.6,.9h3.8M-.8,-.9h3.8M-.8,.9h3.8",stroke:"#9AA5AF","stroke-width":.35},cb);
  el("path",{d:"M10.2,-4.6 L12.4,-4.6 Q15.4,-4.6 15.6,-2.2 L15.6,2.2 Q15.4,4.6 12.4,4.6 L10.2,4.6 Z",fill:"url(#cta-blue)"},cb);   // blue cab end
  el("path",{d:"M13.2,-2.8 Q14.6,-2.4 14.7,0 Q14.6,2.4 13.2,2.8",stroke:"#0B1118","stroke-width":1.4,fill:"none","stroke-linecap":"round"},cb);  // windshield
  for(const y of[-3.4,3.4])el("circle",{cx:14.8,cy:y,r:.75,fill:"#FF5A6E",stroke:"#FFC2CC","stroke-width":.35},cb);    // headlights
