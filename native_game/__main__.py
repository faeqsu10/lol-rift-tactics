from __future__ import annotations

from .app import GameApp, build_parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    app = GameApp(headless=args.headless)
    app.run(max_frames=args.frames, screenshot_path=args.screenshot)


if __name__ == "__main__":
    main()
