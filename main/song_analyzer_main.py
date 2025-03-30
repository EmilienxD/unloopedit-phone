from _core import *


def main():
    from tkinter import filedialog, messagebox
    from lib.modules.paths import get_source_path
    from lib.config import Paths
    from song_analyzer import run

    sanitize = messagebox.askyesno('Sanitize', "Sanitize output?")
    paths = filedialog.askopenfilenames(filetypes=[("Audio and Video files", "*.mp3 *.m4a")], initialdir=Paths.BASE_PATH.fs)
    if paths:
        args = [','.join(get_source_path(path, target_extensions=['.mp3', '.m4a']).fs for path in paths)]
        if sanitize:
            args.append('-s')
        run(args)


if __name__ == '__main__':
    main()

