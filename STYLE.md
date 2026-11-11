# DoD Fighter art style (locked)

The approved look is **DarthNox LF2 v4** (AutoSprite character
`cmwbyt2s9008lsxrgic7ttmeq`), and specifically his **idle** frames. Every new
character and every new animation must match it. Do not improvise on the
items below; they were each arrived at by trying the alternatives in game.

## The look

| Rule | Value | Why |
|---|---|---|
| Proportions | **~3 heads tall**, head ≈ ⅓ of body height | Matches Davis and the stock LF2 cast. ~5 heads read as a tiny head; slim anime proportions read as a stick figure. |
| Build | short, broad torso; thick short limbs; big gloves and boots | Stocky silhouettes read at 82px. |
| Face | big readable eyes, bold brows, simple features | The face must survive a 40×45 HUD portrait. |
| View | side view facing right (3/4 allowed), fighting stance | LF2 sprites face right; the engine mirrors for left. |
| Rendering | bold dark outlines, flat cel shading, saturated colours | Survives the 255-colour reduction. |
| Weapons | **short and thick**, bright, high-contrast against the body | A thin blade vanishes at 82px and AutoSprite drops thin weapons from stock clips. |
| Darks | no pure black (0,0,0) anywhere in the art | Pure black is the transparent colour key; the converter lifts it to (8,8,8) anyway. |

## New character prompt (template)

Use `create_character` with `quality: "pro"`. Keep the first two sentences
word-for-word; only the outfit sentence and the weapon change.

```
Full-body 2D beat-em-up fighter sprite, side view facing right, fighting
stance. Super-deformed proportions: only 3 heads tall, very big head (one
third of total height), short broad body, thick short limbs, big gloves and
boots. <OUTFIT: hair, face, clothing, colours>. <WEAPON: short, thick, bright,
clearly visible>. Bold outlines, flat cel shading.
```

DarthNox's outfit sentence, for reference:

> Musketeer: navy hat with red-and-white plume, spiky black hair, clean-shaven
> face, navy cape, royal-blue tabard with white cross, brown belt with gold
> buckle, brown gloves, brown trousers, brown boots. Right hand holds a short,
> thick, bright silver rapier with gold cup hilt, clearly visible.

## Animation settings

Proportions drift when AutoSprite re-imagines the character for each clip
(v4's first walk came out with a smaller head than its idle). To stop that:

1. Generate **idle** first: `kind: "idle"`, `videoTier: "turbo"`, 16 frames,
   256px. Check it. This is the style reference for everything after.
2. Save idle frame 0 as a pose (`save_pose`, free). DarthNox's is
   **"Idle Lock"** `cmwbz0zox002d5fd9bu6f138p`.
3. Generate every other clip **from that pose**:
   `turboMode: "first_frame"`, `first_frame_pose_id: <Idle Lock>`, and for
   loops (walk, run) also `last_frame_pose_id: <Idle Lock>`, `loop: true`.
4. If a weapon goes missing, use `kind: "custom"` with a prompt that says the
   weapon is "fully visible in every frame" — and describe only what should be
   there, never what shouldn't. (The stock `run` dropped the rapier; the custom
   "run sword" clip kept it.)
5. A clip anchored on the pose starts and ends on the standing pose, so skip
   those frames when converting (`walk.png,walk.json,4,1,14`) and, for a clip
   that repeats, take exactly one cycle (`run.png,run.json,4,1,4`).

Never enable `withSound` without asking — it costs extra.

## Conversion settings

```
python tools/autosprite_to_lf2.py out s0.345992 idle.png,idle.json,4 walk.png,walk.json,4,1,14 run.png,run.json,4,1,4     slash.png,slash.json,@5/6/7 thrust.png,thrust.json,@3/5/12 jump.png,jump.json,@12/9/6,ground
```

- DarthNox's approved size is **scale s0.345992** (his idle at 82px tall). Pass
  it as `s0.345992` so raised swords and jumps can't shrink him. For a new
  character, convert the idle alone with height `82` once, then lock the scale
  it prints (`scale s…`) for every later rebuild.
- Attacks: pick the key frames by hand with `@A/B/C` (wind-up, strike,
  follow-through). Jumps: add `,ground` — the clip lifts the character, and the
  engine already does that.
- Skip frames where AutoSprite cropped the hat or weapon at the image edge.
- 4 evenly spaced frames per clip, `wait: 3`.
- Portraits: `tools/autosprite_portrait.py` — `head:` 120×120, `small:` 40×45,
  on the dark navy backdrop (22,30,58).
