"""enum_mapper.py — map free-text model outputs to allowed enum values."""

ISSUE_TYPE_MAP: dict[str, str] = {
    # dent
    "dent": "dent", "dented": "dent", "denting": "dent",
    "deformation": "dent", "deformed": "dent", "indentation": "dent",
    "bump": "dent", "ding": "dent",
    # scratch
    "scratch": "scratch", "scratched": "scratch", "scratching": "scratch",
    "scrape": "scratch", "scraped": "scratch", "mark": "scratch",
    "scuff": "scratch", "scuffed": "scratch", "surface mark": "scratch",
    # crack
    "crack": "crack", "cracked": "crack", "cracking": "crack",
    "fracture": "crack", "fractured": "crack", "hairline crack": "crack",
    "split": "crack", "fissure": "crack", "cracked screen": "crack",
    "broken display": "crack", "shattered screen": "glass_shatter",
    # glass_shatter
    "glass_shatter": "glass_shatter", "shattered": "glass_shatter",
    "shattered glass": "glass_shatter", "smashed glass": "glass_shatter",
    "glass broken": "glass_shatter",
    # broken_part
    "broken": "broken_part", "broken_part": "broken_part",
    "broken part": "broken_part", "snapped": "broken_part",
    "snapped off": "broken_part", "detached": "broken_part",
    "broke off": "broken_part", "fallen off": "broken_part",
    # missing_part
    "missing": "missing_part", "missing_part": "missing_part",
    "missing part": "missing_part", "not there": "missing_part",
    "gone": "missing_part", "absent": "missing_part",
    # torn_packaging
    "torn": "torn_packaging", "torn_packaging": "torn_packaging",
    "torn packaging": "torn_packaging", "ripped": "torn_packaging",
    "ripped open": "torn_packaging", "opened": "torn_packaging",
    "open": "torn_packaging", "tear": "torn_packaging",
    # crushed_packaging
    "crushed": "crushed_packaging", "crushed_packaging": "crushed_packaging",
    "crushed packaging": "crushed_packaging", "squashed": "crushed_packaging",
    "flattened": "crushed_packaging", "collapsed": "crushed_packaging",
    "caved in": "crushed_packaging", "dented box": "crushed_packaging",
    # water_damage
    "water_damage": "water_damage", "water damage": "water_damage",
    "wet": "water_damage", "soaked": "water_damage",
    "moisture": "water_damage", "water stain": "water_damage",
    "rain damage": "water_damage", "flood damage": "water_damage",
    # stain
    "stain": "stain", "stained": "stain", "staining": "stain",
    "liquid stain": "stain", "spill": "stain", "spilled": "stain",
    "discoloration": "stain", "discoloured": "stain",
    # none / unknown
    "none": "none", "no damage": "none", "no issue": "none",
    "unknown": "unknown", "unclear": "unknown", "unsure": "unknown",
}

CAR_PART_MAP: dict[str, str] = {
    "front_bumper": "front_bumper", "front bumper": "front_bumper",
    "bumper front": "front_bumper", "front": "front_bumper",
    "rear_bumper": "rear_bumper", "rear bumper": "rear_bumper",
    "back bumper": "rear_bumper", "rear": "rear_bumper",
    "back": "rear_bumper",
    "door": "door", "car door": "door", "door panel": "door",
    "hood": "hood", "bonnet": "hood",
    "windshield": "windshield", "windscreen": "windshield",
    "front glass": "windshield", "front windshield": "windshield",
    "side_mirror": "side_mirror", "side mirror": "side_mirror",
    "wing mirror": "side_mirror", "mirror": "side_mirror",
    "headlight": "headlight", "head light": "headlight",
    "front light": "headlight", "headlamp": "headlight",
    "taillight": "taillight", "tail light": "taillight",
    "rear light": "taillight", "brake light": "taillight",
    "fender": "fender", "wing": "fender",
    "quarter_panel": "quarter_panel", "quarter panel": "quarter_panel",
    "body": "body", "car body": "body", "panel": "body",
    "unknown": "unknown",
}

LAPTOP_PART_MAP: dict[str, str] = {
    "screen": "screen", "display": "screen", "lcd": "screen",
    "monitor": "screen", "laptop screen": "screen",
    "keyboard": "keyboard", "keys": "keyboard", "keypad": "keyboard",
    "trackpad": "trackpad", "touchpad": "trackpad", "track pad": "trackpad",
    "hinge": "hinge", "laptop hinge": "hinge",
    "lid": "lid", "top cover": "lid", "laptop lid": "lid",
    "cover": "lid",
    "corner": "corner", "laptop corner": "corner", "edge": "corner",
    "port": "port", "usb port": "port", "charging port": "port",
    "hdmi port": "port", "ports": "port",
    "base": "base", "bottom": "base", "underside": "base",
    "body": "body", "laptop body": "body", "chassis": "body",
    "unknown": "unknown",
}

PACKAGE_PART_MAP: dict[str, str] = {
    "box": "box", "package": "box", "carton": "box",
    "package_corner": "package_corner", "package corner": "package_corner",
    "corner": "package_corner", "box corner": "package_corner",
    "package_side": "package_side", "package side": "package_side",
    "side": "package_side", "box side": "package_side",
    "seal": "seal", "tape": "seal", "flap": "seal",
    "sealed area": "seal", "packaging seal": "seal",
    "label": "label", "shipping label": "label", "sticker": "label",
    "contents": "contents", "inside": "contents", "interior": "contents",
    "inner": "contents",
    "item": "item", "product": "item", "object": "item",
    "unknown": "unknown",
}

OBJECT_PART_MAPS: dict[str, dict[str, str]] = {
    "car": CAR_PART_MAP,
    "laptop": LAPTOP_PART_MAP,
    "package": PACKAGE_PART_MAP,
}

SEVERITY_MAP: dict[str, str] = {
    "none": "none", "no damage": "none", "undamaged": "none",
    "low": "low", "minor": "low", "light": "low", "slight": "low",
    "cosmetic": "low", "superficial": "low", "small": "low",
    "medium": "medium", "moderate": "medium", "significant": "medium",
    "medium severity": "medium", "noticeable": "medium",
    "high": "high", "severe": "high", "major": "high",
    "serious": "high", "critical": "high", "extreme": "high",
    "heavy": "high", "bad": "high",
    "unknown": "unknown", "unclear": "unknown", "unsure": "unknown",
}


def map_issue_type(raw: str) -> str:
    """Map raw model text to an allowed issue_type value."""
    key = raw.lower().strip()
    return ISSUE_TYPE_MAP.get(key, "unknown")


def map_object_part(raw: str, claim_object: str) -> str:
    """Map raw model text to an allowed object_part for the given object."""
    key = raw.lower().strip()
    part_map = OBJECT_PART_MAPS.get(claim_object, {})
    return part_map.get(key, "unknown")


def map_severity(raw: str) -> str:
    """Map raw model text to an allowed severity value."""
    key = raw.lower().strip()
    return SEVERITY_MAP.get(key, "unknown")