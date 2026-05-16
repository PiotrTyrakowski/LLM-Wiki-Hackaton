"""Prompts for Gemini vision interrogation. Tuned per recreator's cookbook:
one question per call, tabular text answers, no JSON schemas."""

CUTS_PROMPT = (
    "Watch this clip. List every visible cut you see (hard cuts, J-cuts, L-cuts, dissolves). "
    "Ignore micro-jitter under 0.2s. "
    "Format each line as `t=<seconds> | type=<hard|j|l|dissolve> | from=<scene_desc> | to=<scene_desc>`. "
    "Be precise on timestamps. Only output the lines, no prose."
)

PACING_PROMPT = (
    "Watch this clip. Tabulate shot lengths in seconds. "
    "Format each line as `shot=<n> | start=<sec> | end=<sec> | length=<sec> | label=<one-clause-desc>`. "
    "Only output the lines."
)

BROLL_PROMPT = (
    "Watch this clip. Identify every moment when b-roll (cutaway footage that is NOT the primary speaker) is shown. "
    "Format each line as `t=<start_sec> | duration=<sec> | subject=<what is shown> | speaker_line=<short quote of what the speaker is saying>`. "
    "Only output the lines."
)

MOTION_PROMPT = (
    "Watch this clip. Identify camera motion and intra-shot effects (zoom in, zoom out, pan, push-in, dolly, shake). "
    "Format each line as `t=<sec> | kind=<zoom-in|zoom-out|pan|push-in|dolly|shake> | strength=<small|medium|large> | duration=<sec>`. "
    "Only output the lines."
)

TEXT_PROMPT = (
    "Watch this clip. Identify every on-screen text overlay (titles, lower-thirds, callouts, captions are excluded — only graphic text). "
    "Format each line as `t=<start_sec> | duration=<sec> | position=<bottom|center|top> | text=<exact text>`. "
    "Only output the lines."
)


INGEST_PROMPTS = {
    "cuts": CUTS_PROMPT,
    "pacing": PACING_PROMPT,
    "broll": BROLL_PROMPT,
    "motion": MOTION_PROMPT,
    "text": TEXT_PROMPT,
}
