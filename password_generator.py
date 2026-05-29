"""
Password Generator — creates memorable, secure passwords.
Pattern: Adjective + Number + Symbol + Noun
"""

import secrets

ADJECTIVES = [
    "Quick", "Brave", "Sharp", "Mighty", "Swift", "Bold", "Calm", "Cool",
    "Dark", "Bright", "Silent", "Clever", "Fierce", "Gentle", "Happy",
    "Jolly", "Kind", "Lively", "Lucky", "Noble", "Proud", "Royal", "Silly",
    "Smart", "Super", "Witty", "Ancient", "Cosmic", "Divine", "Epic",
    "Frozen", "Golden", "Hidden", "Jumbo", "Lunar", "Magic", "Neon",
    "Ocean", "Pearl", "Quiet", "Rapid", "Solar", "Tiny", "Ultra", "Vivid",
    "Wild", "Amber", "Bliss", "Crisp", "Dusk",
]

NOUNS = [
    "Falcon", "Tiger", "Eagle", "Lion", "Wolf", "Bear", "Hawk", "Owl",
    "Panda", "Koala", "Coral", "Storm", "Flame", "River", "Mountain",
    "Forest", "Ocean", "Planet", "Star", "Moon", "Cloud", "Thunder",
    "Dragon", "Phoenix", "Saber", "Blade", "Crystal", "Diamond", "Ember",
    "Feather", "Galaxy", "Horizon", "Island", "Jungle", "Knight", "Legend",
    "Meadow", "Nebula", "Orchid", "Python", "Raven", "Sphinx", "Temple",
    "Umbra", "Valley", "Willow", "Yonder", "Zephyr", "Anchor", "Breeze",
]

SYMBOLS = "!@#$%&*"


def generate_password() -> str:
    """Generate a password like 'Quick42$Falcon'"""
    adj = secrets.choice(ADJECTIVES)
    noun = secrets.choice(NOUNS)
    num = secrets.randbelow(90) + 10
    sym = secrets.choice(SYMBOLS)
    return f"{adj}{num}{sym}{noun}"

