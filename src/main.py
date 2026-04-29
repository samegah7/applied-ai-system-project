"""
Music Recommender — main CLI runner.

Pipeline for each profile:
  1. Load songs from data/songs.csv
  2. Score every song against the user profile (retrieval layer 1)
  3. Retrieve genre and mood docs from docs/ (retrieval layer 2)
  4. Generate a grounded recommendation paragraph with Claude (generation layer)
  5. Validate the response automatically (grounding + hallucination + length checks)
  6. Print Claude's recommendation as the primary output, with scoring breakdown below
"""

import sys

from .recommender import load_songs, recommend_songs
from .rag import generate_recommendation
from .validator import validate_response, format_report
from .logger import logger


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

CONFLICTING_ENERGY_MOOD = {
    "name": "Adversarial — High Energy + Chill Mood",
    "genre": "lofi",
    "mood": "chill",
    "energy": 0.9,
}

UNKNOWN_GENRE = {
    "name": "Adversarial — Unknown Genre (country)",
    "genre": "country",
    "mood": "happy",
    "energy": 0.7,
}

ZERO_ENERGY = {
    "name": "Adversarial — Extreme Low Energy",
    "genre": "ambient",
    "mood": "chill",
    "energy": 0.0,
}

PROFILES = [
    HIGH_ENERGY_POP,
    CHILL_LOFI,
    DEEP_INTENSE_ROCK,
    CONFLICTING_ENERGY_MOOD,
    UNKNOWN_GENRE,
    ZERO_ENERGY,
]


def _divider(char: str = "═", width: int = 60) -> str:
    return char * width


def print_results(
    user_prefs: dict,
    recommendations: list,
    ai_response: str,
    validation: dict,
) -> None:
    name = user_prefs.get("name", "Unnamed Profile")

    print("\n" + _divider())
    print(f"  Profile : {name}")
    print(f"  genre={user_prefs['genre']}  mood={user_prefs['mood']}  energy={user_prefs['energy']}")
    print(_divider())

    # Claude's response is the primary recommendation output
    print("\n  AI Recommendation")
    print("  " + "-" * 40)
    for line in ai_response.splitlines():
        print(f"  {line}")

    # Scoring breakdown is secondary — shows how retrieval ranked the songs
    print("\n  Scoring Breakdown (retrieval ranking)")
    print("  " + "-" * 40)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"  #{rank}  {song['title']} by {song['artist']}")
        print(f"       {song['genre']} | {song['mood']} | energy {song['energy']}  →  score {score:.2f}")
        print(f"       {explanation}")

    print()
    print(format_report(validation))
    print(_divider())


def run_profile(user_prefs: dict, songs: list) -> None:
    name = user_prefs.get("name", "Unknown")
    logger.info(f"[{name}] Starting profile")

    # Layer 1 — score-based retrieval
    recommendations = recommend_songs(user_prefs, songs, k=5)

    # Augment each song dict with its score and reasons for the RAG prompt
    retrieved = [
        {**song, "score": score, "reasons": explanation}
        for song, score, explanation in recommendations
    ]

    # Layer 2 + Generation — doc retrieval + Claude
    ai_response = generate_recommendation(user_prefs, retrieved, profile_name=name)

    # Automated validation
    validation = validate_response(ai_response, retrieved, profile_name=name)

    print_results(user_prefs, recommendations, ai_response, validation)
    logger.info(f"[{name}] Done\n")


def main() -> None:
    try:
        songs = load_songs("data/songs.csv")
    except FileNotFoundError:
        logger.error("data/songs.csv not found. Run from the project root: python -m src.main")
        sys.exit(1)

    logger.info(f"Loaded {len(songs)} songs from data/songs.csv")

    for prefs in PROFILES:
        try:
            run_profile(prefs, songs)
        except EnvironmentError:
            # API key missing — already logged in rag.py; stop here
            sys.exit(1)
        except Exception as exc:
            logger.error(f"[{prefs.get('name')}] Unexpected error: {exc}")
            raise


if __name__ == "__main__":
    main()
