# Theme decision: dark, light, auto, or high-contrast

## The rule

Dark vs. light is never a default. Not dark "because tools look cool dark." Not light "to be safe."

Before choosing, write one sentence of physical scene: who uses this, where, under what ambient light, in what mood. If the sentence doesn't force the answer, it's not concrete enough. Add detail until it does.

Run the sentence, not the category.

## Why this works

Categories ("DevOps tool", "data CLI", "AI assistant") collapse to training-data reflexes — green-on-black, navy + grid, purple gradient. The category does not determine the theme. The user's body, the room, the lamp, and the moment determine the theme. A scene sentence forces those details into the decision.

If the sentence is vague ("developer using a terminal"), the theme is whatever the model already wanted to pick. The sentence has to be specific enough that any alternative answer would feel wrong.

## TUI scene examples

Each sentence forces a different answer. The forced answer is not negotiable — once the scene is concrete, the theme is already decided.

| Scene sentence | Forced answer |
|---|---|
| SRE glancing at incident severity on a 27-inch monitor at 2am in a dim room | dark |
| Junior dev running their first Python script in a cafe with sunlight on the screen | light or auto |
| CI runner streaming logs into a piped buffer with no human watching | no-colour fallback |
| Designer pairing on a Stream Deck preset with the camera capturing their terminal | high-contrast |

When the scene sentence does not yet force one of these answers, the sentence is too generic. Add the time of day, the ambient light, the surface (laptop / 4K monitor / SSH session / camera feed), and the mood (calm review / 2am incident / first-run nerves). Stop adding detail when the answer becomes obvious.

## Light-terminal default consideration

Some terminals default to a light theme — notably macOS Terminal.app and several enterprise SSH clients. A CLI that hard-codes assumptions about a dark background renders unreadable text against light surfaces. Two consequences:

- Status colours chosen for dark backgrounds (bright yellow, pale cyan) often fail contrast on light backgrounds. Verify both directions.
- Detect the terminal background where the runtime allows it (e.g. Textual `App.dark` reactive, `COLORFGBG` env var). Where detection is not possible, default to `auto` and let the user override via `--theme` or env var.

When the scene sentence forces dark but the user's terminal is light, the implementation must still be readable. Theme decision drives the *primary* aesthetic; the *fallback* path is a separate non-negotiable.

## Pure black is dead — TUI adaptation

`oklch(50% 0 0)` and `#000` don't exist in nature; real shadows and surfaces always have a colour cast. For TUI:

- Where the terminal supports truecolor, the TCSS dark theme uses `$surface: oklch(15% 0.01 hue)` — small chroma toward the brand hue, never zero.
- Where truecolor is unavailable (16-colour or 256-colour mode), terminal default `bg=black` is acceptable. The fallback path is named, not silently inherited.

The rule: tinted surfaces when the rendering target supports them; named-colour fallback when it doesn't. Never specify `#000` as the canonical surface.

## Dark mode is not inverted light mode

You can't just swap colours. Dark mode requires different design decisions, and TCSS supports them through layered surface variables.

| Light mode | Dark mode (TUI translation) |
|---|---|
| Shadows for depth | Lighter surfaces for depth via `$boost` / `$panel` / `$surface` |
| Dark text on light | Light text on dark, with reduced text-style emphasis |
| Vibrant accents | Slightly desaturated accents |
| White backgrounds | Dark tinted surface (`oklch 12-18%`); never pure black |

In dark mode, depth comes from surface lightness, not shadow. Use a 3-step surface scale where higher elevations are *lighter* (e.g. `$surface` 15% / `$panel` 20% / `$boost` 25% lightness). Use the same hue and chroma as the brand colour for this project — vary only lightness.

Reduce text-style emphasis on dark backgrounds. `bold` weight reads heavier on dark than on light, so a body line that is `bold` on light should usually be regular on dark. Same word, different rendered weight.

## Decision checklist

Before any code, the shape brief records:

- The scene sentence (verbatim, one sentence)
- The theme it forces (dark / light / auto / high-contrast)
- The fallback path when terminal capability or background detection breaks the primary choice
- The surface scale for the chosen theme (3 lightness steps if dark)
- The accent desaturation rule (if dark)

If any item is missing, the brief is not yet concrete. Add detail to the scene sentence until the answer is forced.

## Source

SOURCE: [impeccable v3.0.7 SKILL.md "Theme" section](https://github.com/withastro/impeccable) (accessed 2026-05-07) — verbatim port of "Dark vs. light is never a default", scene sentence rule, and "Run the sentence, not the category". Local cache path: `~/.claude/plugins/cache/impeccable/impeccable/3.0.7/skills/impeccable/SKILL.md` lines 87-91.

SOURCE: [impeccable v3.0.7 reference/color-and-contrast.md](https://github.com/withastro/impeccable) (accessed 2026-05-07) — "Pure black is dead" rule (line 70) and "Dark mode is not inverted light mode" table (lines 80-99). Local cache path: `~/.claude/plugins/cache/impeccable/impeccable/3.0.7/skills/impeccable/reference/color-and-contrast.md`.
