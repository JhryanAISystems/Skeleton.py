"""
script_lines.py

All spoken-line data for the Vampire Ball skeleton — guest recognition
lines, event triggers, kid-safe lines, unknown-guest fallback, and the
opening/closing monologues.

This is kept SEPARATE from config.py (which holds your hardware/pin
settings) so generating audio never risks touching your working hardware
config. generate_audio.py imports from this file.
"""

OPENING_MONOLOGUE = [
    {"text": "Well, well. The gate creaks open, and look what wandered in.",
     "state": "HOST", "tone": "gentle", "event": "PARTY_OPEN"},
    {"text": "Welcome, welcome, to the Ryan family's second annual Vampire Ball.",
     "state": "HOST", "tone": "gentle", "event": "PARTY_OPEN"},
    {"text": "I've been waiting here in the dark. Patiently. Politely.",
     "state": "HOST", "tone": "gentle", "event": "PARTY_OPEN"},
    {"text": "Come closer, if you dare — the punch is spiked and so am I.",
     "state": "HOST", "tone": "flirty", "event": "PARTY_OPEN"},
    {"text": "Oh, don't mind my posture, two hundred years of standing will do that to a spine.",
     "state": "TRICKSTER", "tone": "teasing", "event": "PARTY_OPEN"},
]

