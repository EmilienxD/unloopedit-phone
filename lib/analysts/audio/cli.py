import argparse
from . import SongAnalyst


def run_analyst(args) -> list[dict]:
    song_paths = args.songs
    sanitize = args.sanitize

    if not song_paths:
        return []
    song_analyst = SongAnalyst()
    results = [song_analyst.analyze(song_path, sanitize=sanitize) for song_path in song_paths]
    for idx, result in enumerate(results):
        print(f"Result for {song_paths[idx]}:\n{result}")
    return results

def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Analyze a list of song files using SongAnalyst."
    )
    parser.add_argument(
        "songs",
        type=lambda ss: ss.split(","),
        help="Comma-separated list of song file paths to analyze.",
    )
    parser.add_argument(
        "--sanitize", "--s", "-sanitize", "-s",
        action="store_true",
        help="Flag to indicate if sanitization should be applied.",
    )

    return parser.parse_args(args)

def run(args=None):
    return run_analyst(parse_args(args))


if __name__ == "__main__":
    run()
