# Lint report — 2026-05-16T22-57-18Z

Lint never auto-fixes; treat each item as a suggestion.

## Skill density
- **cut-detection**: 5 rule(s)
- **broll-selection**: 5 rule(s)
- **pacing**: 5 rule(s)
- **transitions**: 5 rule(s)
- **on-screen-text**: 5 rule(s)

## Cross-skill duplicate candidates
- between **cut-detection** ('stay around 4-8 seconds per shot.') and **broll-selection** ('hold b-roll 2-4 seconds.') — common tokens: `['4', 'b', 'hold', 'roll', 'seconds']`
- between **cut-detection** ('stay around 4-8 seconds per shot.') and **pacing** ('end on a held shot.') — common tokens: `['3', 'cut', 'hold', 'seconds', 'shot']`
- between **cut-detection** ('stay around 4-8 seconds per shot.') and **on-screen-text** ('hold for at least 2 seconds.') — common tokens: `['at', 'hold', 'least', 'seconds']`
- between **cut-detection** ('tighten pauses.') and **broll-selection** ('hold b-roll 2-4 seconds.') — common tokens: `['4', 'seconds', 'speaker', 'than']`
- between **broll-selection** ('hold b-roll 2-4 seconds.') and **on-screen-text** ('hold for at least 2 seconds.') — common tokens: `['2', '2s', 'hold', 'seconds']`

## Unapplied skill-improvement proposals (Cognee graph)
- None.

## Orphan observation files
- ✅ none
