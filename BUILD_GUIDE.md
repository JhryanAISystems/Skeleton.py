# 💀 BUILD GUIDE — Animatronic Skeleton on Raspberry Pi Zero 2 W

*Written for a first-time hobbyist. If you've never soldered, wired a
breadboard, or flashed an SD card before, you can still do this — every
step says exactly what to do and why. Budget a full weekend for the first
build.*

---

## Before you start: what this build does and doesn't do

- ✅ Real camera-based face tracking (OpenCV Haar-cascade detection)
- ✅ Head servo turns to follow whoever it detects
- ✅ Jaw synced live to microphone volume
- ✅ Two personality modes (calm "Host" / jump-scare "Trickster")
- ✅ Mode switches on loud noise, a knock, or someone getting close
- ✅ Pre-recorded voice lines + offline text-to-speech
- ⚠️ The Pi Zero 2 W is the *cheapest* board that can still do all of the
  above — but it's noticeably slower than a Pi 4/5. We compensate with a
  smaller camera resolution and a slower control loop (see `config.py`).
  If your Trickster mode feels sluggish, that's the first thing to know
  about, not a bug.

---

## Part 1 — Shopping list

Prices are rough USD estimates as of writing; shop around.

### Electronics

| Item | Qty | Approx. price | Notes |
|---|---|---|---|
| Raspberry Pi Zero 2 W (with headers) | 1 | $18 | Get the **with pre-soldered header** version unless you're comfortable soldering 40 pins yourself |
| microSD card, 16GB+, class 10 | 1 | $8 | This is where the OS and your code live |
| Raspberry Pi Camera Module v2 or v3 | 1 | $15–25 | v3 has autofocus, nice-to-have, not required |
| **Raspberry Pi Zero camera cable** | 1 | $3 | ⚠️ **Do not skip this.** The Zero 2 W's CSI port is the narrow style — the cable that ships with the camera module will NOT fit. Search "Pi Zero camera cable" specifically. |
| MG996R servo | 2 | $6 each | One for head rotation, one for the jaw |
| USB audio adapter (mic-in + headphone-out combo) | 1 | $6 | This is your mic AND speaker — the Zero 2 W has no audio jack |
| micro-USB to USB-A OTG adapter | 1 | $4 | Lets the USB audio dongle plug into the Zero's data micro-USB port |
| Small powered speaker or amplified 3.5mm speaker | 1 | $8 | Plugs into the USB audio dongle's headphone jack |
| High-brightness LEDs (amber, red, or bi-color) | 2 | $1 each | Eyes — only need 1 if you're putting the camera in the other socket |
| 220Ω resistors | 2 | <$1 | Current-limiting for the LEDs |
| Piezo disc or small vibration sensor | 1 | $2 | Knock sensor |
| HC-SR04 ultrasonic distance sensor | 1 | $3 | Proximity trigger |
| Logic-level shifter (or 1kΩ + 2kΩ resistor pair) | 1 | $2 | HC-SR04's ECHO pin outputs 5V; the Pi's GPIO is 3.3V-only |
| Female-to-female jumper wires (pack) | 1 | $5 | For sensor/LED wiring |
| Male-to-female jumper wires (pack) | 1 | $5 | For servo wiring |
| 5V 2.5A micro-USB power supply | 1 | $8 | Powers the Pi — use a real phone-charger-quality supply, not a cheap one; brownouts cause mysterious bugs |
| 4×AA battery holder + switch (6V) **or** a 6V 2A wall adapter | 1 | $5–10 | **Dedicated servo power** — never power servos from the Pi's 5V rail |
| Small proto-board or terminal block | 1 | $3 | Optional, makes wiring tidier than loose jumpers |

**Electronics subtotal: roughly $100–120**

### 3D-printed parts (see Part 4) — or substitute materials

| Item | Qty | Notes |
|---|---|---|
| PLA filament (standard color) | ~150g | Servo mounts, jaw linkage, enclosure |
| PLA filament, **translucent/natural** | ~30g | Eye diffuser dome only — needs to glow, not print opaque |
| Small M3 bolts + nuts | ~8 | Spine clamp and mount assembly |
| M2.5 standoffs or small self-tapping screws | 4 | Mounting the Pi board in its enclosure |

*No printer? See "No 3D printer?" at the end of Part 4 for a buy-instead
alternative for every printed part.*

### Structure and props

| Item | Qty | Notes |
|---|---|---|
| Full-size plastic prop skeleton | 1 | Any Halloween-decor skeleton with a detachable head/skull works |
| Metal rod or ½" PVC pipe, ~4ft | 1 | Spine reinforcement |
| Wooden dowel or metal rod, ~6" | 1 | Neck rotation shaft (goes servo → skull) |
| Short length of silicone tubing | ~1" | Dampens the jaw pivot so it doesn't clack |
| Zip ties | 1 pack | Cable management + neck reinforcement |
| Stand or wall bracket | 1 | However you're mounting the finished prop |

---

## Part 2 — Physical assembly

### 2.1 Reinforce the skeleton

