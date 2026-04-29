"""
RAG pipeline: retrieve genre/mood docs + retrieved songs, then generate
a grounded recommendation with the Claude API.

Retrieval layer 1 — scoring algorithm in recommender.py (top-k songs)
Retrieval layer 2 — local docs/ folder (genre and mood context)
Generation layer  — Claude API, with prompt caching on static instructions
"""

import os
from pathlib import Path
from typing import Optional

import anthropic

from .logger import logger

_DOCS_DIR = Path(__file__).parent.parent / "docs"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 350

# Cached at module level so the client is reused across calls
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Copy .env.example to .env and add your key, "
                "then run: export ANTHROPIC_API_KEY=your_key"
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _load_doc(category: str, name: str) -> Optional[str]:
    filename = (
        name.lower()
        .replace(" ", "_")
        .replace("&", "_and_")
        .replace("-", "_")
    )
    path = _DOCS_DIR / category / f"{filename}.md"
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        logger.debug(f"Loaded doc: {path.name}")
        return content
    logger.warning(f"No doc found for {category}/{name!r} — continuing without it")
    return None


_BASE_INSTRUCTIONS = """\
You are a music recommendation assistant built into an educational project.

Your job is to explain a set of pre-ranked song recommendations to the user in \
natural, conversational language. You will receive:
  1. The user's taste profile (genre, mood, energy level)
  2. The top songs chosen by a scoring algorithm, with their scores and match reasons
  3. Context documents describing the user's preferred genre and mood

Rules you must follow:
- Only mention songs from the provided list. Never invent or suggest other songs.
- Reference specific song titles and artists by name.
- Explain why the top picks fit the user — connect their energy level, mood, and genre \
preference to concrete song attributes.
- If the user's genre is absent from the catalog, acknowledge it honestly rather than \
pretending the results are a perfect genre match.
- If the user's preferences conflict (e.g., a "chill" mood but energy 0.9), \
flag the tension briefly.
- Write 3–5 sentences. No bullet points, no headers — just a short paragraph.
- Do not reproduce raw scores or match reasons verbatim; translate them into \
plain language the user would find helpful.
"""


def generate_recommendation(
    user_prefs: dict,
    retrieved_songs: list[dict],
    profile_name: str = "Unknown",
) -> str:
    """
    Full RAG pipeline:
      1. Retrieve genre + mood docs (external knowledge)
      2. Build a grounded prompt (retrieved songs + docs + user profile)
      3. Generate with Claude (with prompt caching on static instructions)
      4. Return Claude's response string; fall back to template on API error
    """
    genre = user_prefs.get("genre", "")
    mood = user_prefs.get("mood", "")

    genre_doc = _load_doc("genres", genre)
    mood_doc = _load_doc("moods", mood)

    doc_status = (
        f"genre={'found' if genre_doc else 'missing'}, "
        f"mood={'found' if mood_doc else 'missing'}"
    )
    logger.info(f"[{profile_name}] Docs retrieved — {doc_status}")

    user_message = _build_user_message(user_prefs, retrieved_songs, genre_doc, mood_doc)
    logger.debug(f"[{profile_name}] User message length: {len(user_message)} chars")

    try:
        client = _get_client()
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": _BASE_INSTRUCTIONS,
                    # Cache the static instructions — hits on every subsequent call
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        result = response.content[0].text.strip()
        usage = response.usage
        logger.info(
            f"[{profile_name}] Claude response OK "
            f"(in={usage.input_tokens}, out={usage.output_tokens}, "
            f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)})"
        )
        return result

    except EnvironmentError as exc:
        logger.error(str(exc))
        raise
    except anthropic.APIError as exc:
        logger.error(f"[{profile_name}] Claude API error: {exc} — using fallback output")
        return _template_fallback(retrieved_songs)
    except Exception as exc:
        logger.error(f"[{profile_name}] Unexpected error: {exc} — using fallback output")
        return _template_fallback(retrieved_songs)


def _build_user_message(
    user_prefs: dict,
    songs: list[dict],
    genre_doc: Optional[str],
    mood_doc: Optional[str],
) -> str:
    profile_lines = [
        f"Preferred genre : {user_prefs.get('genre', 'unknown')}",
        f"Preferred mood  : {user_prefs.get('mood', 'unknown')}",
        f"Target energy   : {user_prefs.get('energy', 'unknown')} (scale 0.0–1.0)",
        f"Likes acoustic  : {user_prefs.get('likes_acoustic', False)}",
    ]

    song_lines = []
    for i, s in enumerate(songs, start=1):
        song_lines.append(
            f"  {i}. \"{s['title']}\" by {s['artist']}"
            f" | genre={s['genre']} | mood={s['mood']}"
            f" | energy={s['energy']} | score={s['score']:.2f}"
            f" | reasons: {s['reasons']}"
        )

    parts = [
        "## User taste profile",
        "\n".join(profile_lines),
        "",
        "## Retrieved songs (ranked by scoring algorithm)",
        "\n".join(song_lines),
    ]

    if genre_doc:
        parts += ["", f"## Genre context: {user_prefs.get('genre', '')}", genre_doc]
    if mood_doc:
        parts += ["", f"## Mood context: {user_prefs.get('mood', '')}", mood_doc]

    parts += ["", "Please write your recommendation paragraph now."]
    return "\n".join(parts)


def _template_fallback(songs: list[dict]) -> str:
    lines = ["[AI generation unavailable — showing scored results]\n"]
    for i, s in enumerate(songs, start=1):
        lines.append(f"  #{i}  {s['title']} by {s['artist']}  (score: {s['score']:.2f})")
        lines.append(f"       {s['reasons']}")
    return "\n".join(lines)
