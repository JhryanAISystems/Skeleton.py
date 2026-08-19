// eye_socket_camera_mount.scad
//
// A snap-fit ring that holds a Raspberry Pi Camera Module (v2/v3) inside
// one eye socket, angled slightly downward toward visitors. The other eye
// socket uses eye_led_diffuser.scad instead — this build uses ONE eye for
// the camera and ONE for the LED, since both don't fit in most skull eye
// sockets side by side.
//
// PRINT SETTINGS: PLA, 15% infill. Print with the flat face down; the
// downward camera-angle tilt is applied by how you glue this into the
// socket, not by the print geometry, so orientation during printing is
// simple.

cam_board_w   = 25.0;  // Camera Module PCB is ~25x24mm for v2/v3
cam_board_h   = 24.0;
cam_board_thick = 1.5;
cam_lens_d    = 8.0;   // clearance hole for the lens housing

socket_od     = 34.0;  // adjust to your skeleton's actual eye socket diameter
ring_thick    = 3.0;
ring_depth    = 10.0;

$fn = 60;

module camera_pocket() {
    translate([-cam_board_w/2, -cam_board_h/2, 0])
        cube([cam_board_w, cam_board_h, cam_board_thick + 0.5]);
}

module lens_hole() {
    translate([0, 0, -1])
        cylinder(h = ring_depth + 2, d = cam_lens_d);
}

module ribbon_slot() {
    // Slot for the CSI ribbon cable to exit toward the back of the skull.
    translate([-6, cam_board_h/2 - 1, 0])
        cube([12, ring_thick + 2, cam_board_thick + 1]);
}

difference() {
    cylinder(h = ring_depth, d = socket_od);
    translate([0, 0, ring_depth - cam_board_thick - 1])
        camera_pocket();
    lens_hole();
    translate([0, 0, ring_depth - cam_board_thick - 1])
        ribbon_slot();
    // hollow the center so the ring is a thin shell, not a solid disc
    translate([0, 0, -1])
        cylinder(h = ring_depth - cam_board_thick - 0.5, d = socket_od - ring_thick*2);
}