GUEST_PROFILES = {
    "joe": {
        "display_name": "Joseph (Joe)",
        "notes": "host, jumps easily, samosa/chai/snack jokes — keep it warmer, he's the creator",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "There's the man who built me. Careful, I know where you keep the samosas.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Welcome home, Joe. I promise not to jump out at— oh, too late, you flinched already.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Every wire in me, every joint, every joke — you built all of it, Joe. I don't say thank you enough for a guy with no vocal cords.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "karishma": {
        "display_name": "Karishma",
        "notes": "stressed lately, but game for some light roasting — keep it playful, not mean",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "Karishma. Still running on caffeine and sheer willpower, I see. Respect.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "You've got that 'I have four unread group chats and I'm ignoring all of them' energy tonight. Iconic.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Ah, Karishma. Even the dead could use a night off — you more than most.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "komal": {
        "display_name": "Komal",
        "notes": "Punjabi lines welcome, keep teasing light",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "Komal! Ki haal hai? Even bones like a good greeting.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Careful walking past me too fast, Komal — I've got two hundred years of patience and zero of it for being ignored.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "⚠ [flag: confirm any additional Punjabi phrasing directly with Komal or a fluent family member before recording — I kept this to one common, verified greeting rather than guessing further.]",
             "state": "HOST", "tone": "gentle", "event": "NOTE_ONLY"},
        ],
    },
    "kamna": {
        "display_name": "Kamna",
        "notes": "AI job jokes",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Kamna. The one person here whose job might actually get replaced by something like me.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Don't worry, I only run on a Raspberry Pi. Your job's safe for another year, at least.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Kamna's here. Somewhere, a spreadsheet just got automated.",
             "state": "TRICKSTER", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "manoj": {
        "display_name": "Manoj",
        "notes": "cigar jokes, teasing welcome",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Manoj! Bring a cigar for the dead man too, or don't come in at all.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "I don't need lungs to know that smells expensive, Manoj.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "There he is. The only man here classier than a skeleton in a bowtie.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "mina": {
        "display_name": "Mina",
        "notes": "flirty and friendly",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "Mina. If I still had a heartbeat, you'd hear it skip right now.",
             "state": "HOST", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "You clean up nicely for a party full of the dead, Mina.",
             "state": "TRICKSTER", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "Careful — charm like that could wake the dead. Oh wait.",
             "state": "TRICKSTER", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "skylar": {
        "display_name": "Skylar",
        "notes": "deadpan, teasing",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Skylar. Still unimpressed by everything. Respect.",
             "state": "TRICKSTER", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
            {"text": "You could survive a horror movie on that face alone, Skylar.",
             "state": "TRICKSTER", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
            {"text": "I tried a jumpscare face. You didn't blink. I respect that more than I can say.",
             "state": "TRICKSTER", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "angel": {
        "display_name": "Angel",
        "notes": "flirty, funny, fabulous",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Angel! Even the cobwebs are jealous of your outfit tonight.",
             "state": "TRICKSTER", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "You walked in and I swear my jaw dropped — well, more than usual.",
             "state": "TRICKSTER", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "Fabulous as always, Angel. I'd stand up for you if I weren't, you know, bolted down.",
             "state": "HOST", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "parth": {
        "display_name": "Parth",
        "notes": "polite — don't roast him, goad HIM into roasting others",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Parth. Too polite for your own good — I know you've got a roast loaded, let it out.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Everyone's heard you've got jokes, Parth. I'm just standing here giving you the opening.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Welcome, Parth. Manners like yours are almost as rare as my pulse — don't let them stop you tonight.",
             "state": "HOST", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "massi": {
        "display_name": "Massi",
        "notes": "Punjabi jokes, gentle teasing",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "Massi ji, aa jao — the party doesn't start until you're in the room.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Massi, don't pinch my cheek, I don't have one anymore.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "⚠ [flag: 'Massi ji' and 'aa jao' are common, verified terms of respect/invitation — confirm comfort level before adding more Punjabi lines.]",
             "state": "HOST", "tone": "gentle", "event": "NOTE_ONLY"},
        ],
    },
    "sue": {
        "display_name": "Sue (Joe's mom)",
        "notes": "flirty + sarcastic, keep it warm — not edgy",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "Sue! The only woman here who could scare me worse than a jump scare — in the best way.",
             "state": "HOST", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "Joe built me, but Sue built Joe. Respect where it's due.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Don't tell Joe I said this, but you're clearly the favorite in the family, Sue.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "liam": {
        "display_name": "Liam",
        "notes": "serious, no edgy jokes — keep it warm and simple",
        "personality_affinity": "HOST",
        "lines": [
            {"text": "Liam. Good to see you. Come in out of the cold.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Welcome, Liam. No tricks tonight, just a friendly skeleton and good company.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "There you are, Liam. Glad you made it.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "laura": {
        "display_name": "Laura",
        "notes": "giggly, cute, kid-safe teasing",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Laura! I heard your laugh three rooms away. Do it again.",
             "state": "TRICKSTER", "tone": "kid_safe", "event": "GUEST_RECOGNIZED"},
            {"text": "You giggle every time you see me. I'm choosing to take that as a compliment.",
             "state": "TRICKSTER", "tone": "kid_safe", "event": "GUEST_RECOGNIZED"},
            {"text": "Careful, Laura, keep smiling like that and you'll make even a skeleton blush.",
             "state": "HOST", "tone": "kid_safe", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "rachel": {
        "display_name": "Rachel",
        "notes": "flirty, mischievous — NOT creepy, keep it light and clearly a bit",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Rachel! Careful, that grin of yours is more dangerous than anything I've got.",
             "state": "TRICKSTER", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "You've got trouble written all over you tonight, Rachel — I like it.",
             "state": "TRICKSTER", "tone": "flirty", "event": "GUEST_RECOGNIZED"},
            {"text": "Don't start plotting with me, Rachel, my head only turns 90 degrees and I need it for dramatic effect.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "ricky": {
        "display_name": "Ricky",
        "notes": "sarcastic, quick-witted — mix of fart jokes, firefighter jokes, and personality roasting; keep the smoke alarm line as-is",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Ricky's here. Somewhere a smoke alarm just got nervous.",
             "state": "TRICKSTER", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
            {"text": "Careful near the candles, Ricky, we both know what you're capable of.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Somebody call the fire department, Ricky's within ten feet of an open flame again.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "I'd try to out-sarcasm you, Ricky, but I only have one tone of voice and it's already unsettling.",
             "state": "TRICKSTER", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "emron": {
        "display_name": "Emron",
        "notes": "gets legitimately spooked, deadpan reactions, light Afghan folklore reference — keep vague/respectful, don't invent specifics",
        "personality_affinity": "BOTH",
        "lines": [
            {"text": "Emron. Relax. I only come alive for guests who scream, and you're clearly too smart for that.",
             "state": "HOST", "tone": "deadpan", "event": "GUEST_RECOGNIZED"},
            {"text": "Your grandmother's stories about things that walk at night? I'm the polite version.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "⚠ [flag: kept the folklore reference deliberately vague — I don't have reliable detail on specific Afghan folklore to reference accurately. If Emron has a specific story he likes being teased about, tell me and I'll write it in properly rather than guessing.]",
             "state": "HOST", "tone": "gentle", "event": "NOTE_ONLY"},
        ],
    },
    "sam": {
        "display_name": "Sam",
        "notes": "Disney lover, always late, jokester, Halloween superfan",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Sam! Fashionably late, as always. I've been dead longer than you've kept people waiting tonight, and even I'm impressed.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "A fellow Halloween fanatic. Finally, someone who gets it.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Let me guess — you've already got next year's costume planned, Sam?",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "slim": {
        "display_name": "Talmer (Slim)",
        "notes": "beer jokes, safe teasing",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Slim! Bring the good stuff, I've got two hundred years of thirst to make up for.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "I don't have a liver, but I respect a man who takes his beer seriously.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "There's Slim. Grab a cold one, the party's officially started.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
        ],
    },
    "kirk": {
        "display_name": "Kirk",
        "notes": "regular butt of jokes at work; jumpscare is TTS (same voice as everything else) with a head-turn/eye-flare stage direction, not a recorded impression",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Well, well, well. Look who wandered within jumpscare range. Relax, Kirk — I only bite people who deserve it. You're borderline.",
             "state": "TRICKSTER", "tone": "teasing", "event": "JUMPSCARE_CUE",
             "stage_direction": "sudden head-turn + eye flare toward Kirk right before this line plays"},
            {"text": "Kirk! Relax, I only borrowed your voice for a second — someone at work already stole your whole personality.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "Was that a good Kirk impression? Be honest. I've had two hundred years to work on my delivery, you've had, what, one performance review cycle?",
             "state": "TRICKSTER", "tone": "teasing", "event": "JUMPSCARE_CUE_FOLLOWUP"},
        ],
    },
    "jules": {
        "display_name": "Jules",
        "notes": "thrifting jokes, childcare jokes",
        "personality_affinity": "TRICKSTER",
        "lines": [
            {"text": "Jules! Love the outfit — thrifted, I'm guessing? I respect a good bargain, even in the afterlife.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
            {"text": "You wrangle other people's kids all day and you still showed up smiling. Absolute legend.",
             "state": "HOST", "tone": "gentle", "event": "GUEST_RECOGNIZED"},
            {"text": "Jules found the one used bone in the house. Fitting.",
             "state": "TRICKSTER", "tone": "teasing", "event": "GUEST_RECOGNIZED"},
        ],
    },
}

TONE_SAMPLES = {
    "gentle":   {"HOST": ["Come, sit a while — no tricks here.", "You're always welcome at this door."],
                 "TRICKSTER": ["Even I take it easy on some nights.", "No scares for you tonight, promise."]},
    "deadpan":  {"HOST": ["I've seen scarier things in the mirror.", "Fascinating. Truly."],
                 "TRICKSTER": ["Wow. Riveting.", "I would gasp, but I don't have lungs."]},
    "flirty":   {"HOST": ["You didn't need to dress up, you already haunt my thoughts.", "Careful, that smile could raise the dead."],
                 "TRICKSTER": ["Be still my nonexistent heart.", "You're trouble, and I mean that as a compliment."]},
    "teasing":  {"HOST": ["Oh, I've heard about you.", "Behave, or I'll tell everyone what I know."],
                 "TRICKSTER": ["Oh, this is going to be fun.", "I've been saving a joke just for you."]},
    "kid_safe": {"HOST": ["Hello, little one! I'm a friendly skeleton.", "Don't be scared, I'm actually quite silly."],
                 "TRICKSTER": ["Boo! ...just kidding, want to see my wiggly fingers?", "I lost my nose. Have you seen it?"]},
}

EVENT_LINES = {
    "KNOCK_DETECTED": {
        "HOST": ["Ah, a knock. How refreshingly polite of you.",
                  "Come in, come in — the door was never really locked."],
        "TRICKSTER": ["Knock knock. Who's— oh wait, that's my line.",
                       "Someone's eager. I like that."],
    },
    "LOUD_NOISE": {
        "HOST": ["Goodness. Someone's having a good time.",
                  "That noise nearly rattled my bones loose."],
        "TRICKSTER": ["Whoa! Save some chaos for the rest of us.",
                       "Was that a scream of terror or of joy? Hard to tell these days."],
    },
    "PERSON_JUMPED": {
        "HOST": ["There, there. I do have that effect on people.",
                  "No shame in a good jump — it means I'm doing my job."],
        "TRICKSTER": ["Ha! Got you. Worth every second of standing still.",
                       "Oh, that was a good one. I'll be replaying that all night."],
    },
    "LAUGH_DETECTED": {
        "HOST": ["Music to my ears — or wherever it is I hear from now.",
                  "Laughter suits this house. Keep it coming."],
        "TRICKSTER": ["That's the sound I was going for. Mission accomplished.",
                       "See? I'm funnier dead than most people are alive."],
    },
    "WAVE_DETECTED": {
        "HOST": ["Hello to you too. Manners noted and appreciated.",
                  "A friendly wave. Rare, but welcome."],
        "TRICKSTER": ["Oh, we're waving now? Watch this.",
                       "I'd wave back if my arms weren't full of dramatic flair."],
    },
    "GUEST_TOO_CLOSE": {
        "HOST": ["A little close, don't you think? I bruise easy. Well — I would, if I had skin.",
                  "Personal space, friend. Even skeletons have boundaries."],
        "TRICKSTER": ["Ooh, brave one. Or foolish. Bit of both, probably.",
                       "One more step and this becomes a whole different kind of party."],
    },
    "TOUCH_DETECTED": {
        "HOST": ["Careful now — I'm older than I look, and I look pretty old.",
                  "Gentle, please. These bones have seen better centuries."],
        "TRICKSTER": ["Ticklish! Wait, no. I have no nerve endings. Carry on.",
                       "You poked a skeleton. Bold choice."],
    },
    "KID_APPROACH": {
        "HOST": ["Well hello there, little one! Nothing scary here, just silly old bones.",
                  "Come say hi — I promise I'm friendlier than I look."],
        "TRICKSTER": ["Uh oh, a tiny human spotted me! Quick, act cool.",
                       "Boo! ...too much? Okay, let's just wiggle fingers instead."],
    },
}

IDLE_INTERJECTIONS = [
    {"text": "I do love a good party. Gives me something to do besides stand here.",
     "state": "HOST", "tone": "gentle", "event": "IDLE_INTERJECTION"},
    {"text": "Someone left snacks unattended near me. Bold strategy.",
     "state": "TRICKSTER", "tone": "teasing", "event": "IDLE_INTERJECTION"},
    {"text": "I ran the numbers — I'm the only one here who's technically unemployed and undead. Living the dream.",
     "state": "TRICKSTER", "tone": "deadpan", "event": "IDLE_INTERJECTION"},
    {"text": "Two hundred years and I still haven't figured out where I put my other hand.",
     "state": "TRICKSTER", "tone": "teasing", "event": "IDLE_INTERJECTION"},
    {"text": "It's a good crowd tonight. I can tell — my hollow chest has a certain resonance to it.",
     "state": "HOST", "tone": "gentle", "event": "IDLE_INTERJECTION"},
    {"text": "Psst. Don't look now, but I think that shadow moved on its own. ...Kidding. Probably.",
     "state": "TRICKSTER", "tone": "teasing", "event": "IDLE_INTERJECTION"},
]

UNKNOWN_GUEST_LINES = {
    "HOST": [
        "Well now, I don't believe we've met. Welcome all the same.",
        "A new face. How delightfully unexpected.",
        "I don't know your name yet, but the door's open regardless.",
    ],
    "TRICKSTER": [
        "Ooh, a stranger. Give me a minute, I'll come up with something good.",
        "New person! I promise my material gets better once I know your name.",
        "You're new. I like new. New people haven't heard my jokes yet.",
    ],
}

KID_SAFE_LINES = {
    "kushiya": ["Hi Kushiya! I'm a friendly skeleton, want to see my wiggly fingers?",
                "Kushiya! I lost my nose somewhere. Have you seen it?"],
    "avni":    ["Hello Avni! Don't be scared, I'm actually very silly.",
                "Avni! Wanna hear my favorite spooky-but-not-scary sound? Oooooo!"],
    "aaliyah": ["Hi Aaliyah! I only know friendly tricks tonight.",
                "Aaliyah! Did you know skeletons love dancing? Watch this wobble."],
    "ellie":   ["Hello Ellie! I'm the world's friendliest pile of bones.",
                "Ellie! Want to hear a joke? Why don't skeletons fight each other? They don't have the guts!"],
    "mia":     ["Hi Mia! Come closer, I promise I'm more silly than spooky.",
                "Mia! I'm missing a tooth. Or twelve. It's fine, really."],
    "_default": ["Hello, little one! I'm a friendly skeleton, not a scary one.",
                 "Hi there! Want to see my wiggly, silly dance?"],
}

CLOSING_MONOLOGUE = [
    {"text": "The candles are low, and even the dead need their rest.",
     "state": "HOST", "tone": "gentle", "event": "PARTY_CLOSE"},
    {"text": "Thank you for spending your evening with the restless and the ridiculous.",
     "state": "HOST", "tone": "gentle", "event": "PARTY_CLOSE"},
    {"text": "Go carefully into the night — the real monsters are all still inside, eating the last of the snacks.",
     "state": "HOST", "tone": "gentle", "event": "PARTY_CLOSE"},
    {"text": "Until next year's ball... unless, of course, I get bored and show up sooner.",
     "state": "TRICKSTER", "tone": "teasing", "event": "PARTY_CLOSE"},
]
