"""Scene compositor — layers environment, body, outfit, face, and aura.

Two rendering modes:

  SPEAKING mode:  Character left + dynamic-sized chat bubble right
  IDLE mode:      Full 250x122 canvas, no bubble, detailed environment

Pipeline:
    1.  Clear frame
    2.  Draw ENVIRONMENT background (full-canvas in idle, left-zone in speaking)
    3.  Apply POSE body transform + select pose RLE body
    4.  Draw BODY (RLE with transforms)
    5.  Draw OUTFIT (body-relative anchors)
    6.  Draw white eye sockets
    7.  Draw PUPILS (emotion-specific)
    8.  Draw BROWS / LIDS / SPECIAL EYES (emotion-specific)
    9.  Draw TEARS (if applicable)
    10. Draw MOUTH (emotion-specific)
    11. Draw AURA PARTICLES (emotion-specific, body-center-relative)
    12. Draw WEATHER overlay (emotion modulation)
    13. Draw CHAT BUBBLE (dynamic size, or skip in idle mode)
"""

from .core import canvas
from .core.body import draw_body, BODY_RLE_STANDARD, BODY_RLE_FAT, BODY_RLE_LAZY
from .emotions import REGISTRY as EMOTIONS
from .emotions.faces import draw_eyes
from .poses import REGISTRY as POSES
from .environments import REGISTRY as ENVIRONMENTS
from .outfits import REGISTRY as OUTFITS, DEFAULT_ANCHORS
from .aura import REGISTRY as AURAS

# Body RLE lookup by key
_BODY_MAP = {
    "standard": BODY_RLE_STANDARD,
    "fat": BODY_RLE_FAT,
    "lazy": BODY_RLE_LAZY,
}

# Standard face/body center positions (standing, standard body)
_STD_FACE_CENTER = (35, 25)
_STD_BODY_CENTER = (35, 45)


# ── Dynamic chat bubble ──

