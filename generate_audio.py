"""
generate_audio.py

Batch-generates all skeleton voice lines via the ElevenLabs API and saves
them as MP3 files named to match your config.py event/guest keys.

Run this ONCE on your Windows machine (not on the Pi). Copy the resulting
audio/ folder onto the Pi afterward; audio.py just plays files by name,
no TTS happens on-device.

SETUP BEFORE RUNNING:
  1. pip install requests
  2. Set your API key as an environment variable (do NOT hardcode it):
       Windows PowerShell:  setx ELEVENLABS_API_KEY "your-key-here"
       (then reopen PowerShell so it takes effect)
  3. Fill in VOICE_ID below with the voice ID you copied from your Voice
     Library (already done for you in this version).
  4. Put this file in the same folder as your config.py, or adjust the
     import path below.

The script is resume-safe: it skips any file that already exists, so if
it stops partway (rate limit, network blip) you can just run it again.
"""

import os
import sys
import time
from pathlib import Path

import requests

# ── CONFIGURE THESE ─────────────────────────────────────────────────────
VOICE_ID = "zORJBZhiRRn4mwnx5CAb"  # single voice used for both HOST and TRICKSTER
KID_SAFE_VOICE_ID = VOICE_ID  # same voice for kid-safe lines too

MODEL_ID = "eleven_multilingual_v2"  # highest quality; swap to eleven_flash_v2_5 for faster/cheaper if quality is good enough
OUTPUT_DIR = Path("audio")
REQUEST_DELAY_SECONDS = 0.5  # small pause between calls to stay well under rate limits

# Since HOST and TRICKSTER share one voice, we lean on voice_settings to make
# them read a little differently: HOST is steadier/more deliberate,
# TRICKSTER is looser/more expressive. This is a modest effect, not a
# replacement for a second voice — adjust these numbers by ear once you
# hear the first batch.
VOICE_SETTINGS_FOR_STATE = {
    "HOST": {
        "stability": 0.65,       # steadier, more deliberate delivery
        "similarity_boost": 0.8,
        "style": 0.2,            # low style exaggeration — slow/raspy/theatrical reads better calm
    },
    "TRICKSTER": {
        "stability": 0.35,       # looser, more variation call-to-call
        "similarity_boost": 0.7,
        "style": 0.6,            # higher style exaggeration — more sarcastic/snappy energy
    },
}
# ─────────────────────────────────────────────────────────────────────────

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    sys.exit(
        "ERROR: ELEVENLABS_API_KEY environment variable is not set.\n"
        "Run: setx ELEVENLABS_API_KEY \"your-key-here\"  (then reopen PowerShell)"
    )

if "PASTE_" in VOICE_ID:
    sys.exit("ERROR: Fill in VOICE_ID at the top of this script first.")

# Import your line data from script_lines.py (kept separate from config.py
# on purpose, so this never touches your hardware/pin settings).
try:
    from script_lines import (
        GUEST_PROFILES,
        EVENT_LINES,
        KID_SAFE_LINES,
        UNKNOWN_GUEST_LINES,
        OPENING_MONOLOGUE,
        CLOSING_MONOLOGUE,
        IDLE_INTERJECTIONS,
    )
except ImportError as e:
    sys.exit(f"ERROR: Could not import line data from script_lines.py: {e}")

VOICE_FOR_STATE = {"HOST": VOICE_ID, "TRICKSTER": VOICE_ID}

total_chars = 0
total_calls = 0
skipped = 0


def tts_to_file(text: str, voice_id: str, out_path: Path, state: str = "HOST"):
    """Call the ElevenLabs API and save the result. Skips if file already exists."""
    global total_chars, total_calls, skipped

    if out_path.exists():
        skipped += 1
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS_FOR_STATE[state],
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        print(f"  ⚠ FAILED ({response.status_code}) for {out_path.name}: {response.text[:200]}")
        return

    out_path.write_bytes(response.content)
    total_chars += len(text)
    total_calls += 1
    print(f"  ✓ {out_path.name}  ({len(text)} chars)")
    time.sleep(REQUEST_DELAY_SECONDS)


