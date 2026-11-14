// Placeholder enclosure model.
//
// Real enclosure geometry (two shells, button plungers, antenna mount, USB-C
// cutout) lands via pilink-8hx. This trivial cube exists only to seed the
// docker-compose preview pipeline (preview/) so the OpenSCAD -> STL -> GLB
// export chain already works end-to-end the moment real geometry lands here.
cube([20, 20, 10], center = true);
