# Future Ideas

## Optional Cloud TTS (Deferred)
- Consider adding an opt-in online TTS engine for higher quality.
- Keep local Dia2 as default; cloud only if explicitly configured.
- Only send the generated script to the service; receive audio back.
- Maintain fallback chain: cloud -> Dia2 -> Kokoro.

## Installer UX
- Add `--local` flag to installers to force local-only mode.
- Default behavior remains local unless user opts in to cloud.

## Safety & Privacy
- Clearly document data sent (script only) and require explicit consent.
- Make cloud usage opt-in by config/env and never default silently.
