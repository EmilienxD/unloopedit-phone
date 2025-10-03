import os
from dotenv import load_dotenv
from sys import platform

from src.modules.paths import Path, PathLike, Trash, BASE_PATH
from src.modules.files import TempFolderCleaner, remove_empty_folders
from src.modules.display import LoggerConfig, Logger


load_dotenv()


# IMPORTANT: uninit_clear=False to prevent any clean up temp path conflict
TEMP = TempFolderCleaner(temp_path='TEMP', definitly=True, init_clear=True, uninit_clear=False)

Trash.set_trash_path('TRASH')
Trash.auto_cleanup(days=3, max_size=0.8)

LoggerConfig.LEVEL = 'CRITICAL' if platform == 'darwin' else 'DEBUG'
LoggerConfig.LOG_DIR_PATH = Path('logs', 'Directory')
LoggerConfig.LOG_DIR_PATH(exist_ok=True)
LoggerConfig.MAX_BACKUP_COUNT = 14


logger = Logger('[Config]')


class Paths:

    PRIVATE_FILE_TEMPLATES = ['config', 'credentials', 'token']
    PRIVATE_FILE_EXTENSIONS = ['.json']
    BASE_PATH = BASE_PATH
    _paths: dict[str, PathLike | dict] = {}

    def __new__(cls, path: PathLike) -> PathLike:
        """Access to a tree path"""
        path = Path(path).relative
        paths = cls._paths
        for p in path.split_components():
            if p not in paths:
                raise KeyError(f"The path '{p}' does not exist in the structure.")
            paths = paths[p]
        return paths['%folder_path%'] if isinstance(paths, dict) else paths
    
    @classmethod
    def getenv(cls, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)

    @classmethod
    def setenv(cls, key: str, value: str) -> None:
        os.environ[key] = value

    @classmethod
    def _parse_structure(cls, structure: dict[str, PathLike | dict], base_path: PathLike, assert_exists: bool=True) -> dict[str, PathLike | dict]:
        """Recursively parse the JSON structure to build paths."""
        base_path = Path(base_path, 'Directory')

        if not base_path.exists:
            base_path(exist_ok=True)
            logger.warning(f'Project folder: "{base_path.relative}" not found -> added empty folder.')

        paths = {}

        def add(path: PathLike, name: str, content: str):
            if name in ('__pycache__',):
                return
            if path.is_file_path:
                paths[name] = path.relative

                if not path.exists:
                    if not name.startswith('_'):
                        path(exist_ok=True)
                        logger.warning(f'Project file: "{path.ufs}" not found -> added empty file.')
            else:
                paths[name] = cls._parse_structure(content, path, assert_exists)
                paths[name]['%folder_path%'] = path.relative

        for name, content in structure.items():
            if isinstance(content, str):
                name += content    # Add extension for files

            path = base_path * name

            if isinstance(content, dict) and name == '%name%':
                [add(path, path.full_name, content) for path in base_path]
            else:
                add(path, name, content)
                
        return paths
    
    @classmethod
    def set_defaults(cls) -> None:
        if not cls._paths:
            logger.info('Parsing project tree...')
            cls._paths = cls._parse_structure(structure=Path('pathconfig.json', 'File', assert_exists=True).read(default={}), base_path=BASE_PATH.fs)
        logger.info('Project tree up-to-date.')
    
    @classmethod
    def sub_tree(cls, tree_path: PathLike) -> dict[str, PathLike]:
        tree_path = Path(tree_path).relative
        path_components = tree_path.split_components()
        paths = cls._paths
        for item in path_components:
            if item not in paths:
                raise KeyError(f"The path '{item}' does not exist in the structure.")
            paths = paths[item]
        assert isinstance(paths, dict), f'No tree found for: {tree_path}'
        del paths['%folder_path%']
        return paths
    
    @classmethod
    def cleanup(cls) -> None:
        if not cls._paths:
            return
        # Clean empty folders
        target_empty_folders = [
            cls('content_created/FINAL')
        ]
        for p in target_empty_folders:
            remove_empty_folders(p)

        # Clean share point
        cls('sharepoint').clear(send_to_trash=True)

Paths.set_defaults()


class AudioExportSettings:

    OPTIONS = {}
    OPTIONS["LQ"] = {
        "extension": ".mp3",
        "codec": "aac",
        "params": [
            "-c:a", "aac",
            "-b:a", "96k"
        ]
    }


class ImageExportSettings:

    OPTIONS = {}
    OPTIONS["HQ"] = {
        "extension": ".jpg"
    }
    OPTIONS["LQ"] = {
        "extension": ".png"
    }


