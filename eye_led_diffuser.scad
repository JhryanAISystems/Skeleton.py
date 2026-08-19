// eye_led_diffuser.scad
//
// A frosted-look dome that sits in the eye socket NOT occupied by the
// camera (see eye_socket_camera_mount.scad), holding an LED and
// scattering its light into a soft glow instead of a harsh point source.
//
// PRINT SETTINGS: print in translucent/natural PLA (not opaque colors —
// you need light to pass through the shell) at 2 perimeters / low infill
// (10-15%) so light diffuses through the thin walls evenly.

socket_od   = 34.0;   // match eye_socket_camera_mount.scad's socket_od
dome_depth  = 16.0;
shell_thick = 1.6;    // thin on purpose — this is what makes it glow evenly

led_lead_hole_d = 4.0; // clearance for the LED body + leads to pass through

$fn = 80;

module dome_shell() {
    difference() {
        sphere(d = socket_od);
        translate([0, 0, -socket_od/2])
            cube([socket_od+2, socket_od+2, socket_od], center = true);
        sphere(d = socket_od - shell_thick*2);
    }
}

module base_ring() {
    difference() {
        cylinder(h = 4, d = socket_od);
        translate([0, 0, -1]) cylinder(h = 6, d = socket_od - shell_thick*2);
    }
}

module led_hole() {
    translate([0, 0, -1]) cylinder(h = 6, d = led_lead_hole_d);
}

union() {
    intersection() {
        translate([0, 0, dome_depth - socket_od/2]) dome_shell();
        translate([0, 0, -1]) cylinder(h = dome_depth + 1, d = socket_od);
    }
    difference() {
        base_ring();
        led_hole();
    }
}