1. Run the metal rod or PVC pipe up through the spine to eliminate wobble.
2. Zip-tie or screw it to the ribcage/pelvis mounting points your prop skeleton has.
3. Mount the reinforced skeleton on its stand or wall bracket now — it's much easier to work on upright.

### 2.2 Head servo + neck rotation

1. Print `head_servo_mount.scad` (see Part 4) — this gives you a spine clamp, a servo platform, and a neck-rod collar.
2. Clamp the spine-clamp piece around your spine rod at the top, just below where the neck meets the skull, and bolt or zip-tie it snug (it has a flex-slot for this).
3. Screw the MG996R into the servo platform using its mounting tabs, then attach the platform on top of the clamp.
4. Push your neck dowel/rod into the skull's neck opening (glue if it's loose) and attach the other end to the printed neck-rod collar.
5. Slide the collar onto the servo horn and secure with the horn's screw, at the servo's **center (90°) position** — this becomes your head's forward-facing center.
6. Reattach the skull. Manually rotate the servo horn (unpowered) through its range to confirm the head turns freely without binding on wires or the ribcage.

### 2.3 Jaw servo

1. Open the skull if it's detachable, or work through the mouth opening if not.
2. Mount the second MG996R inside the upper skull using screws or strong epoxy, positioned so its horn is near the jaw hinge.
3. Print `jaw_linkage_arm.scad`, measuring your actual horn-to-jaw-pivot distance first and editing the `arm_length` variable at the top of the file before rendering.
4. Screw the arm to the servo horn, and thread the silicone tubing over the jaw-pivot pin before connecting the arm's other end — this is your rubber damper, so the jaw doesn't clack loudly on every closure.
5. Manually cycle the jaw through open/closed (servo unpowered) to confirm it doesn't bind.

### 2.4 Camera in one eye socket

1. Print `eye_socket_camera_mount.scad`, measuring your skull's actual eye socket diameter first (edit `socket_od`).
2. Seat the Camera Module into the printed ring — it should snap/friction-fit against the pocket.
3. Route the CSI ribbon cable back through the skull and down the spine toward the chest cavity. **Be gentle** — these ribbons crease permanently if bent sharply.
4. Glue or press-fit the ring into the eye socket, angled *very slightly* downward — visitors are usually shorter than the skeleton's natural eye line.

### 2.5 LED eye

1. Print `eye_led_diffuser.scad` in **translucent** filament — this is the one part where filament color matters functionally, not just aesthetically.
2. Wire your LED with its 220Ω resistor (resistor in series on the positive leg), thread the leads through the diffuser's base hole, and seat the LED inside the dome.
3. Press-fit or glue the diffuser into the remaining eye socket.

### 2.6 Microphone and speaker

1. Mount the USB audio dongle somewhere accessible — behind the ribcage or teeth works, since you'll want to reach it if you ever need to re-seat the USB connection.
2. Route a short USB extension or the OTG adapter down to where the Pi will live.
3. Mount the small speaker inside the ribcage, plugged into the dongle's headphone-out jack.

### 2.7 Knock sensor and proximity sensor

1. Mount the piezo/vibration sensor on the door frame or wherever visitors will actually knock or brush against.
2. Mount the HC-SR04 facing the approach path to your entrance — usually at chest height on the prop itself, or on a nearby post.
3. **Wire the HC-SR04's ECHO pin through your logic-level shifter (or the 1kΩ/2kΩ resistor divider)** before it reaches the Pi's GPIO — skipping this step risks damaging the GPIO pin, since the sensor outputs 5V and the Pi's inputs are 3.3V only.

### 2.8 Electronics enclosure and power

1. Print `electronics_enclosure.scad` and its lid.
2. Mount the Pi Zero 2 W inside on the four standoffs.
3. Connect all your wiring per the diagram and pin table above (GPIO17 head servo, GPIO27 jaw servo, GPIO22/23 eyes, GPIO24 knock, GPIO5/6 HC-SR04).
4. **Power split — this is the step people most often get wrong:**
   - The Pi Zero 2 W gets its own 5V 2.5A supply into its **PWR** micro-USB port (the one closest to the middle of the board, not the one nearer the HDMI-less end — check silkscreen labels).
   - The two servos get power from the **separate** 6V battery pack or wall adapter — never from the Pi's 5V rail. MG996R servos can draw well over an amp each under load; the Pi cannot supply that safely.
   - **Tie the grounds together**: run a wire from the servo power supply's ground/negative to any GPIO ground pin on the Pi. Without this shared ground, your PWM signals won't have a stable reference and servo motion will be erratic.
5. Mount the enclosure inside the ribcage, with the GPIO slot facing where your servo/LED/sensor wiring runs.

---

## Part 3 — Software setup

### 3.1 Flash the OS

1. Download **Raspberry Pi Imager** (free, from raspberrypi.com/software) on your regular computer.
2. Insert the microSD card.
3. In Imager, choose **Raspberry Pi OS Lite (64-bit)** — you don't need the desktop environment, and Lite leaves more RAM free for your code.
4. Click the gear icon (⚙) before writing: set your hostname, enable SSH, set a username/password, and pre-configure your Wi-Fi credentials. This lets you boot the Zero 2 W headless — no monitor/keyboard needed.
5. Write the image, then boot the Pi with the SD card inserted.

