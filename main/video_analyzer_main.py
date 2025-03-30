from _core import *


def main():
    from tkinter import filedialog
    from lib.modules.paths import Path
    from lib.config import Paths
    from video_analyzer import run

    paths = filedialog.askopenfilenames(filetypes=[("Audio and Video files", "*.mp4 *.mov")], initialdir=Paths.BASE_PATH.fs)
    if paths:
        run([','.join(Path(path, target_extensions=['.mp4', '.mov']).fs for path in paths)])


if __name__ == '__main__':
    main()

    