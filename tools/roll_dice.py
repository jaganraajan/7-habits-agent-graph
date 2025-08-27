import random
from langchain_core.tools import tool

@tool
def roll_dice(sides: int = 6) -> int:
    """
    Roll a dice and return a random number between 1 and the given number of sides.
    """
    return random.randint(1, sides)