def draw_bubble_dynamic(text_lines=0, text_width=0):
    """Draw a chat bubble sized to content.

    text_lines: number of text lines (0 = small single-line bubble)
    text_width: approximate pixel width of longest line (0 = auto)

    Bubble anchors to the character's right side and scales with content.
    Minimum: 60x24. Maximum: 170x70 (legacy full size).
    """
    # Size calculation
    min_w, min_h = 60, 24
    max_w, max_h = 168, 70
    line_height = 10  # approx pixels per text line
    padding = 8

    lines = max(1, text_lines)
    bh = min(max_h, max(min_h, lines * line_height + padding * 2))
    bw = min(max_w, max(min_w, text_width + padding * 2)) if text_width > 0 else min(max_w, max(min_w, 40 + lines * 15))

    # Position: anchored RIGHT NEXT to the character (x~70), vertically centered
    bx = 78  # snug against character's right edge + tail gap
    by = max(2, (canvas.IMG_H - bh) // 2)
    # Clamp width so bubble doesn't overflow canvas
    if bx + bw > canvas.IMG_W - 2:
        bw = canvas.IMG_W - bx - 2

    # Clear interior (white fill so environment doesn't bleed through)
    for y in range(by + 1, by + bh - 1):
        for x in range(bx + 1, bx + bw - 1):
            canvas.px_clr(x, y)

    # Border (double-thick)
    for x in range(bx + 3, bx + bw - 3):
        canvas.px_set(x, by)
        canvas.px_set(x, by + 1)
        canvas.px_set(x, by + bh - 1)
        canvas.px_set(x, by + bh - 2)
    for y in range(by + 3, by + bh - 3):
        canvas.px_set(bx, y)
        canvas.px_set(bx + 1, y)
        canvas.px_set(bx + bw - 1, y)
        canvas.px_set(bx + bw - 2, y)

    # Rounded corners
    corners = [(bx + 2, by + 2), (bx + bw - 3, by + 2),
               (bx + 2, by + bh - 3), (bx + bw - 3, by + bh - 3)]
    for cx, cy in corners:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    canvas.px_set(cx + dx, cy + dy)

    # Speech tail — triangular pointer toward character
    tail_y = by + bh // 3  # point roughly at character's face height
    tail_len = 7
    # Clear tail area first
    for i in range(tail_len):
        spread = int(1 + i * 0.5)
        for dy in range(-spread, spread + 1):
            canvas.px_clr(bx - 1 - i, tail_y + dy)
    # Draw tail outline
    for i in range(tail_len):
        t = i / max(tail_len - 1, 1)
        tx = bx - 1 - i
        ty_top = tail_y - int(3 * t)
        ty_bot = tail_y + int(3 * t)
        canvas.px_set(tx, ty_top)
        canvas.px_set(tx, ty_bot)
    # Tip pixel
    canvas.px_set(bx - tail_len, tail_y)


def draw_bubble_legacy():
    """Original fixed-size chat bubble (170x70) for backwards compat."""
    bx, by, bw, bh = 75, 5 + canvas.Y_OFF, 170, 70
    # Clear interior
    for y in range(by + 1, by + bh - 1):
        for x in range(bx + 1, bx + bw - 1):
            canvas.px_clr(x, y)
    for x in range(bx + 3, bx + bw - 3):
        canvas.px_set(x, by)
        canvas.px_set(x, by + 1)
        canvas.px_set(x, by + bh - 1)
        canvas.px_set(x, by + bh - 2)
    for y in range(by + 3, by + bh - 3):
        canvas.px_set(bx, y)
        canvas.px_set(bx + 1, y)
        canvas.px_set(bx + bw - 1, y)
        canvas.px_set(bx + bw - 2, y)
    corners = [(bx + 2, by + 2), (bx + bw - 3, by + 2),
               (bx + 2, by + bh - 3), (bx + bw - 3, by + bh - 3)]
    for cx, cy in corners:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    canvas.px_set(cx + dx, cy + dy)
    tb = 35 + canvas.Y_OFF
    tail_dx = [0, -1, -2, -3, -4, -5, -6, -7, -6, -5, -4, -3, -2, -1, 0]
    tail_dy = [0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 7, 6, 5, 4]
    for i in range(15):
        canvas.px_set(bx + tail_dx[i], tb + tail_dy[i])


# ── Main render function ──

def render_scene(
    emotion: str,
    pose: str = "standing",
    environment: str | None = None,
    outfit: str | None = None,
    frame_idx: int = 0,
    mode: str = "speaking",
    text_lines: int = 2,
    text_width: int = 0,
    bubble_style: str = "dynamic",
    scale: int | None = None,
    # Legacy compat
    draw_chat_bubble: bool | None = None,
):
    """Render a complete scene and return a PIL Image.

    Args:
        emotion: one of the 16 emotion keys
        pose: pose key (shared or unique)
        environment: environment key, or None for no background
        outfit: outfit key, or None for no outfit
        frame_idx: animation frame (0-3 for standard 4-frame cycle)
        mode: "speaking" (character + bubble) or "idle" (full scene, no bubble)
        text_lines: number of text lines for dynamic bubble sizing
        text_width: pixel width of text for dynamic bubble sizing
        bubble_style: "dynamic" (sized to text) or "legacy" (fixed 170x70)
        scale: upscale factor (default: canvas.SCALE)
        draw_chat_bubble: deprecated, use mode="idle" instead

    Returns:
        PIL.Image in mode "1" (1-bit monochrome)
    """
    # Legacy compat
    if draw_chat_bubble is not None:
        mode = "speaking" if draw_chat_bubble else "idle"

    emo_cfg = EMOTIONS[emotion]
    pose_cfg = POSES.get(pose)

    # 1. Clear
    canvas.clear_frame()

    # 2. Environment background — always render full canvas.
    #    The chat bubble clears its own area on top when in speaking mode.
    if environment and environment in ENVIRONMENTS:
        env_cfg = ENVIRONMENTS[environment]
        try:
            env_cfg.draw_bg(frame_idx, mode="idle")
        except TypeError:
            env_cfg.draw_bg(frame_idx)

    # 3. Body transform (emotion-specific, then pose adjustments)
    canvas.reset_body_transform()
    if emo_cfg.setup_transform:
        emo_cfg.setup_transform(frame_idx)

    # 4. Body
    body_rle = _BODY_MAP.get(emo_cfg.body_key, BODY_RLE_STANDARD)
    if pose_cfg and pose_cfg.body_rle is not None:
        body_rle = pose_cfg.body_rle
    draw_body(body_rle)

    # Compute anchor points for outfit/aura (adjust for pose offset)
    face_off = (0, 0) if not pose_cfg else pose_cfg.face_anchor_offset
    dome_top = (35 + face_off[0], 10 + face_off[1])
    eye_centers = (
        (22 + face_off[0], 25 + face_off[1]),
        (48 + face_off[0], 25 + face_off[1]),
    )
    neck = (35 + face_off[0], 45 + face_off[1])
    body_center = (35 + face_off[0], 35 + face_off[1])

    # 5. Outfit (before face so face draws on top)
    if outfit and outfit in OUTFITS:
        OUTFITS[outfit].draw(
            dome_top=dome_top,
            eye_centers=eye_centers,
            neck=neck,
            body_center=body_center,
        )

    # 6. White eye sockets
    draw_eyes()

    # 7. Pupils
    if pose_cfg and pose_cfg.force_eyes_closed:
        from .emotions.faces import draw_lids_tired
        draw_lids_tired()
    elif emo_cfg.draw_pupils:
        emo_cfg.draw_pupils()

    # 8. Brows / lids / special eyes
    if emo_cfg.draw_brows:
        emo_cfg.draw_brows()
    if emo_cfg.draw_lids and not (pose_cfg and pose_cfg.force_eyes_closed):
        emo_cfg.draw_lids()
    if emo_cfg.draw_special_eyes:
        emo_cfg.draw_special_eyes()

    # 9. Tears
    if emo_cfg.draw_tears:
        emo_cfg.draw_tears()

    # 10. Mouth
    emo_cfg.draw_mouth()

    # 10b. Belly tentacle (lazy only)
    if emo_cfg.draw_belly:
        emo_cfg.draw_belly()

    # 11. Aura particles (Emotion Echo system)
    aura_key = emo_cfg.aura_key or emotion
    if aura_key in AURAS:
        AURAS[aura_key](body_center[0], body_center[1], frame_idx)

    # 12. Weather overlay
    # TODO: wire up environment.has_weather + emotion -> weather effect

    # 13. Chat bubble
    if mode == "speaking":
        if bubble_style == "legacy":
            draw_bubble_legacy()
        else:
            draw_bubble_dynamic(text_lines=text_lines, text_width=text_width)

    return canvas.frame_to_image(scale=scale)


def scene_address(emotion, pose, environment, outfit):
    """Return the canonical address string for a scene configuration."""
    env = environment or "none"
    out = outfit or "none"
    return f"{emotion}/{pose}/{env}/{out}"
