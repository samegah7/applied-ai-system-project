"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


# ── Standard user profiles ────────────────────────────────────────────────────

HIGH_ENERGY_POP = {
    "name": "High-Energy Pop",
    "genre": "pop",
    "mood": "happy",
    "energy": 0.9,
}

CHILL_LOFI = {
    "name": "Chill Lofi",
    "genre": "lofi",
    "mood": "chill",
    "energy": 0.35,
}

DEEP_INTENSE_ROCK = {
    "name": "Deep Intense Rock",
    "genre": "rock",
    "mood": "intense",
    "energy": 0.92,
}

# ── Adversarial / edge-case profiles ─────────────────────────────────────────
# Profiles designed to expose scoring surprises or weaknesses.

# Conflicting signals: asks for very high energy but a typically low-energy mood
CONFLICTING_ENERGY_MOOD = {
    "name": "Adversarial — High Energy + Sad/Chill Mood",
    "genre": "lofi",
    "mood": "chill",
    "energy": 0.9,
}

# Genre that does not exist in the catalog at all
UNKNOWN_GENRE = {
    "name": "Adversarial — Unknown Genre (country)",
    "genre": "country",
    "mood": "happy",
    "energy": 0.7,
}

# Extreme low energy — tests the floor of the energy scoring
ZERO_ENERGY = {
    "name": "Adversarial — Extreme Low Energy",
    "genre": "ambient",
    "mood": "chill",
    "energy": 0.0,
}

# All profiles to run
PROFILES = [
    HIGH_ENERGY_POP,
    CHILL_LOFI,
    DEEP_INTENSE_ROCK,
    CONFLICTING_ENERGY_MOOD,
    UNKNOWN_GENRE,
    ZERO_ENERGY,
]


def print_recommendations(user_prefs: dict, recommendations: list) -> None:
    name = user_prefs.get("name", "Unnamed Profile")
    print("\n" + "=" * 56)
    print(f"  Profile: {name}")
    print(f"  genre={user_prefs['genre']}  mood={user_prefs['mood']}  energy={user_prefs['energy']}")
    print("=" * 56)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']} by {song['artist']}")
        print(f"      Genre: {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']}")
        print(f"      Score:   {score:.2f}")
        print(f"      Why:     {explanation}")
    print("\n" + "=" * 56)


def main() -> None:
    songs = load_songs("data/songs.csv")

    for prefs in PROFILES:
        recommendations = recommend_songs(prefs, songs, k=5)
        print_recommendations(prefs, recommendations)


if __name__ == "__main__":
    main()
