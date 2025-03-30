import argparse
from lib.analysts.video import VideoAnalyst


def run_analyst(args) -> list[dict]:
    video_paths = args.videos

    if not video_paths:
        return []
    
    with VideoAnalyst() as video_analyst:
        results = [video_analyst.analyze(video_path) for video_path in video_paths]
    
    for idx, result in enumerate(results):
        print(f"Result for {video_paths[idx]}:\n{result}")
    return results

def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Analyze a list of video files using VideoAnalyst."
    )
    parser.add_argument(
        "videos",
        type=lambda ss: ss.split(","),
        help="Comma-separated list of video file paths to analyze.",
    )

    return parser.parse_args(args)

def run(args=None):
    return run_analyst(parse_args(args))


if __name__ == "__main__":
    run()
