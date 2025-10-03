from enum import Enum

from src.config import Paths


COMMON_NICHE = 'COMMON'

niches_data = {
    "bodybuilding": {
        "description": "Training focused on muscle hypertrophy and physique development.",
        "concepts": [
            "weight",
            "athlete",
            "nutrition",
            "supplement"
        ]
    },
    "motivation": {
        "description": "Content designed to inspire action and positive mindset.",
        "concepts": [
            "discipline",
            "self-employed",
            "constancy"
        ]
    },
    "mma": {
        "description": "Mixed Martial Arts combining striking and grappling disciplines.",
        "concepts": [
            "grappling",
            "box"
        ]
    },
    "boxing": {
        "description": "Combat sport focused on striking with fists.",
        "concepts": [
            "jab"
        ]
    },
    "self_defense": {
        "description": "Techniques and strategies for protecting oneself.",
        "concepts": [
            "defense",
            "defence"
        ]
    },
    "parkour": {
        "description": "Art of movement through urban environments using efficient techniques.",
        "concepts": [
            "building",
            "home",
            "athlete"
        ]
    },
    "skateboarding": {
        "description": "Sport involving tricks and maneuvers on a skateboard.",
        "concepts": [
            "skate",
            "skateboard"
        ]
    },
    "surfing": {
        "description": "Riding waves on a surfboard in the ocean.",
        "concepts": [
            "wave",
            "water sports"
        ]
    },
    "gymnastics": {
        "description": "Sport involving physical exercises requiring balance, strength, and coordination.",
        "concepts": [
            "gymnastics"
        ]
    },
    "camping": {
        "description": "Outdoor activity involving overnight stays in nature.",
        "concepts": [
            "tent",
            "camp",
            "camper"
        ]
    },
    "american football": {
        "description": "Team sport involving tactical plays to advance the ball.",
        "concepts": [
            "touchdown",
            "tackle",
            "defense"
        ]
    },
    "football": {
        "description": "Global team sport also known as soccer.",
        "concepts": [
            "goal",
            "pass",
            "dribble",
            "tackle",
            "offense (sports)",
            "football",
            "football field",
            "football pass",
            "football player",
            "football stadium",
            "football tackle"
        ]
    },
    "basketball": {
        "description": "Team sport involving shooting a ball into a hoop.",
        "concepts": [
            "dribble",
            "offense (sports)",
            "basket",
            "basketball",
            "basketball court",
            "basketball hoop",
            "basketball player"
        ]
    },
    "tennis": {
        "description": "Racquet sport played individually or in doubles.",
        "concepts": [
            "tennis",
            "tennis ball",
            "tennis match",
            "tennis player",
            "tennis racket"
        ]
    },
    "car_racing": {
        "description": "Motorsport involving competitive automobile racing.",
        "concepts": [
            "drift",
            "aerodynamic"
        ]
    },
    "motorcycle_stunts": {
        "description": "Performing tricks and stunts on motorcycles.",
        "concepts": [
            "wheelie",
            "ramp",
            "motorcycle sidecar",
            "motorcyclist"
        ]
    },
    "tech_unboxing": {
        "description": "Unpacking and showcasing the features of new technology products.",
        "concepts": [
            "toolbox",
            "box",
            "high-tech",
            "technology"
        ]
    },
    "pc_building": {
        "description": "Assembling personal computers with custom parts.",
        "concepts": [
            "cpu",
            "motherboard",
            "computer",
            "computer graphic",
            "computer network",
            "computer science",
            "computer simulation",
            "computerize",
            "computerized"
        ]
    },
    "coding": {
        "description": "Writing and debugging software using programming languages.",
        "concepts": [
            "python",
            "java",
            "algorithm",
            "conversion"
        ]
    },
    "editing": {
        "description": "Cutting, assembling, and enhancing video or audio content.",
        "concepts": [
            "footage",
            "high quality",
            "transition",
            "computer graphic",
            "video",
            "video recording",
            "videotape",
            "image",
            "smooth"
        ]
    },
    "video_game": {
        "description": "Electronic games played via consoles or PCs.",
        "concepts": [
            "video",
            "gameplan",
            "playtime",
            "strategy",
            "mission"
        ]
    },
    "beauty": {
        "description": "Content focusing on skincare, makeup, and aesthetic.",
        "concepts": [
            "aesthetic",
            "beautiful",
            "beautify",
            "beauty treatment",
            "dress",
            "dressage",
            "dressing room",
            "dressing table",
            "dressmaker",
            "make up"
        ]
    },
    "outfit_inspiration": {
        "description": "Showcasing fashion looks and styling ideas.",
        "concepts": [
            "natural law",
            "gallery",
            "caress",
            "stained glass"
        ]
    },
    "sneaker_reviews": {
        "description": "Evaluating sneakers for style, comfort, and performance.",
        "concepts": [
            "crawly",
            "loft store",
            "technology",
            "birthday present"
        ]
    },
    "music": {
        "description": "Content focused on audio production and performance.",
        "concepts": [
            "beat",
            "lyric",
            "instrument",
            "music",
            "music (auditory)",
            "musical chord",
            "musical composition",
            "musician"
        ]
    },
    "rap": {
        "description": "A genre of music characterized by rhythmic speech.",
        "concepts": [
            "rap",
            "drill",
            "freestyle",
            "beat",
            "music"
        ]
    },
    "animated_series": {
        "description": "Serialized content featuring animated characters and stories.",
        "concepts": [
            "series",
            "video"
        ]
    },
    "cosplay": {
        "description": "Dressing up as characters from fiction or pop culture.",
        "concepts": [
            "cumin seed",
            "stopper",
            "make up",
            "photo"
        ]
    },
    "reaction": {
        "description": "Videos showing creators reacting to other content.",
        "concepts": [
            "facial expression",
            "video",
            "video recording",
            "videotape",
            "surprise",
            "quiet"
        ]
    },
    "goofy_humor": {
        "description": "Silly and absurd style of comedy.",
        "concepts": [
            "humor",
            "physcially force",
            "fancy",
            "smirking",
            "smile"
        ]
    },
    "dark_humor": {
        "description": "Humor that explores grim or taboo topics.",
        "concepts": [
            "humor",
            "handicap",
            "black and white"
        ]
    },
    "pranks": {
        "description": "Deceptive tricks played for comedic effect.",
        "concepts": [
            "surprise",
            "upset",
            "reveal"
        ]
    },
    "news": {
        "description": "Reporting on current events and happenings.",
        "concepts": [
            "journal",
            "journalism",
            "journalist",
            "interview",
            "newsletter",
            "newspaper",
            "photojournalism",
            "photojournalist"
        ]
    },
    "politics": {
        "description": "Content related to governance, policies, and public affairs.",
        "concepts": [
            "election",
            "bill"
        ]
    },
    "astronomy": {
        "description": "Study of celestial bodies and the universe.",
        "concepts": [
            "space",
            "sun",
            "moon",
            "science",
            "spacecraft",
            "spaceship",
            "astrology",
            "astronaut",
            "astronomical observatory",
            "astronomy",
            "asymmetrical",
            "planet",
            "planet Neptune",
            "Jupiter",
            "planetarium",
            "telescope",
            "necleus (astronomy)"
        ]
    },
    "animal_documentaries": {
        "description": "Educational content about wildlife and ecosystems.",
        "concepts": [
            "animal",
            "giant animal",
            "predator",
            "predatory",
            "migration",
            "animal hoof"
        ]
    },
    "cute_animal_moments": {
        "description": "Clips of animals doing endearing things.",
        "concepts": [
            "animal hood",
            "filly",
            "cuddly"
        ]
    },
    "asmr": {
        "description": "Content designed to induce tingling relaxation through sound.",
        "concepts": [
            "sound",
            "whisper",
            "micro"
        ]
    },
    "meditation": {
        "description": "Practices for mental clarity and relaxation.",
        "concepts": [
            "breath",
            "breathe",
            "breathing",
            "breathtaking",
            "focus"
        ]
    },
    "travel": {
        "description": "Exploring new places, cultures, and adventures.",
        "concepts": [
            "itinerary",
            "backpack",
            "travel",
            "travel companion",
            "sightseeing"
        ]
    },
    "business": {
        "description": "Content on entrepreneurship, management, and finance.",
        "concepts": [
            "strategy",
            "amount",
            "amount of money",
            "business",
            "business card",
            "business suit",
            "businessperson"
        ]
    },
    "productivity": {
        "description": "Methods and tools for efficient work.",
        "concepts": [
            "management",
            "work"
        ]
    },
    "trend": {
        "description": "Content centered on current popular topics and challenges.",
        "concepts": [
            "popularity",
            "poplar",
            "famous",
            "trend",
            "trendy",
            "challenge",
            "meme"
        ]
    }
}

if COMMON_NICHE not in niches_data.keys():
    niches_data[COMMON_NICHE] = {
        "description": "Common niche",
        "concepts": []
    }

Niche: type[Enum] = Enum('Niche', {n.upper(): n.upper() for n in niches_data.keys()})