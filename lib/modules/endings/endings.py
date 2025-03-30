"""
This module offers functions for ending tasks:
opening directories in Windows Explorer, playing video files using specific applications, and playing audio notifications.
It leverages functions from the `files` module and external libraries like `subprocess` and `pygame` to perform these tasks.
Only work on Windows.

Functions:
---------
    open_dir:
        Opens a directory in Windows Explorer.
    play_video:
        Plays a video using a specified application (VLC, Windows Media Player, or auto-detection based on file extension).
    avert_success:
        Plays a success sound notification.
    close:
        Closes the audio mixer.
"""

from os import system
from subprocess import run, Popen

from lib.modules.paths import PathLike, Path
from lib.modules.display import Logger



logger = Logger('[endings]')


def open_dir(dir_or_file_path: PathLike) -> None:
    """
    Opens a directory in Windows Explorer.

    Parameters:
    ----------
        dir_or_file_path (str): The path to the directory or file.
    """
    dir_or_file_path = Path(dir_or_file_path, reset_instance=False)
    if dir_or_file_path.is_file_path:
        run(['explorer', '/select,', dir_or_file_path.fs], shell=True)
    else:
        run(['explorer', dir_or_file_path.fs], shell=True)

def play_video(video_path: PathLike, app: str='auto', opening_dir=False) -> None:
    """
    Plays a video using a specified application.

    Parameters:
    ----------
        video_path (str): The path to the video file.
        app (str): The application to use ('vlc', 'wmplayer', or 'auto').
        opening_dir (bool): If True, opens the directory containing the video before playing it.

    Video players available:
    -----------------------
        vlc (.mov files)
        wmplayer (.mp4 files)
        auto (an app that can play the video)
    """
    apps_path = {
        'vlc': Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe", 'File'),
        'wmplayer': Path(r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe", 'File')
    }

    assert all([app_path.exists for app_path in apps_path.values()]), 'Invalid apps_path, need to update paths.'

    video_path = Path(video_path, 'File', reset_instance=False)
    ext = video_path.extension
    apps_path['auto'] = apps_path['wmplayer'] if ext == '.mp4' else (apps_path['vlc'] if ext == '.mov' else None)

    app = app.lower()
    app_path = apps_path[app] if app in apps_path else None

    if app_path is not None:
        if opening_dir:
            open_dir(video_path)

        Popen([app_path.fs, video_path.fs])
    else:
        system(video_path.fs)

def play_audio(audio_path: PathLike) -> None:
    """
    Plays an audio file.
    """
    audio_path = Path(audio_path, 'File', reset_instance=False)
    assert audio_path.extension in ['.mp3', '.wav', '.ogg', '.flac', '.mp4', '.mov'], 'Invalid audio file.'
    system(audio_path.fs)


