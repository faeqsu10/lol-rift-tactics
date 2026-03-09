from __future__ import annotations

import os
import sys

from .runtime import project_root

PROJECT_ROOT = project_root()
VENDORED_AUDIO_LIB_DIR = PROJECT_ROOT / ".vendor" / "pulse" / "extracted" / "usr" / "lib" / "x86_64-linux-gnu"
VENDORED_AUDIO_PLUGIN_DIR = VENDORED_AUDIO_LIB_DIR / "pulseaudio"


def bootstrap_audio_runtime() -> None:
    if os.environ.get("RIFT_AUDIO_BOOTSTRAPPED") == "1":
        return

    if os.environ.get("SDL_AUDIODRIVER") in {"dummy", "disk"}:
        return

    if not os.environ.get("PULSE_SERVER"):
        return

    if not (VENDORED_AUDIO_LIB_DIR / "libpulse.so.0").exists():
        return

    current_paths = [path for path in os.environ.get("LD_LIBRARY_PATH", "").split(":") if path]
    required_paths = [str(VENDORED_AUDIO_LIB_DIR), str(VENDORED_AUDIO_PLUGIN_DIR)]
    missing_paths = [path for path in required_paths if path not in current_paths]

    if not missing_paths and os.environ.get("SDL_AUDIODRIVER") in {"pulseaudio", "pulse"}:
        return

    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ":".join(required_paths + current_paths)
    env["SDL_AUDIODRIVER"] = "pulseaudio"
    env["RIFT_AUDIO_BOOTSTRAPPED"] = "1"
    os.execvpe(sys.executable, [sys.executable, "-m", "native_game", *sys.argv[1:]], env)


def main() -> None:
    bootstrap_audio_runtime()
    from .app import GameApp, build_parser

    parser = build_parser()
    args = parser.parse_args()
    app = GameApp(headless=args.headless)
    app.run(max_frames=args.frames, screenshot_path=args.screenshot)


if __name__ == "__main__":
    main()
