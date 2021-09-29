import random

def generate(digit=6) -> str:
    """One Time Passcode generator

    Args:
        digit (int): Number of degits. Default is 6.

    Returns:
        str: Return zero filled int string.
    """
    return f"{int(random.random() * pow(10, digit))}".zfill(digit)