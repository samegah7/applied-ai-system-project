from pathlib import Path

import streamlit as st

from src.recommender import load_songs, recommend_songs
from src.rag import generate_recommendation
from src.validator import validate_response, confidence_score

_ROOT = Path(__file__).parent
_CSV = str(_ROOT / "data" / "songs.csv")

GENRES = ["lofi", "pop", "country", "r&b", "hip-hop", "edm",
          "rock", "ambient", "jazz", "synthwave", "indie pop"]
MOODS = ["chill", "happy", "intense", "relaxed", "moody", "focused"]

st.set_page_config(page_title="MoodMatch", layout="centered")


@st.cache_resource
def _songs():
    return load_songs(_CSV)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Your taste profile")
    genre = st.selectbox("Genre", GENRES)
    mood = st.selectbox("Mood", MOODS)
    energy = st.slider(
        "Energy level", 0.0, 1.0, 0.5, step=0.05,
        help="0 = extremely mellow  ·  1 = maximum intensity",
    )
    likes_acoustic = st.checkbox("Prefers acoustic")
    run = st.button("Get Recommendation", type="primary", use_container_width=True)

# ── Main ──────────────────────────────────────────────────────────────────────

st.title("MoodMatch")
st.caption("Content-based music recommendations · RAG pipeline · automated validation")

if not run:
    st.info("Set your taste profile in the sidebar and click **Get Recommendation**.")
    st.stop()

user_prefs = {
    "name": f"{genre}/{mood}",
    "genre": genre,
    "mood": mood,
    "energy": energy,
    "likes_acoustic": likes_acoustic,
}

with st.spinner("Retrieving songs and generating recommendation…"):
    try:
        recommendations = recommend_songs(user_prefs, _songs(), k=5)
        retrieved = [
            {**song, "score": score, "reasons": explanation}
            for song, score, explanation in recommendations
        ]
        ai_response = generate_recommendation(
            user_prefs, retrieved, profile_name=user_prefs["name"]
        )
    except EnvironmentError:
        st.error(
            "**ANTHROPIC_API_KEY is not set.**\n\n"
            "Run `export ANTHROPIC_API_KEY=your_key` in the terminal, then restart Streamlit."
        )
        st.stop()

validation = validate_response(ai_response, retrieved, profile_name=user_prefs["name"])
conf = confidence_score(validation)

# AI recommendation
st.subheader("AI Recommendation")
st.write(ai_response)

st.divider()

# Validation result
if validation["passed"]:
    mentioned = ", ".join(validation["songs_mentioned"]) or "none"
    st.success(
        f"**Validation PASSED** · confidence {conf:.2f}  \n"
        f"Songs mentioned: {mentioned}"
    )
else:
    issues = []
    if not validation["grounded"]:
        issues.append("not grounded — no retrieved songs mentioned")
    if validation["potential_hallucinations"]:
        issues.append(f"possible hallucinations: {validation['potential_hallucinations']}")
    if not validation["reasonable_length"]:
        issues.append(f"unusual length ({validation['word_count']} words)")
    st.error(
        f"**Validation FAILED** · confidence {conf:.2f}  \n"
        + " · ".join(issues)
    )

st.divider()

# Scoring breakdown
with st.expander("Scoring Breakdown — how retrieval ranked the songs"):
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**#{rank}  {song['title']}** by {song['artist']}")
            st.caption(f"{song['genre']} · {song['mood']} · energy {song['energy']}")
            st.caption(explanation)
        with right:
            st.metric("Score", f"{score:.2f}")
        if rank < len(recommendations):
            st.divider()
