#!/usr/bin/env python3
"""Batch renderer — render scenes to the output/ directory tree.

Usage:
    # Render all emotions in standing pose, no environment
    python -m octopus.render_all

    # Render specific scene
    python -m octopus.render_all --emotion angry --pose ground_stomp --env kitchen --outfit chef_hat

    # Render all emotions x all environments grid
    python -m octopus.render_all --grid emotions_x_envs

    # Render all poses for one emotion
    python -m octopus.render_all --emotion sad --all-poses
"""

import argparse
import os
import sys

# Add parent dir to path so octopus package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from octopus.compose import render_scene, scene_address
from octopus.emotions import REGISTRY as EMOTIONS
from octopus.poses import REGISTRY as POSES, poses_for_emotion
from octopus.environments import REGISTRY as ENVIRONMENTS
from octopus.outfits import REGISTRY as OUTFITS

OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def render_single(emotion, pose="standing", env=None, outfit=None,
                   frame_idx=0, scale=4):
    """Render one scene and save to output tree."""
    img = render_scene(
        emotion=emotion, pose=pose, environment=env,
        outfit=outfit, frame_idx=frame_idx, scale=scale,
    )

    # Save by emotion
    emo_dir = os.path.join(OUT_ROOT, "by_emotion", emotion)
    ensure_dir(emo_dir)
    env_s = env or "none"
    out_s = outfit or "none"
    fname = f"{pose}_{env_s}_{out_s}.png"
    path = os.path.join(emo_dir, fname)
    img.save(path)
    return path


def render_all_standing(scale=4):
    """Render all 16 emotions in standing pose — the baseline set."""
    print("Rendering all emotions (standing, no env)...")
    for emo in EMOTIONS:
        path = render_single(emo, scale=scale)
        print(f"  {emo:12s} -> {path}")


def render_emotion_all_poses(emotion, scale=4):
    """Render all available poses for one emotion."""
    print(f"Rendering all poses for '{emotion}'...")
    available = poses_for_emotion(emotion)
    for pose in available:
        path = render_single(emotion, pose=pose, scale=scale)
        print(f"  {pose:20s} -> {path}")


def render_grid_emotions_x_envs(scale=2):
    """Render a grid: rows=emotions, cols=environments."""
    from PIL import Image

    emotions = list(EMOTIONS.keys())
    envs = list(ENVIRONMENTS.keys()) if ENVIRONMENTS else ["none"]
    if not envs or envs == ["none"]:
        envs = [None]

    cell_w = 250 * scale
    cell_h = 122 * scale
    cols = len(envs)
    rows = len(emotions)

    grid = Image.new("1", (cell_w * cols, cell_h * rows), color=1)

    for r, emo in enumerate(emotions):
        for c, env in enumerate(envs):
            img = render_scene(emotion=emo, environment=env, scale=scale)
            grid.paste(img, (c * cell_w, r * cell_h))

    grid_dir = os.path.join(OUT_ROOT, "grids")
    ensure_dir(grid_dir)
    path = os.path.join(grid_dir, "emotions_x_environments.png")
    grid.save(path)
    print(f"Grid -> {path} ({rows}x{cols})")


def main():
    parser = argparse.ArgumentParser(description="Batch render octopus scenes")
    parser.add_argument("--emotion", help="Emotion to render")
    parser.add_argument("--pose", default="standing", help="Pose key")
    parser.add_argument("--env", help="Environment key")
    parser.add_argument("--outfit", help="Outfit key")
    parser.add_argument("--frame", type=int, default=0, help="Frame index (0-3)")
    parser.add_argument("--scale", type=int, default=4, help="Upscale factor")
    parser.add_argument("--all-poses", action="store_true",
                        help="Render all poses for --emotion")
    parser.add_argument("--grid", choices=["emotions_x_envs"],
                        help="Render a comparison grid")
    parser.add_argument("--all", action="store_true",
                        help="Render all 16 emotions in standing pose")
    args = parser.parse_args()

    if args.grid:
        render_grid_emotions_x_envs(scale=args.scale)
    elif args.all:
        render_all_standing(scale=args.scale)
    elif args.emotion and args.all_poses:
        render_emotion_all_poses(args.emotion, scale=args.scale)
    elif args.emotion:
        path = render_single(
            args.emotion, args.pose, args.env, args.outfit,
            args.frame, args.scale,
        )
        print(f"Rendered -> {path}")
    else:
        render_all_standing(scale=args.scale)


if __name__ == "__main__":
    main()
