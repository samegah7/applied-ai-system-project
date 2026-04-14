# Model Card: Music Recommender Simulation

## 1. Model Name

**MoodMatch 1.0** — a rule-based music recommender that scores songs against a user's mood, genre, and energy preferences.

---

## 2. Goal / Task

MoodMatch 1.0 predicts the top 5 songs from a small catalog that best fit a user's current mood, favorite genre, and target energy level. Given three inputs — a genre string, a mood string, and an energy number (0–1) — it assigns each song a score and returns the highest-scoring songs with a plain-language explanation of why each ranked where it did.

---

## 3. Data Used

The catalog contains 21 songs (10 starter songs + 11 added). Each song has these attributes: genre, mood, energy (0–1), tempo in BPM, valence, danceability, and acousticness.

Genres represented: lofi (3), pop (2), country (3), r&b (3), hip-hop (3), edm (2), rock (1), ambient (1), jazz (1), synthwave (1), indie pop (1). Moods represented: happy (5), chill (5), intense (4), relaxed (3), moody (2), focused (1).

11 songs were added to cover genres absent from the starter dataset: country (Backroad Summer, Heartbreak Highway, Golden Hour Drive), R&B (Late Night Feels, Neon Love, Smooth Like That), hip-hop (Block Party, Grind Season, Low Key), and EDM (Drop Zone, Euphoria Wave). The dataset now spans a wider energy range and includes more high-energy songs. Still absent: metal, classical, K-pop, Latin, and many regional genres. The catalog, while broader, still skews toward genres that were easy to name and describe in English and does not represent global listener diversity.

---

## 4. Algorithm Summary

Every song in the catalog gets a score against a user's preferences. The score has three parts:

- **Mood match** adds +2.0 if the song's mood label (e.g., "happy," "intense," "chill") matches what the user asked for. This is the highest-weight signal because mood captures how you feel right now.
- **Genre match** adds +0.75 if the song's genre (e.g., "pop," "lofi," "rock") matches the user's favorite. Genre is given less weight than mood because it is a weaker signal in this experiment.
- **Energy closeness** awards up to +2.0 based on how close the song's energy level (0 to 1) is to the user's target. A perfect match earns +2.0; the further away, the smaller the bonus.

The scores are added up, and the top 5 songs are returned with an explanation of why each scored the way it did. Note: the user's `likes_acoustic` preference is collected but never used in the scoring — this is a known gap.

---

## 5. Observed Behavior / Biases

**What works well:** When all three signals — mood, genre, and energy — point in the same direction, the system produces sensible and explainable results. A "Chill Lofi" user correctly gets Library Rain at #1 (score 4.75). A "Deep Intense Rock" user correctly gets Storm Runner at #1 (score 4.73).

**Biggest limitation — ignored acoustic preference:** The `likes_acoustic` user preference is collected but never used in the scoring formula. A user who dislikes acoustic music will still receive Library Rain (acousticness 0.86) and Coffee Shop Stories (acousticness 0.89) as top recommendations if their energy and mood align, because the scorer ignores this preference entirely.

**Mood/energy conflict:** The energy score (up to +2.0) carries equal weight to a mood match (+2.0). A high-energy song in completely the wrong mood can still rank in the top 5 simply because its energy level is close. Gym Hero — a workout track labeled "intense" — appears at #3 for a user who asked for "happy pop" because its energy (0.93) is nearly identical to the user's target (0.9). The system cannot distinguish "I want music that feels happy" from "I want music that is loud."

**Catalog gap = fairness gap:** Users whose genre does not appear in the catalog (e.g., country fans) never receive a genre bonus. Every pop user gets a structural advantage of +0.75 over any genre not in the catalog. This is not intentional bias — it is a data gap that becomes a fairness problem.

---

## 6. Evaluation Process

Six user profiles were tested: three standard profiles and three adversarial profiles designed to expose edge cases.

