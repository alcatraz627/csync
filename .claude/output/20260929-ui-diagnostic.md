# csync UI diagnostic: what's actually wrong

**Date:** 2026-09-29 · author: csync-opus

## The core finding

The native app is **not** diverging from the mock. The side-by-side
(`.claude/output/20260928-recon/side-by-side/home-dark.png`) shows the app
reproduces the codex mock almost pixel for pixel. So fidelity is not the
problem. **The mock is the ceiling, and the mock is a generic template.** It
hits several of the well-known "generated UI" tells at once. Faithfully
implementing a generic design yields a generic app. To make the UI good we fix
the mock's design first, then bring the app to it.

## Systemic problems, ranked by how much they hurt

### 1. The SaaS-card kit: no hierarchy (highest impact)
Every screen is the same thing. Identical flat dark rounded cards, one corner
radius on everything, one flat fill, arranged in uniform stacks and 2-col grids.
Nothing leads the eye. On Home, the Raspberry Pi (the hub the whole app exists
to reach) is rendered as a list row the same weight as "Mac" and the same weight
as a settings link. The screen has no subject, no focal point, no sense that one
thing matters more than another. This is the single biggest reason it reads as
"an app template" rather than "an app".

### 2. Flat, sleepy, low density
Big empty vertical gaps, mono-weight text (title and body are near the same
grey), low contrast, no depth. Screens feel sparse and half-finished rather than
calm. The Player is the worst: a large dead grey box with "DISPLAY IDLE"
floating in it, then four identical control cards with `Volume _` / `Speed _`
underscore placeholders that look broken.

### 3. The generic tells (each one is a known AI-design signature)
- ALL-CAPS tracked-out eyebrows over every section: `DEVICES`, `CAPABILITIES`,
  `DISPLAY IDLE`, `CHOOSE A DRIVE`.
- Meta strings joined with middle dots: `Online · media, assistant, camera`,
  `Pi screen · Stopped · select a file to play`, `1 thread · assistant ready`.
- Tinted near-black background (#0F1216) standing in for a considered dark.
- Placeholder underscores shown as real UI (`Volume _`).

### 4. The accent does nothing
Coral (#E4572E) only appears in tiny 14 to 20px icons. It is never used to
signal the primary action, a live state, or hierarchy. The play button looks
like the rewind button. "Online" is a small dot. There is no moment of colour
that tells you where to look or what is alive.

### 5. No identity
Nothing on screen says csync, or "your own machines", or "a mesh". Strip the
words and it could be any dark settings app. The one asset with real identity is
the new mesh-hub app icon, and the UI does not echo it at all.

## Per-screen specifics
- **Home:** flat Pi row where a hub hero belongs; 2-col grid of 7 identical
  capability cards; two ALL-CAPS eyebrows; middle-dot status strings.
- **Player:** dead grey poster with an ALL-CAPS float; transport row with no
  primary; `Volume _` placeholder cards; huge empty lower half.
- **Media / Settings / More:** long stacks of identical rows and cards. The only
  differentiator between a "connected drive", a "capability", and a "setting" is
  the label text, not the design.
- **Chat:** the most defensible screen (bubbles and thinking sections have real
  structure), but the header subtitle is a middle-dot `model · effort` string.

## The fix direction (for the mock, then the app)
One point of view, applied per the frontend-design guidance "spend your boldness
in one place":

1. **Make the hub the hero.** Home opens on the Pi as the centre of a small
   personal mesh, not a list row: larger, warmer, with its capabilities as inline
   pills and live state in coral. Echo the mesh-hub icon motif.
2. **Build real hierarchy.** Primary (the hub, the now-playing, the compose
   action) is large and coral-led. Secondary (capabilities, settings) is quieter.
   Tertiary (metadata) is small and dim. Not every element is a card.
3. **Kill the tells.** Sentence-case section labels or fold them into the layout.
   Replace middle-dot strings with pills or plain sentences. Never show a
   placeholder underscore. Give the dark a considered, slightly warm tone.
4. **Spend the accent deliberately.** Coral marks the one primary action and live
   state on each screen, nothing else.
5. **One identity thread.** The mesh motif and a consistent, denser rhythm run
   through every screen so it reads as one designed product.

## Proposed order of work
1. This diagnostic (done).
2. Redesign the **Home** mock as a concrete direction proposal, then show it.
3. On approval, roll the direction across the mock's screens.
4. Bring the native app to the improved mock, screen by screen, verified on the
   emulator.