def clean_text_for_tts(text: str) -> str:
    """Strip stage-direction-only lines (e.g. '[STAGE DIRECTION: ...]') — those aren't spoken."""
    return text.strip()


# ── MODULE 1 — Opening Monologue ───────────────────────────────────────
print("\n== Opening Monologue ==")
for i, line in enumerate(OPENING_MONOLOGUE, 1):
    if line["text"].startswith("["):
        continue
    voice = VOICE_FOR_STATE[line["state"]]
    out = OUTPUT_DIR / "opening" / f"opening_{i:02d}_{line['state'].lower()}.mp3"
    tts_to_file(clean_text_for_tts(line["text"]), voice, out, state=line["state"])

# ── MODULE 2 — Guest Recognition Lines ─────────────────────────────────
print("\n== Guest Recognition Lines ==")
for guest_key, profile in GUEST_PROFILES.items():
    for i, line in enumerate(profile["lines"], 1):
        if line["event"] == "NOTE_ONLY" or line["text"].startswith("["):
            continue  # skip flag notes and stage-direction-only entries
        voice = VOICE_FOR_STATE[line["state"]]
        out = OUTPUT_DIR / "guests" / guest_key / f"{guest_key}_{i:02d}_{line['state'].lower()}.mp3"
        tts_to_file(clean_text_for_tts(line["text"]), voice, out, state=line["state"])

# ── MODULE 4 — Event Trigger Lines ─────────────────────────────────────
print("\n== Event Trigger Lines ==")
for event_key, states in EVENT_LINES.items():
    for state, lines in states.items():
        voice = VOICE_FOR_STATE[state]
        for i, text in enumerate(lines, 1):
            out = OUTPUT_DIR / "events" / event_key.lower() / f"{event_key.lower()}_{state.lower()}_{i:02d}.mp3"
            tts_to_file(clean_text_for_tts(text), voice, out, state=state)

# ── MODULE 5 — Random Interjections ────────────────────────────────────
print("\n== Idle Interjections ==")
for i, line in enumerate(IDLE_INTERJECTIONS, 1):
    voice = VOICE_FOR_STATE[line["state"]]
    out = OUTPUT_DIR / "idle" / f"idle_{i:02d}_{line['state'].lower()}.mp3"
    tts_to_file(clean_text_for_tts(line["text"]), voice, out, state=line["state"])

# ── MODULE 6 — Unknown Guest Fallback ──────────────────────────────────
print("\n== Unknown Guest Fallback ==")
for state, lines in UNKNOWN_GUEST_LINES.items():
    voice = VOICE_FOR_STATE[state]
    for i, text in enumerate(lines, 1):
        out = OUTPUT_DIR / "unknown_guest" / f"unknown_{state.lower()}_{i:02d}.mp3"
        tts_to_file(clean_text_for_tts(text), voice, out, state=state)

# ── MODULE 7 — Kid-Safe Lines ──────────────────────────────────────────
print("\n== Kid-Safe Lines ==")
for kid_key, lines in KID_SAFE_LINES.items():
    for i, text in enumerate(lines, 1):
        out = OUTPUT_DIR / "kids" / f"{kid_key}_{i:02d}.mp3"
        tts_to_file(clean_text_for_tts(text), KID_SAFE_VOICE_ID, out, state="TRICKSTER")

# ── MODULE 8 — Closing Monologue ───────────────────────────────────────
print("\n== Closing Monologue ==")
for i, line in enumerate(CLOSING_MONOLOGUE, 1):
    voice = VOICE_FOR_STATE[line["state"]]
    out = OUTPUT_DIR / "closing" / f"closing_{i:02d}_{line['state'].lower()}.mp3"
    tts_to_file(clean_text_for_tts(line["text"]), voice, out, state=line["state"])

# ── SUMMARY ─────────────────────────────────────────────────────────────
print(f"\nDone. {total_calls} files generated, {skipped} already existed and were skipped.")
print(f"Total characters sent: {total_chars} (~{total_chars} credits on ElevenLabs' 1-credit-per-character pricing).")
print(f"Output saved to: {OUTPUT_DIR.resolve()}")