- **High-Energy Pop** (pop, happy, energy 0.9): Sunrise City ranked #1 correctly. Surprising: Gym Hero ranked #3 despite its mood being "intense," not "happy."
- **Chill Lofi** (lofi, chill, energy 0.35): Cleanest result. Library Rain scored 4.75 — perfect energy match + mood + genre. Top 3 all felt intuitively right.
- **Deep Intense Rock** (rock, intense, energy 0.92): Storm Runner correctly ranked #1. Surprising: Gym Hero (pop, intense, energy 0.93) ranked #2, ahead of every other rock song, because mood + energy signals were strong enough to overcome the wrong genre.
- **Conflicting Energy+Mood** (lofi, chill, energy 0.9): The user wants the sound of a chill lofi playlist but the energy of a workout track. The system returned the same low-energy lofi songs as the normal chill user — mood+genre (+2.75) outweighed the energy mismatch penalty. The system had no way to detect the contradiction.
- **Unknown Genre — country** (country, happy, energy 0.7): No genre match was ever awarded. The system defaulted to mood-and-energy matching, delivering Rooftop Lights (#1) and Sunrise City (#2) — reasonable mood choices, but the genre the user asked for is completely absent.
- **Extreme Low Energy** (ambient, chill, energy 0.0): Spacewalk Thoughts correctly ranked #1 (4.19). No errors or zero-division issues.

**Biggest surprise:** Mood+genre together dominate over energy. A user who requests "chill lofi at energy 0.9" gets nearly the same low-energy songs as one who requests "chill lofi at energy 0.35" — the mood and genre points overwhelm the energy difference.

---

## 7. Intended Use and Non-Intended Use

**Intended use:** MoodMatch 1.0 is designed for classroom exploration of how recommender systems work. It is a simulation to help students understand how scoring decisions encode assumptions and create bias. It works best as a teaching tool when you run multiple profiles and compare what changes.

**Non-intended use:** This system should not be used as a real music recommendation product. It has a 10-song catalog, ignores user feedback, cannot learn from listening history or skips, and cannot represent genres outside its small dataset. It assumes every user can perfectly express their taste as a single genre, a single mood, and one energy number — an assumption that does not hold for real listeners. Do not use it to make decisions about what music to surface to real users.

---

## 8. Ideas for Improvement

- **Use the `likes_acoustic` field**: Add up to +1.0 for songs with low acousticness when `likes_acoustic=False`, and up to +1.0 for high-acousticness songs when `likes_acoustic=True`. This field is already in the data model — it just needs to be wired into the scorer.
- **Expand the catalog**: Add at least 3–5 songs per genre, including country, R&B, hip-hop, and electronic dance music, to reduce genre-blindness for underrepresented listeners.
- **Use valence and danceability**: These fields exist in the data but are never scored. Valence (emotional positivity) is a strong proxy for mood, and danceability is a strong signal for genre fit. Incorporating them would reduce the chance that "intense" and "happy" songs score identically on energy alone.
- **Diversify top-k results**: Prevent the same genre or mood from occupying all 5 spots by adding a diversity constraint that ensures at least 2 different moods or genres appear in results.

---

## 9. Personal Reflection

**Biggest learning moment:** Building this recommender made it clear how much a scoring formula encodes assumptions about what matters. Giving mood the highest weight felt intuitive at first — of course how you feel matters most — but the moment energy and mood conflict (a user who wants "chill but loud"), the system breaks down invisibly: it returns songs that look correct in the explanation output but feel completely wrong to a real listener. The most striking discovery was that the `likes_acoustic` field was designed into the data model but never wired into the scorer. Unused signals are the same as missing signals — the system behaves as if the preference never existed. This changes how I think about apps like Spotify: the features they collect are only as good as whether an engineer actually plugged them into the model.

**How AI tools helped — and when I needed to double-check:** AI tools helped speed up scaffolding the data model and drafting the scoring function, and were useful for quickly generating adversarial test profiles I might not have thought of on my own (like the conflicting energy+mood profile). Where I needed to double-check was in the explanation strings and score values: generated explanations sounded confident and readable, but I had to verify manually that the numbers matched what the code actually computed. It is easy for AI-generated text to "look right" without being precisely accurate. I also had to check that the edge-case profiles (energy 0.0, unknown genre) were actually testing what I thought they were testing — the AI suggested them, but I had to run them and read the output myself to understand what was happening.

**What surprised me about simple algorithms "feeling" like recommendations:** The most surprising thing was how much the output *feels* like a thoughtful recommendation even though the system is just adding three numbers together. When Library Rain appears at #1 for a chill lofi user with the explanation "mood match (+2.0), genre match (+0.75), energy closeness (+1.84)," it reads like a considered choice — but it is pure arithmetic. This made me realize that a lot of the "intelligence" in a recommendation system lives in the design of the features and weights, not in any learning algorithm. A simple formula with well-chosen signals can produce outputs that feel meaningful, which is both powerful and dangerous — it is easy to trust results that are wrong for reasons the formula cannot see.

**What I would try next:** I would add the acoustic preference to the scoring formula first, since it is the lowest-effort fix with the highest impact on users who care about it. After that, I would expand the catalog to at least 50 songs covering underrepresented genres, then experiment with using valence as a secondary mood signal so the system can more reliably distinguish between "high energy happy" and "high energy intense" — the two cases this version handles least well.
