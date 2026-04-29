"""
Test suite for MoodMatch.

Coverage:
  - Scoring formula (score_song): perfect match, no match, weight ordering
  - Real catalog (load_songs + recommend_songs): expected #1 song per profile,
    k-result count, unknown-genre fallback behavior
  - Recommender class (OOP): sort order, explanation string
  - Validator: grounding, hallucination detection, length flag, confidence score
  - Doc loading: known genre resolves, unknown genre returns None
"""

import pytest
from pathlib import Path

from src.recommender import Song, UserProfile, Recommender, load_songs, recommend_songs, score_song
from src.validator import validate_response, confidence_score, check_consistency
from src.rag import _load_doc

CATALOG_PATH = "data/songs.csv"

# ── Shared fixtures ───────────────────────────────────────────────────────────

def make_small_recommender() -> Recommender:
    songs = [
        Song(id=1, title="Test Pop Track", artist="Test Artist", genre="pop",
             mood="happy", energy=0.8, tempo_bpm=120, valence=0.9,
             danceability=0.8, acousticness=0.2),
        Song(id=2, title="Chill Lofi Loop", artist="Test Artist", genre="lofi",
             mood="chill", energy=0.4, tempo_bpm=80, valence=0.6,
             danceability=0.5, acousticness=0.9),
    ]
    return Recommender(songs)


SAMPLE_RETRIEVED = [
    {"title": "Library Rain", "artist": "Paper Lanterns", "genre": "lofi",
     "mood": "chill", "energy": 0.35, "score": 4.75, "reasons": "mood match, genre match"},
    {"title": "Midnight Coding", "artist": "LoRoom", "genre": "lofi",
     "mood": "chill", "energy": 0.42, "score": 4.61, "reasons": "mood match, genre match"},
]


# ── OOP Recommender (original tests, kept) ───────────────────────────────────

def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)
    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ── score_song formula tests ──────────────────────────────────────────────────

def test_score_song_perfect_match():
    """All three signals match exactly: mood(+2.0) + genre(+0.75) + energy(+2.0) = 4.75."""
    user = {"genre": "lofi", "mood": "chill", "energy": 0.5}
    song = {"genre": "lofi", "mood": "chill", "energy": 0.5, "acousticness": 0.3}
    score, reasons = score_song(user, song)
    assert score == pytest.approx(4.75, abs=0.01)
    reason_text = " ".join(reasons)
    assert "mood match" in reason_text
    assert "genre match" in reason_text
    assert "energy closeness" in reason_text


def test_score_song_no_match():
    """No mood or genre match; only a partial energy proximity score."""
    user = {"genre": "rock", "mood": "intense", "energy": 0.9}
    song = {"genre": "lofi", "mood": "chill", "energy": 0.2, "acousticness": 0.3}
    score, reasons = score_song(user, song)
    # (1 - |0.9 - 0.2|) * 2 = (1 - 0.7) * 2 = 0.6
    assert score == pytest.approx(0.6, abs=0.01)
    assert len(reasons) == 1


def test_score_song_mood_weight_exceeds_genre_weight():
    """Mood match (+2.0) outweighs genre match (+0.75) at equal energy."""
    user = {"genre": "rock", "mood": "happy", "energy": 0.5}
    song_mood_match  = {"genre": "pop",  "mood": "happy",   "energy": 0.5, "acousticness": 0.3}
    song_genre_match = {"genre": "rock", "mood": "intense", "energy": 0.5, "acousticness": 0.3}
    score_mood,  _ = score_song(user, song_mood_match)
    score_genre, _ = score_song(user, song_genre_match)
    assert score_mood > score_genre


# ── Real catalog tests ────────────────────────────────────────────────────────

def test_chill_lofi_top_song_is_library_rain():
    """Chill lofi at energy 0.35 should surface Library Rain (perfect energy + mood + genre)."""
    songs = load_songs(CATALOG_PATH)
    results = recommend_songs({"genre": "lofi", "mood": "chill", "energy": 0.35}, songs, k=5)
    assert results[0][0]["title"] == "Library Rain"


