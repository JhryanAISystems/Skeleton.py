// head_servo_mount.scad
//
// L-bracket that clamps an MG996R servo to a vertical spine rod (metal
// rod or 1/2" PVC pipe run up through the skeleton's spine) and provides
// a horn-to-neck-rod coupling on top.
//
// PRINT SETTINGS: PLA or PETG, 20% infill, 3 perimeters, no supports
// needed if printed with the spine-clamp face down.
//
// Render to STL: install OpenSCAD (openscad.org, free), open this file,
// press F6 to render, then File > Export > Export as STL.

// ---- Parameters (mm) — edit these to match your exact servo/rod ----
servo_body_l   = 40.7;   // MG996R body length
servo_body_w   = 20.2;   // MG996R body width
servo_body_h   = 38.0;   // MG996R body height (top of case to bottom, no horn)
servo_tab_l    = 54.7;   // outer length across the two mounting tabs
servo_tab_hole_spacing = 49.5; // distance between the two tab screw holes
tab_hole_d     = 3.2;    // M3 screw clearance

spine_rod_od   = 12.7;   // 1/2" PVC OD ≈ 12.7mm; use your rod's actual OD
neck_rod_od    = 6.0;    // dowel/rod inserted into the skull

wall = 3.5;              // bracket wall thickness
clamp_gap = 2.0;         // slot width that lets the clamp flex closed

$fn = 60;

module servo_cutout() {
    // Pocket that the servo body drops into, open on top for the horn shaft.
    translate([-servo_body_l/2, -servo_body_w/2, 0])
        cube([servo_body_l, servo_body_w, servo_body_h + 1]);
}

module tab_holes() {
    for (x = [-servo_tab_hole_spacing/2, servo_tab_hole_spacing/2])
        translate([x, 0, -1])
            cylinder(h = wall*2 + 2, d = tab_hole_d);
}

module spine_clamp() {
    // A split ring that clamps around the vertical spine rod. Two ears
    // with holes let you cinch it tight with a small M3 bolt + nut, or
    // just zip-tie through them if you'd rather not tap threads.
    outer_d = spine_rod_od + wall*2;
    difference() {
        union() {
            cylinder(h = 25, d = outer_d);
            // clamp ears
            for (side = [-1, 1])
                translate([side * (outer_d/2 - 1), -6, 0])
                    cube([10, 12, 25]);
        }
        translate([0, 0, -1]) cylinder(h = 27, d = spine_rod_od);
        // the slot that lets the ring flex closed around the rod
        translate([-clamp_gap/2, 0, -1]) cube([clamp_gap, outer_d, 27]);
        // ear bolt holes
        for (side = [-1, 1])
            translate([side * (outer_d/2 + 4), 0, 12.5])
                rotate([90,0,0]) cylinder(h = 20, d = 3.2, center = true);
    }
}

module servo_platform() {
    // Flat plate on top of the spine clamp that the servo sits on,
    // secured through its mounting tabs.
    plate_l = servo_tab_l + 6;
    plate_w = servo_body_w + wall*2;
    plate_h = wall;

    difference() {
        translate([-plate_l/2, -plate_w/2, 0])
            cube([plate_l, plate_w, plate_h]);
        translate([0, 0, plate_h/2])
            servo_cutout();
        translate([0, 0, plate_h/2])
            tab_holes();
    }
}

module neck_rod_collar() {
    // Sits on the servo horn (glue or horn-screw through the center hole)
    // and grips the rod that runs up into the skull.
    difference() {
        cylinder(h = 15, d = neck_rod_od + wall*2);
        translate([0,0,-1]) cylinder(h = 17, d = neck_rod_od);
        // set-screw hole to pin the rod in place
        translate([0, 0, 8]) rotate([90,0,0])
            cylinder(h = neck_rod_od + wall*2 + 2, d = 2.5, center = true);
    }
}

// ---- Assembly (printed as separate pieces, positioned here for preview) ----
spine_clamp();
translate([0, 0, 25]) servo_platform();
translate([40, 0, 0]) neck_rod_collar();