### 3.2 First boot and enabling the camera

```bash
ssh yourusername@yourhostname.local
sudo raspi-config
```

In `raspi-config`:
- **Interface Options → Camera → Enable**
- **System Options → Audio → select the USB audio device** as the output
- Reboot when prompted.

### 3.3 Install system dependencies

```bash
sudo apt update
sudo apt install -y python3-venv portaudio19-dev python3-pyaudio espeak libespeak1 pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### 3.4 Get the code onto the Pi and install Python packages

Copy the `skeleton_pi0/` project folder onto the Pi (via `scp`, a USB
drive, or `git clone` if you've pushed it to a repo), then:

```bash
cd skeleton_pi0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This installs opencv-python, numpy, picamera2, gpiozero, pigpio,
sounddevice, simpleaudio, playsound, and pyttsx3.

### 3.5 Add your audio lines

Place WAV/MP3 files under `assets/audio/` matching the filenames listed in
`config.py`'s `AudioLineConfig` — e.g. `assets/audio/host_greeting_01.wav`.
Record these yourself, or edit the filenames in `config.py` to match
whatever clips you already have.

### 3.6 Run it

```bash
python main.py --test     # mock-hardware smoke test — confirms the code runs at all
python main.py            # live run with real camera/servos/sensors
```

---

## Part 4 — 3D printed parts

All five files are plain-text **OpenSCAD** source (`.scad`), not binary
STL — this is deliberate: OpenSCAD is free, and having the source means
you can tweak a single number (a servo dimension, a socket diameter) and
re-render, instead of hand-editing a mesh.

**To turn these into files your printer's slicer understands:**
1. Install OpenSCAD (openscad.org — free, all platforms).
2. Open each `.scad` file.
3. Press **F5** to preview, **F6** to fully render.
4. **File → Export → Export as STL.**
5. Open the resulting `.stl` in your slicer (PrusaSlicer, Cura, whatever came with your printer) as usual.

| File | What it makes | Filament note |
|---|---|---|
| `head_servo_mount.scad` | Spine clamp + servo platform + neck-rod collar | Standard PLA |
| `jaw_linkage_arm.scad` | Servo-horn-to-jaw-pivot linkage | **100% infill** — this part takes repeated stress |
| `eye_socket_camera_mount.scad` | Snap-fit ring holding the camera in one eye socket | Standard PLA |
| `eye_led_diffuser.scad` | Glowing dome for the LED eye | **Translucent/natural PLA only** |
| `electronics_enclosure.scad` | Ventilated box for the Pi Zero 2 W | Standard PLA/PETG |

**Before rendering, open each file and check the parameter block at the
top** — servo dimensions, rod diameters, and socket sizes are variables
you should measure against your own parts, not assume match mine exactly.

### No 3D printer?

Every part has a low-tech substitute:
- **Head servo mount**: a metal servo bracket (sold for hobby servos, ~$5) zip-tied to the spine rod, with the neck dowel epoxied directly to the servo horn.
- **Jaw linkage**: a straight servo horn extension arm (comes with most servos) bent/drilled to reach the jaw pivot.
- **Camera mount**: hot glue and patience — friction-fit the camera board directly into the eye socket.
- **LED diffuser**: a ping-pong ball half, sanded from the inside, hot-glued into the socket.
- **Electronics enclosure**: any small plastic project box with holes drilled for cable pass-through.

---

## Part 5 — Testing sequence

1. `python main.py --test` — confirms the state machine and mode-switching logic all pass, and tells you (in the log output) which backends — real or mock — got selected for each module. If it says "mock" for something you've wired up, that's your first debugging clue.
2. Power on and confirm `raspistill`/the camera preview works before trusting `main.py`'s face tracking.
3. Confirm head tracking follows a face smoothly in Host mode. If it's jittery, increase `tracking_smoothing_host` in `config.py` (lower = smoother).
4. Confirm jaw sync reacts to speech/noise.
5. Confirm eye glow and, separately, camera image quality in your actual lighting conditions (Halloween decorating is usually dim — you may need to lower `detection_min_neighbors` in `VisionConfig` for reliable detection in low light).
6. Trigger Trickster mode three ways — loud noise, knock, close proximity — confirming each independently.
7. Confirm auto-revert to Host after ~20 seconds of quiet.
8. Confirm both pre-recorded lines and TTS play through the speaker.
9. Let the full loop run for at least 30 minutes and watch for slowdown — this is the step that catches Zero-2-W-specific performance issues a quick test won't.

---

## Part 6 — Optional enhancements

- Fog machine triggered by proximity (add a relay + fog machine, hook into `behavior.py`'s `_check_triggers`)
- A second HC-SR04 or a PIR sensor for wider approach detection
- Swap in a Pi 4/5 later — none of your wiring or GPIO pin numbers change, only bump the resolution back up in `config.py`
- Face *recognition* (not just detection) — swap the Haar cascade in `vision.py` for `face_recognition` (dlib-based) if you want it to react differently to specific known faces vs. strangers; note this is meaningfully heavier on the Zero 2 W's CPU
