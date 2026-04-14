import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score a Song dataclass against a UserProfile and return (score, reasons)."""
        score = 0.0
        reasons = []

        if song.mood == user.favorite_mood:
            score += 2.0
            reasons.append("mood match (+2.0)")

        if song.genre == user.favorite_genre:
            score += 0.75
            reasons.append("genre match (+0.75)")

        energy_diff = abs(user.target_energy - song.energy)
        energy_score = round((1.0 - energy_diff) * 2.0, 2)
        score += energy_score
        reasons.append(f"energy closeness (+{energy_score})")

        if user.likes_acoustic and song.acousticness >= 0.6:
            score += 0.5
            reasons.append("acoustic preference (+0.5)")
        elif not user.likes_acoustic and song.acousticness < 0.4:
            score += 0.5
            reasons.append("non-acoustic preference (+0.5)")

        return round(score, 2), reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs sorted by descending score for the given user."""
        scored = [(song, self._score(user, song)[0]) for song in self.songs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language explanation of why this song was recommended."""
        _, reasons = self._score(user, song)
        return ", ".join(reasons) if reasons else "no strong match"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast to int/float."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a song against user prefs (+2 mood, +0.75 genre, +2 energy) and return (score, reasons)."""
    score = 0.0
    reasons = []

    # Mood match (+2.0) — highest weight: what you feel right now matters most
    if song.get("mood") == user_prefs.get("mood"):
        score += 2.0
        reasons.append(f"mood match (+2.0)")

    # Genre match (+0.75) — halved weight: genre is a weaker signal in this experiment
    if song.get("genre") == user_prefs.get("genre"):
        score += 0.75
        reasons.append(f"genre match (+0.75)")

    # Energy closeness — award up to +2.0 based on proximity (multiplier doubled)
    user_energy = user_prefs.get("energy")
    if user_energy is not None:
        energy_diff = abs(user_energy - song["energy"])
        energy_score = round((1.0 - energy_diff) * 2.0, 2)
        score += energy_score
        reasons.append(f"energy closeness (+{energy_score})")

    return round(score, 2), reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort by score descending, and return the top k as (song, score, explanation) tuples."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = ", ".join(reasons) if reasons else "no strong match"
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