class VideoFFMPEGBuilder:

    EXTENSIONS = {
        "video": {".mp4", ".mov", ".mkv", ".avi", ".webm"},
        "audio": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"},
        "image": {".png", ".jpg", ".jpeg", ".heic", ".heif"}
    }

    PRESET_MAP = {
        "nvidia": {
            "ultrafast": "p1", "superfast": "p2", "veryfast": "p3",
            "faster": "p4", "fast": "p5", "medium": "p6",
            "slow": "p7", "veryslow": "p7"
        },
        "intel": {
            # QSV presets are driver dependent; using rough mapping
            "ultrafast": "veryfast", "superfast": "veryfast", "veryfast": "faster",
            "faster": "faster", "fast": "fast", "medium": "balanced",
            "slow": "slow", "veryslow": "slow"
        },
        "amd": {
            "ultrafast": "speed", "superfast": "speed", "veryfast": "speed",
            "faster": "balanced", "fast": "balanced", "medium": "quality",
            "slow": "quality", "veryslow": "quality"
        }
    }
    
    GPU_ENCODERS = {
        "nvidia": {
            "libx264": "h264_nvenc",
            "libx265": "hevc_nvenc"
        },
        "intel": {
            "libx264": "h264_qsv",
            "libx265": "hevc_qsv"
        },
        "amd": {
            "libx264": "h264_amf",
            "libx265": "hevc_amf"
        }
    }

    GPU_BITRATE_PARAMS = {
        "nvidia": ["-cq", "23"],
        "intel": ["-rc", "cqp", "-qp", "23"],
        "amd": ["-q:v", "23"]
    }

    UNSUPPORTED_PARAMS = {"-x264-params", "-x265-params", "-tune"}

    OPTIONS = {}

    # HQ ################################################################
    OPTIONS["HQ"] = {
        "extension": ".mov",
        "codec": "prores_ks",
        "audio_codec": "acc",
        "params": [
            "-c:v", "prores_ks",
            "-profile:v", "3",
            "-qscale:v", "1",
            "-pix_fmt", "yuv422p10le",
            "-movflags", "+faststart"
        ],
        "audio_params": [
            "-c:a", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2"
        ]
    }

    # LT #########################################################
    OPTIONS["LT"] = {
        "extension": ".mov",
        "codec": "prores_ks",
        "audio_codec": "aac",
        "params": [
            "-c:v", "prores_ks",
            "-profile:v", "1",  # LT profile
            "-qscale:v", "15",  # Lower quality
            "-pix_fmt", "yuv422p10le",
            "-movflags", "+faststart",
        ],
        "audio_params": [
            "-c:a", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2"
        ]
    }

    # CHQ ################################################################
    OPTIONS["CHQ"] = {
        "extension": ".mov",
        "codec": "libx264",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-b:v", "80M",
            "-maxrate", "90M",
            "-bufsize", "15M",
            "-rc-lookahead", "20",
            "-movflags", "+faststart"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "192k"
        ]
    }

    # CLQ ################################################################
    OPTIONS["CLQ"] = {
        "extension": ".mov",
        "codec": "libx264",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx264",
            "-preset", "medium",
            "-profile:v", "main",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            "-movflags", "+faststart",
            "-rc-lookahead", "20"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "96k"
        ]
    }

    # PROXYQ ################################################################
    OPTIONS["PROXYQ"] = {
        "extension": ".mov",
        "codec": "libx264",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "baseline",
            "-pix_fmt", "yuv420p",
            "-crf", "28",
            "-movflags", "+faststart"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "64k"
        ]
    }

    # youtube ################################################################
    OPTIONS["youtube"] = {
        "extension": ".mp4",
        "codec": "libx264",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            "-movflags", "+faststart"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "128k"
        ]
    }

    # tiktok ################################################################
    OPTIONS["tiktok"] = {
        "extension": ".mp4",
        "codec": "libx265",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx265",
            "-preset", "veryslow",
            "-profile:v", "main10",
            "-x265-params", "level=5.1",
            "-pix_fmt", "yuv420p10le",
            "-crf", "23",
            "-movflags", "+faststart",
            "-tag:v", "hvc1"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "128k"
        ]
    }

    # instagram ################################################################
    OPTIONS["instagram"] = {
        "extension": ".mp4",
        "codec": "libx264",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            "-movflags", "+faststart"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "128k"
        ]
    }

    # x ################################################################
    OPTIONS["x"] = {
        "extension": ".mp4",
        "codec": "libx264",
        "audio_codec": "aac",
        "params": [
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            "-movflags", "+faststart"
        ],
        "audio_params": [
            "-c:a", "aac",
            "-b:a", "128k"
        ]
    }
