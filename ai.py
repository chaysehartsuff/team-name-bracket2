import random


def get_name_submission() -> str:
    """
    Return a random, playful Rocket League club name.
    """
    names = [
        "Ballistic Bouncers",
        "Gutter Gloves",
        "Sonic Spheres",
        "Rim Rattlers",
        "Noggin Knockers",
        "Spiked Spheres",
        "Edge Ballers",
        "Tubular Tenders",
        "Bouncy Bruisers",
        "Barrel Rollers",
        "Rocket Rovers",
        "Nitro Nuggets",
        "Phantom Pounds",
        "Twisted Tops",
        "Orbital Offenders",
        "Psycho Pinchers",
        "Gravity Gropers",
        "Chaos Cannons",
        "Mega Mufflers",
        "Volley Vipers",
        "Ball Bazaar",
        "Sphere Sharks",
        "Clutch Crushers",
        "Maddening Midair",
        "Turbo Terrors",
        "Demolition Dodgers",
        "Flip Fury",
        "Shadow Shots",
        "Momentum Maniacs",
        "Slam Dribblers",
        "Boost Bandits",
        "Knockout Knockers",
        "Pinball Pandas",
        "Boost Bonkers",
        "Whiplash Wombats",
        "Rebound Rebels",
        "Turbo Torque",
        "Cannonball Kings",
        "Orbit Overlords",
        "Chaos Controllers",
    ]
    return random.choice(names)

# Example usage:
# from ai import get_name_submission
# club_name = get_name_submission()
# print(f"Your new Rocket League club: {club_name}")
