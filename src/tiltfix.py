# shared fix: the tilted map was rasterised once at the start of the tilt and never again at its final size
# (will-change:transform freezes the raster scale), so any repaint (a sonar ping, switching train style) came out blurry.
EDITS = [
 ("#stage.tilt{transform-origin:50% 62%;will-change:transform}",
  "#stage.tilt{transform-origin:50% 62%}\n#stage.tilt.moving{will-change:transform}   /* only while it tilts in or out: then it's redrawn sharp at its final size */"),
 ('stage.classList.add("tilt");stage.style.transform=',
  'stage.classList.add("tilt");stage.classList.toggle("moving",k<.999);stage.style.transform='),
 ('if(k<=.001){if(stage.classList.contains("tilt")){stage.classList.remove("tilt");',
  'if(k<=.001){if(stage.classList.contains("tilt")){stage.classList.remove("tilt","moving");'),
]