def test_intense_rock_top_song_is_storm_runner():
    """Intense rock at energy 0.92 should surface Storm Runner (only rock + intense song)."""
    songs = load_songs(CATALOG_PATH)
    results = recommend_songs({"genre": "rock", "mood": "intense", "energy": 0.92}, songs, k=5)
    assert results[0][0]["title"] == "Storm Runner"


def test_zero_energy_top_song_is_spacewalk_thoughts():
    """Ambient chill at energy 0.0 should surface Spacewalk Thoughts (lowest energy + genre + mood)."""
    songs = load_songs(CATALOG_PATH)
    results = recommend_songs({"genre": "ambient", "mood": "chill", "energy": 0.0}, songs, k=5)
    assert results[0][0]["title"] == "Spacewalk Thoughts"


def test_recommend_returns_exact_k_results():
    """recommend_songs should return exactly k items for k in 1, 3, 5."""
    songs = load_songs(CATALOG_PATH)
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    for k in [1, 3, 5]:
        assert len(recommend_songs(prefs, songs, k=k)) == k


def test_unknown_genre_returns_no_genre_match():
    """A genre absent from the catalog should never produce a genre match bonus."""
    songs = load_songs(CATALOG_PATH)
    results = recommend_songs({"genre": "classical", "mood": "relaxed", "energy": 0.3}, songs, k=5)
    assert len(results) == 5
    for _, _, explanation in results:
        assert "genre match" not in explanation


# ── Validator tests ───────────────────────────────────────────────────────────

def test_validator_passes_on_grounded_response():
    response = (
        "Library Rain is the perfect pick for a chill lo-fi session. "
        "At energy 0.35 it sits exactly where you want it, and Midnight Coding "
        "is a close second with a similarly relaxed lo-fi texture."
    )
    report = validate_response(response, SAMPLE_RETRIEVED, profile_name="Test")
    assert report["grounded"] is True
    assert report["passed"] is True


def test_validator_fails_on_ungrounded_response():
    response = "I recommend some nice music for you to enjoy this afternoon."
    report = validate_response(response, SAMPLE_RETRIEVED, profile_name="Test")
    assert report["grounded"] is False
    assert report["passed"] is False


def test_validator_detects_hallucinated_title():
    response = 'For chill vibes I suggest "Phantom Drift" by Unknown Artist, it fits perfectly.'
    report = validate_response(response, SAMPLE_RETRIEVED, profile_name="Test")
    assert "Phantom Drift" in report["potential_hallucinations"]


def test_validator_flags_too_short_response():
    report = validate_response("Listen to this.", SAMPLE_RETRIEVED, profile_name="Test")
    assert report["reasonable_length"] is False


# ── Confidence score tests ────────────────────────────────────────────────────

def test_confidence_score_is_1_when_all_checks_pass():
    response = (
        "Library Rain is the ideal pick here. At energy 0.35 it matches your target "
        "exactly, and Midnight Coding follows closely with a similar lo-fi texture "
        "that keeps the chill mood intact throughout."
    )
    report = validate_response(response, SAMPLE_RETRIEVED, profile_name="Test")
    assert confidence_score(report) == 1.0


def test_confidence_score_is_partial_when_not_grounded():
    response = "Some nice music for you to enjoy."
    report = validate_response(response, SAMPLE_RETRIEVED, profile_name="Test")
    score = confidence_score(report)
    # No grounding (-0.50), short response (-0.20), no hallucinations (+0.30) = 0.30
    assert score == pytest.approx(0.30, abs=0.01)


# ── Doc loading tests ─────────────────────────────────────────────────────────

def test_doc_loads_for_known_genre():
    content = _load_doc("genres", "lofi")
    assert content is not None
    assert len(content) > 50


def test_doc_loads_for_known_mood():
    content = _load_doc("moods", "chill")
    assert content is not None
    assert len(content) > 50


def test_doc_returns_none_for_unknown_genre():
    content = _load_doc("genres", "metal")
    assert content is None
