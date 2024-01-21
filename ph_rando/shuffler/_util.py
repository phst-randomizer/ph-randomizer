import random
import string


def generate_random_seed() -> str:
    # TODO: make this more robust
    return ''.join(random.choices(string.ascii_letters, k=20))
