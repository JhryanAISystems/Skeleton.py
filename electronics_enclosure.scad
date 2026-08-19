// electronics_enclosure.scad
//
// A ventilated box sized for the Raspberry Pi Zero 2 W plus its wiring,
// meant to sit inside the ribcage. Standoffs match the Zero's mounting
// holes; slots on the sides let servo/LED/sensor wires and the USB audio
// dongle pass through without needing extra drilled holes later.
//
// PRINT SETTINGS: PLA or PETG, 20% infill, supports needed only for the
// standoffs' overhang if you print in one piece — or print the lid
// separately (recommended) to avoid supports entirely.

// Pi Zero 2 W board: 65mm x 30mm, mounting holes 3.5mm from each edge corner
board_l = 65.0;
board_w = 30.0;
hole_inset = 3.5;
hole_d = 2.7;          // clearance for M2.5 standoffs/screws

wall = 2.0;
box_h = 22.0;           // interior clearance above the board for the camera
                         // ribbon connector and GPIO header
lid_h = 3.0;

standoff_od = 6.0;
standoff_h  = 6.0;      // lifts the board off the floor for wire clearance

$fn = 40;

module standoff(x, y) {
    translate([x, y, wall])
        difference() {
            cylinder(h = standoff_h, d = standoff_od);
            translate([0,0,-1]) cylinder(h = standoff_h+2, d = hole_d);
        }
}

module box_body() {
    outer_l = board_l + wall*2 + 6;
    outer_w = board_w + wall*2 + 6;

    difference() {
        cube([outer_l, outer_w, box_h]);
        translate([wall, wall, wall])
            cube([outer_l - wall*2, outer_w - wall*2, box_h]);

        // GPIO header access slot along one long edge (ribbon or jumper
        // wires exit here toward the servos/LEDs/sensors)
        translate([wall + 5, -1, box_h - 10])
            cube([outer_l - wall*2 - 10, wall + 2, 8]);

        // USB audio dongle + micro-USB power cable exit slot, opposite edge
        translate([wall + 5, outer_w - wall - 1, box_h - 14])
            cube([outer_l - wall*2 - 10, wall + 2, 10]);

        // camera ribbon exit slot, short edge
        translate([-1, outer_w/2 - 8, box_h - 8])
            cube([wall + 2, 16, 6]);

        // ventilation slots on the lid-facing top rim (simple slits)
        for (i = [0:5])
            translate([12 + i*14, -1, box_h/2])
                cube([4, wall+2, 10]);
    }

    standoff(hole_inset + 3, hole_inset + 3);
    standoff(outer_l - wall - hole_inset - 3, hole_inset + 3);
    standoff(hole_inset + 3, outer_w - wall - hole_inset - 3);
    standoff(outer_l - wall - hole_inset - 3, outer_w - wall - hole_inset - 3);
}

box_body();

// Print a matching flat lid separately:
//   cube([outer_l, outer_w, lid_h])
// sized to friction-fit or be held with two small screws into the two
// standoffs nearest the lid opening — adjust to taste, this enclosure is
// deliberately simple so it's easy to modify.
