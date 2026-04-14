# Reflection: Profile Comparison Notes

This file compares pairs of user profiles and explains what changed in the recommendations
and why. Written in plain language — imagine explaining this to someone who has never seen
the code.

---

## Pair 1: High-Energy Pop vs. Deep Intense Rock

**High-Energy Pop** (pop, happy, energy 0.9) → Top 5: Sunrise City, Rooftop Lights, Gym Hero, Storm Runner, Night Drive Loop
**Deep Intense Rock** (rock, intense, energy 0.92) → Top 5: Storm Runner, Gym Hero, Sunrise City, Rooftop Lights, Night Drive Loop

**What changed and why:**
The top two results completely flipped. Sunrise City ranked #1 for the pop fan because it
matched all three signals (happy + pop + energy 0.82 ≈ 0.9). Storm Runner ranked #1 for the
rock fan because it matched all three of its signals (intense + rock + energy 0.91 ≈ 0.92).

What is interesting is that Gym Hero appears in both lists at #3 and #2 respectively — even
though it is a pop song, not rock. The rock fan got it ranked #2 because its mood ("intense")
matched perfectly and its energy (0.93) was almost identical to what the rock fan wanted (0.92).
The system does not care that "Gym Hero" is pop — the mood and energy signals were strong enough
to push it ahead of every other rock song in the catalog (there is only one: Storm Runner).

Plain language: The pop fan and rock fan both want loud, high-energy music. But the pop fan
wants music that *feels cheerful*, and the rock fan wants music that *feels intense*. The
system mostly gets this right, but both profiles end up sharing "Gym Hero" — a workout track
that does not really belong in either a happy pop playlist or a rock playlist.

---

## Pair 2: Chill Lofi vs. Extreme Low Energy (Ambient)

**Chill Lofi** (lofi, chill, energy 0.35) → Top 5: Library Rain, Midnight Coding, Spacewalk Thoughts, Focus Flow, Coffee Shop Stories
**Extreme Low Energy** (ambient, chill, energy 0.0) → Top 5: Spacewalk Thoughts, Library Rain, Midnight Coding, Coffee Shop Stories, Focus Flow

**What changed and why:**
The top 5 songs are almost identical — just in a different order. Spacewalk Thoughts jumped
from #3 (for the lofi fan) to #1 (for the ambient fan) because:
1. Its genre ("ambient") finally matched — awarding +0.75 that the lofi fan never received.
2. Its energy (0.28) is the closest in the entire catalog to the extreme low target of 0.0.

Library Rain dropped from #1 to #2 because, even though its energy (0.35) is a perfect match
for the lofi fan, it is lofi genre (not ambient) so the ambient fan gets no genre bonus for it.

Plain language: Both profiles want quiet, calm music. The only real difference is that the
"ambient" fan gets Spacewalk Thoughts bumped to the top because it is the one ambient song in
the catalog. For the lofi fan, Library Rain is the clear winner because it is a perfect energy
match plus genre match. When you change the genre label in the preference, one song moves to
the top and another drops slightly — the rest of the list stays the same. This shows how
fragile genre-based ranking is in a small catalog.

---

## Pair 3: Conflicting Energy+Mood vs. Chill Lofi

**Chill Lofi** (lofi, chill, energy 0.35) → Top 5: Library Rain (4.75), Midnight Coding (4.61), Spacewalk Thoughts (3.86), Focus Flow (2.65), Coffee Shop Stories (1.96)
**Conflicting Energy+Mood** (lofi, chill, energy 0.9) → Top 5: Midnight Coding (3.79), Library Rain (3.65), Spacewalk Thoughts (2.76), Storm Runner (1.98), Gym Hero (1.94)

**What changed and why:**
These two profiles have the same genre (lofi) and the same mood (chill), but different energy
targets: 0.35 vs 0.9. You might expect the high-energy version to get different songs — but
the top three are still the same low-energy lofi tracks (Library Rain, Midnight Coding,
Spacewalk Thoughts), just with lower scores.

Why? Because mood + genre together add +2.75 points for Library Rain and Midnight Coding. Even
though the energy penalty for Library Rain is large (|0.9 - 0.35| = 0.55 → energy score 0.90),
the mood+genre bonus still outweighs it. The system has no understanding that "chill" and
"energy 0.9" are contradictory — it treats them as two completely separate signals.

What is new for the conflicting profile: Storm Runner (#4) and Gym Hero (#5) appear at the
bottom of the top 5, pushed up purely by their high energy. These are intense, loud songs that
do not match the user's mood at all.

Plain language: Imagine someone who says "I want relaxing lofi music — but make it really
high energy." That does not quite make sense, because lofi music is almost always quiet and
calm. A human would say "I think you mean something else." But the recommender cannot reason
about contradictions — it just adds up the numbers. The chill mood scores lofi songs highly,
and the high energy request has nowhere to go, so you get a mix of quiet lofi and loud workout
music sharing the same top-5 list. The system is confused, but it does not know it.

---

## Pair 4: Unknown Genre (Country) vs. High-Energy Pop

**High-Energy Pop** (pop, happy, energy 0.9) → Top 5: Sunrise City (4.59), Rooftop Lights (3.72), Gym Hero (2.69), Storm Runner (1.98), Night Drive Loop (1.70)
**Unknown Genre — Country** (country, happy, energy 0.7) → Top 5: Rooftop Lights (3.88), Sunrise City (3.76), Night Drive Loop (1.90), Storm Runner (1.58), Gym Hero (1.54)

**What changed and why:**
The country fan and the pop fan both want "happy" music, but at different energy levels (0.7
vs 0.9). The country fan gets a genre match on *nothing* in the entire catalog — there are
zero country songs. So the genre bonus (+0.75) is permanently unavailable to this user.

As a result, the country fan's top scores are capped lower: their best song scores 3.88 vs the
pop fan's 4.59. The gap between #1 and #5 is also smaller for the country fan (3.88 down to
1.54) compared to the pop fan (4.59 down to 1.70). This is a form of unfairness: users whose
taste is not represented in the catalog are structurally penalized compared to users who happen
to match the genres that were included.

Rooftop Lights jumped to #1 for the country fan (was #2 for the pop fan) because its energy
(0.76) is closer to the country fan's target of 0.7, and without any genre competition, mood
alignment becomes the dominant factor.

Plain language: A country music fan using this app is at a permanent disadvantage. Every time
a pop fan gets +0.75 for a genre match, the country fan gets nothing — not because their taste
is wrong, but because whoever built the catalog did not include any country songs. The system
is not intentionally biased against country fans; it just never thought about them. This is a
classic example of a data gap turning into a fairness problem.
