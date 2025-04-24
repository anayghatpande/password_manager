import random
import pyperclip

adjectives = [
    "Quick", "Silent", "Brave", "Happy", "Clever", "Bright", "Red", "Blue", "Lone", "Fuzzy"
]

nouns = [
    "Tiger", "Falcon", "Rocket", "Wizard", "Phoenix", "Wolf", "Moon", "Ocean", "Cloud", "Ninja"
]

symbols = ['@', '#', '$', '&', '*']

def generate_password() -> str:
    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    number = random.randint(10, 99)
    symbol = random.choice(symbols)
    password = f"{adj}{number}{symbol}{noun}"
    pyperclip.copy(password)
    return password
