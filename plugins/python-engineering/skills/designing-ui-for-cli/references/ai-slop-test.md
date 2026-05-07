# AI Slop Test

Two-altitude category-reflex check. Run before sign-off on any shape brief, palette decision, or implementation.

## The test

If someone could look at this interface and say "AI made that" without doubt, it's failed.

## Two altitudes

The check runs at two altitudes; the second one catches what the first one misses.

- **First-order**: theme + palette guessable from category alone. The category name is enough — no other context needed.
- **Second-order**: aesthetic family guessable from category-plus-anti-references. The first reflex was avoided; the second wasn't.

## First-order reflexes

If someone could guess the theme and palette from the CLI's category alone, the design landed on the first training-data reflex. Listed below: the categories agents reach for and the answer they default to.

| Category | First-order reflex |
|---|---|
| DevOps / SRE / k8s | green-on-black matrix; ASCII whale; cyan banner |
| Package manager | cyan progress bar + emoji checkmarks + "downloading…" spinner |
| AI / LLM CLI | purple gradient banner + "✨" emojis + ASCII robot |
| Crypto / web3 | neon green/cyan on black + ASCII pickaxe |
| Cloud provider tool | blue-and-orange + cloud ASCII art |
| Git / version control | octopus / branch ASCII + git-pink accent |
| Database CLI | cylinder ASCII + amber-on-black |
| Security / pentest | skull ASCII + red-on-black + `[+]` / `[-]` prefixes |
| Build tool | hammer/anvil ASCII + yellow accents + `▰▰▰▱▱` progress |
| Docs / static site | pastel + script-italic banner |

If the planned theme and palette match the row for the project's category, it's the first reflex. Rework the scene sentence and colour strategy until the answer isn't obvious from the domain.

## Second-order reflexes

The first reflex was avoided. The agent reached for the next thing in the same training-data trajectory. Listed below: the trap one tier deeper.

| Anti-reference | Second-order reflex |
|---|---|
| AI tool that's not purple-and-emoji | editorial mono-spaced minimalism |
| DevOps tool that's not green-on-black | desaturated blue + Nerd-Font icons |
| Package manager that's not cyan-and-checkmarks | mono + brackets (`[ok]`, `[fail]`) |
| Build tool that's not hammer-emoji | orange + minimal + Helvetica-vibe banner |
| Crypto CLI that's not neon-on-black | matte black + serif title |

If the planned aesthetic family matches the row for the project's category-plus-anti-reference, it's the second reflex. Rework until both altitudes' answers are not obvious.

## Self-application

Apply the test to the current shape brief and palette before sign-off.

1. Name the project's category in one phrase (e.g. "package manager", "AI CLI", "DevOps tool").
2. Read the shape brief's scene sentence and colour strategy choice.
3. First-order check: does a reader who knows only the category guess the theme and palette? If yes, rework the scene sentence and colour strategy until the answer isn't obvious from the domain alone.
4. Read the project's anti-references (from PRODUCT.md or the shape brief).
5. Second-order check: does a reader who knows the category plus the anti-references guess the aesthetic family? If yes, rework until that answer isn't obvious either.
6. Repeat until both altitudes' answers are not obvious. Only then is the design clear of the slop reflex.

When in doubt, rework. The cost of one more revision is lower than shipping output that reads as machine-generated.
