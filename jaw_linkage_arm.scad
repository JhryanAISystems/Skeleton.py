// jaw_linkage_arm.scad
//
// A rigid extension arm connecting the jaw servo's horn to the skull's
// jaw hinge pin, so the servo (mounted inside the upper skull) can pull
// the jaw open/closed as it rotates.
//
// PRINT SETTINGS: PLA or PETG, 100% infill (this part takes repeated
// mechanical stress — don't skimp on infill here), no supports needed.

arm_length   = 32;   // horn-pivot to jaw-pivot distance — measure your skull
arm_width    = 8;
arm_thick    = 4;

horn_hole_d  = 2.0;   // standard servo horn screw-hole diameter
jaw_pin_d    = 3.0;   // diameter of the pin/pivot you'll use at the jaw end

horn_circle_d = 24;   // MG996R horn diameter, for the mounting pattern
$fn = 40;

module arm() {
    difference() {
        union() {
            // main arm body, rounded ends
            hull() {
                translate([0, 0, 0]) cylinder(h = arm_thick, d = arm_width);
                translate([arm_length, 0, 0]) cylinder(h = arm_thick, d = arm_width);
            }
        }
        // horn-side mounting holes (screw straight into a servo horn arm,
        // or drill out to match your specific horn's hole pattern)
        translate([0, 0, -1]) cylinder(h = arm_thick + 2, d = horn_hole_d);
        for (a = [0:90:270])
            rotate([0, 0, a])
                translate([horn_circle_d/2, 0, -1])
                    cylinder(h = arm_thick + 2, d = horn_hole_d);
        // jaw-pivot hole at the far end
        translate([arm_length, 0, -1]) cylinder(h = arm_thick + 2, d = jaw_pin_d);
    }
}

arm();

// Reminder: rubber-dampen the jaw pivot end (a short piece of silicone
// tubing over the pin) so the jaw doesn't clack loudly against the skull
// on every closure — the original build guide's "add rubber dampers" step
// still applies here, just at this specific joint.
