# Kunumi Source Map

This is the human routing view of the approved Kunumi material bundled with the skill. Query
`semantic-index.json` through `scripts/kunumi_lookup.py`; do not load the JSON wholesale.

## Access Model

- **Local by default:** approved marks, Figtree and Space Grotesk, Instituto static backgrounds, three lightweight
  GIFs, LinkedIn/profile support files, and the CSS/HTML preview. All of it runs without
  authentication.
- **Ask when missing:** slide decks, heavy GIF/video, detailed channel guides, named-person
  portraits, historical/client templates, and the 2025 report are not bundled. Ask the user for
  the approved file instead of substituting or reconstructing it.
- Keep user-supplied working files in a temporary or user-designated cache. Do not add them to
  Git by default.

Resolve a source in one command:

```bash
python scripts/kunumi_lookup.py resolve "Instituto gradient"
python scripts/kunumi_lookup.py sources --identity instituto
python scripts/kunumi_lookup.py sources --kind wordmark
```

## Local Bundle

```text
assets/local/
├── brand-marks/
│   ├── core/
│   ├── instituto/
│   ├── unlimited/
│   └── shared/
├── fonts/Figtree/
├── fonts/SpaceGrotesk/
├── instituto/
│   ├── static/
│   └── motion-lightweight/
└── channels/
    ├── linkedin/
    └── profile/

assets/web/
├── kunumi-tokens.css
├── template-preview.html              ← contact sheet, 4 frames, authoring medium
├── template-preview.render.json       ← measured geometry of the last render
├── template-preview-kunumi-capa.png
├── template-preview-kunumi-dados.png
├── template-preview-instituto-gradiente.png
└── template-preview-instituto-pixels.png
```

The four PNGs are **generated**, one per `data-kunumi-frame`, and must never be replaced by a
screenshot:

```bash
kunumi_critic.py render assets/web/template-preview.html \
  --canvas 2048x1200 --scale 2 --reduced-motion --out-dir assets/web
```

`--out-dir` matters: without it the PNGs and `template-preview.render.json` land in a temp
directory, and the committed record then claims files that are not the committed ones.
`artifact.unprovenanced` checks exactly that claim.

The canvas is wider than the 1920 stage to leave room for the viewer padding; each frame still
captures at exactly 1920x1080, delivered at 2x. See ADR 0016.

No slide deck is bundled. Ask the user for the approved Kunumi or Instituto source deck before
building slides, and use `references/slide-layouts.md` to identify the exact source layout to
duplicate.

## Resolution Procedure

1. Resolve the exact source with `kunumi_lookup.py`.
2. Use the returned `localPath`.
3. If nothing resolves, state which source is missing and ask the user to provide that file. Do
   not redraw, recolor, or synthesize a replacement.
4. Never search portraits broadly when the task names a person; ask for the named portrait only.
