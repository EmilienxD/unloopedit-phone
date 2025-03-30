from lib.modules.paths import Path, PathLike, normpath, Trash, BASE_PATH
from lib.modules.files import TempFolderCleaner
from lib.modules.display import LoggerConfig


class VideoExportSettings:

    OPTIONS = {}

    # HQ ################################################################
    OPTIONS["HQ"] = {
        "quality": "HQ",
        "extension": ".mov",
        "container": "mov",
        "codec": "ProRes",
        "audio_codec": "acc"
    }

    # LT #########################################################
    OPTIONS["LT"] = {
        "quality": "LT",
        "extension": ".mov",
        "container": "mov",
        "codec": "ProRes",
        "audio_codec": "aac"
    }

    # CHQ ################################################################
    OPTIONS["CHQ"] = {
        "quality": "CHQ",
        "extension": ".mov",
        "container": "mov",
        "codec": "H264",
        "audio_codec": "aac"
    }
    
    # CLQ ################################################################
    OPTIONS["CLQ"] = {
        "quality": "CLQ",
        "extension": ".mov",
        "container": "mov",
        "codec": "H264",
        "audio_codec": "aac"
    }
    
    # PROXYQ ################################################################
    OPTIONS["PROXYQ"] = {
        "quality": "PROXYQ",
        "extension": ".mov",
        "container": "mov",
        "codec": "H264",
        "audio_codec": "aac"
    }

    # SMHQ ################################################################
    OPTIONS["SMHQ"] = {
        "quality": "SMHQ",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H264",
        "audio_codec": "aac"
    }

    # SMLQ ################################################################
    OPTIONS["SMLQ"] = {
        "quality": "SMLQ",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H264",
        "audio_codec": "aac"
    }

    # SMLAGQ ################################################################
    OPTIONS["SMLAGQ"] = {
        "quality": "SMLAGQ",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H265",
        "audio_codec": "aac"
    }
    
    # youtube ################################################################
    OPTIONS["youtube"] = {
        "quality": "youtube",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H264",
        "audio_codec": "aac"
    }

    # tiktok ################################################################
    OPTIONS["tiktok"] = {
        "quality": "tiktok",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H265",
        "audio_codec": "aac"
    }
 
    # instagram ################################################################
    OPTIONS["instagram"] = {
        "quality": "instagram",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H264",
        "audio_codec": "aac"
    }

    # x ################################################################
    OPTIONS["x"] = {
        "quality": "x",
        "extension": ".mp4",
        "container": "mp4",
        "codec": "H264",
        "audio_codec": "aac"
    }

    quality = "SMLQ"
    option = OPTIONS[quality]
    extension = option["extension"]
    container = option["container"]
    codec = option["codec"]
    audio_codec = option["audio_codec"]


class AudioExportSettings:

    OPTIONS = {}
    OPTIONS["LQ"] = {
        "extension": ".mp3",
        "container": "mp3",
        "codec": "libmp3lame"
    }

    option = OPTIONS["LQ"]
    extension = option["extension"]
    container = option["container"]
    codec = option["codec"]


class ImageExportSettings:

    OPTIONS = {}
    OPTIONS["HQ"] = {
        "extension": ".jpg",
        "container": "jpg"
    }
    OPTIONS["LQ"] = {
        "extension": ".png",
        "container": "png"
    }    
    
    option = OPTIONS["LQ"]
    extension = option["extension"]
    container = option["container"]


class Paths:

    BASE_PATH = BASE_PATH
    _paths: dict[str, any] = {}

    def __new__(cls, path: PathLike) -> PathLike:
        """Access to a tree path"""
        path = path if isinstance(path, str) else path.relative
        paths = cls._paths
        for path in normpath(path).split('\\'):
            if path not in paths:
                raise KeyError(f"The path '{path}' does not exist in the structure.")
            paths = paths[path]
        return paths['%folder_path%'] if isinstance(paths, dict) else paths

    @classmethod
    def _parse_structure(cls, structure: dict[str, any], base_path: PathLike, assert_exists: bool=True) -> dict[str, any]:
        """Recursively parse the JSON structure to build paths."""
        base_path = Path(base_path, 'Directory', assert_exists=assert_exists)
        paths = {}

        def add(path: PathLike, name: str, content: str):
            if path.is_file_path:
                paths[name] = path
            else:
                paths[name] = cls._parse_structure(content, path, assert_exists)
                paths[name]['%folder_path%'] = path.relative

        for name, content in structure.items():
            if isinstance(content, str):
                name += content    # Add extension for files

            path = base_path * name

            if isinstance(content, dict) and name == '%name%':
                [add(path, path.full_name, content) for path in base_path]
                continue
                        
            elif isinstance(content, str):
                path = Path(path, assert_exists=((not name.startswith('_')) and assert_exists)).relative
            
            add(path, name, content)
                
        return paths
    
    @classmethod
    def set_defaults(cls) -> None:
        if not cls._paths:
            cls._paths = cls._parse_structure(structure=Path('pathconfig.json', 'File', assert_exists=True).read(default={}), base_path='\\')          
    
    @classmethod
    def sub_tree(cls, tree_path: PathLike) -> dict[str, PathLike]:
        tree_path = tree_path if isinstance(tree_path, str) else tree_path.relative
        path_components = normpath(tree_path).split('\\')
        paths = cls._paths
        for item in path_components:
            if item not in paths:
                raise KeyError(f"The path '{item}' does not exist in the structure.")
            paths = paths[item]
        assert isinstance(paths, dict), f'No tree found for: {tree_path}'
        del paths['%folder_path%']
        return paths

Paths.set_defaults()

LoggerConfig.LOG_DIR_PATH = Paths('traceback/logs')
LoggerConfig.MAX_BACKUP_COUNT = 14

TEMP = TempFolderCleaner(temp_path=Paths('TEMP'), definitly=True, init_clear=True, uninit_clear=False)  # IMPORTANT: uninit_clear=False to prevent any clean up temp path conflict

Trash.set_trash_path(Paths('trash'))
Trash.auto_cleanup(days=3)

