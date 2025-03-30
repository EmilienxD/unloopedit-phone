import typing as ty

from lib.modules.paths import PathLike
from lib.modules.display import Logger
from lib.modules.internal_script import get_func_kwargs_an

from lib.config import Paths, VideoExportSettings
from lib import utils
from lib.dataproc.videodata import VideoData
from lib.dataproc.com import _ComE, _ComES, DBContext


class Scene:

    def __init__(self,
            parent_pack: 'ScenePack',
            fname: str = '',
            t_start: float = 0.0,
            t_end: float = float('inf'),
            analysis: str = '',
            usage: int = 0
        ) -> None:
        self.parent_pack = parent_pack
        self.fname = fname or (utils.create_unique_date() + VideoExportSettings.OPTIONS['HQ']['extension'])
        self.usage = usage
        self.t_start = t_start
        self.t_end = t_end
        self.analysis = analysis

    def increase_usage(self, increase_value: int = 1) -> None:
        self.usage += increase_value

    def remove(self, send_to_trash: bool = True, not_exists_ok: bool = True):
        self.path.remove(send_to_trash, not_exists_ok)

    def delete(self, send_to_trash: bool = True, not_exists_ok: bool = True):
        self.parent_pack.scenes.remove(self)
        self.parent_pack.total_duration -= self.duration
        self.parent_pack.total_usage -= self.usage
        self.parent_pack.count -= 1
        self.path.remove(send_to_trash, not_exists_ok)
        self.parent_pack.logger.info(f"{self} deleted.")

    def info(self) -> str:
        info = f'{self.__class__.__name__}:\n'
        for attr_name, attr_value in self.as_dict.items():
            info += f' - {attr_name}: {attr_value}\n'
        sep_bar = '_' * 80
        info += '\n' + sep_bar + '\n' + info + sep_bar + '\n'
        return info
    
    @property
    def path(self) -> PathLike:
        return self.parent_pack.path * (self.fname)
    
    @property
    def duration(self) -> float:
        return self.t_end - self.t_start

    @property
    def is_proxy(self) -> bool:
        if not self.path.exists:
            return False
        if max(utils.get_video_size(self.path)) <= 240:
            return True
        return False

    @property
    def as_dict(self) -> dict[str, ty.Any]:
        return {
            'analysis': self.analysis,
            't_start': self.t_start,
            't_end': self.t_end,
            'usage': self.usage
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(pack={self.parent_pack}, fname={self.fname})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, scene: 'Scene') -> bool:
        return self.fname == scene.fname

    def __hash__(self) -> int:
        return hash(self.fname)
    

class StatussType(type):
    def __contains__(cls, item):
        return item in cls.__dict__.values()

class Statuss(metaclass=StatussType):
    PROCESSING = 0
    FLAGGED = 1
    PROXY_READY = 2
    PROXY_DONE = 3
    READY = 4
    DONE = 5
    ALL: dict[str, int]

Statuss.ALL = {name: value for name, value in Statuss.__dict__.items() 
                if not name.startswith('_') and isinstance(value, int)}

class ScenePack(_ComE):

    _E: 'ScenePack'
    Statuss = Statuss
    DEFAULT_QUALITY = 'CHQ'

    def __init__(self,
            id: str = None,
            metadata: str = None,
            status: int | None = Statuss.PROCESSING,
            width: int = None,
            height: int = None,
            fps: float = None,
            total_duration: float = None,
            total_usage: int = None,
            count: int = None,
            niche: str = None,
            analysis: str = None,
            keywords: list[str] = None,
            scenes_data: dict[str, dict] = None,
            str_vref: str = None,
            auto_save = False
        ):
        super().__init__(id, auto_save)
        self.metadata = metadata or ''
        self.width = width or 0
        self.height = height or 0
        self.fps = fps or 0.0
        self.total_duration = total_duration or 0.0
        self.total_usage = total_usage or 0
        self.count = count or 0
        self.niche = niche or ''
        self.analysis = analysis or ''
        self.keywords = keywords or []

        self.path = Paths('content_created/local_scenepacks') * self.id

        self.scenes_data = scenes_data   # Set self.scenes with property setter

        self.str_vref = str_vref         # Set self.vref with property setter

        self.set_status(status)

    @property
    def is_exported(self) -> bool:
        return self.path.exists
    
    @property
    def scenes_data(self) -> dict[str, dict]:
        return {scene.fname: scene.as_dict for scene in self.scenes}
    
    @scenes_data.setter
    def scenes_data(self, scenes_data: dict[str, dict] | None) -> None:
        self.scenes = sorted((Scene(parent_pack=self, fname=fname,
                                    t_start=items.get('t_start', 0), t_end=items.get('t_end', float('inf'))
                        ,           analysis=items.get('analysis', ''), usage=items.get('usage', 0),
                        ) for fname, items in (scenes_data or {}).items()),
                        key=lambda s: utils.str_to_date(s.fname.split('.')[0]))
    
    @property
    def str_vref(self) -> str | None:
        return str(self.vref.path.relative) if self.vref else ''
    
    @str_vref.setter
    def str_vref(self, str_vref: str | None) -> None:
        # Try to load videodata ref, else use video file or None
        self.vref = (VideoData.load(url=utils.filename_to_url(str_vref))
                     if str_vref and (str(str_vref).lower() != 'none') else None)

        if self.vref is not None:
            if not self.analysis: self.analysis = self.vref.analysis
            if not self.keywords: self.keywords = self.vref.keywords
            if not self.scenes_data: self.scenes_data = self.vref.scenes_data
    
    @classmethod
    def create_indexs(cls) -> None:
        with cls.DBContext:
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status ON "{cls._TABLE_NAME}" (status);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_niche ON "{cls._TABLE_NAME}" (niche);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status_niche ON "{cls._TABLE_NAME}" (status, niche);''')
            cls._db.commit()
    
    def __len__(self) -> int:
        return len(self.scenes)
    
    def __iter__(self) -> ty.Iterator[Scene]:
        return iter(self.scenes)

    def scenes_info(self) -> str:
        return '\n'.join(s.info() for s in self.scenes)
    
    @property
    def to_timeline(self) -> list[tuple[float, float]]:
        return [(s.t_start, s.t_end) for s in self.scenes]
    
    def set_status(self, status: int = Statuss.PROCESSING, ban_vref: bool = True) -> None:
        assert status in self.Statuss, f'Invalid status: {status}'
        self.status = status
        if ban_vref and self.vref and self.status == self.Statuss.DONE:
            self.vref.ban(
                remove_file=True,
                send_to_trash=True
            )
    
    def ai_analyze(self,
            timeline: list[tuple[float, float]] | None = None,
            setter: bool = True
        ) -> dict:
        if self.vref is None:
            raise ValueError("ScenePack's video reference need to be setted and exists.")
        
        if getattr(ScenePack, '_video_analyst', None) is None:
            from lib.analysts.video import VideoAnalyst
            ScenePack._video_analyst = VideoAnalyst(response_schema=VideoAnalyst.MODE.SCENEPACK.OUT())
            ScenePack._video_analyst.login()

        params = self.vref.as_dict.copy()

        if timeline is None:
            if self.scenes:
                params['timeline'] = self.to_timeline
        else:
            params['timeline'] = timeline

        ScenePack._video_analyst.start_chat()
        data = ScenePack._video_analyst.analyze(
            video_path=self.vref.path,
            query=VideoAnalyst.MODE.SCENEPACK.IN(**params)
        )
        if setter:
            [setattr(self, k, v) for k, v in data.items() if hasattr(self, k)]
        return data


class UListScenePacks(_ComES[ScenePack]):

    Statuss = Statuss

    @property
    def status(self) -> list[str]:
        return [v.status for v in self._elements]
    
    @status.setter
    def status(self, value: bool) -> None:
        for v in self._elements:
            v.set_status(value)
    
    @property
    def vref(self) -> list[VideoData]:
        return [v.vref for v in self._elements]
    
    @property
    def width(self) -> list[int]:
        return [v.width for v in self._elements]
    
    @width.setter
    def width(self, value: int) -> None:
        for v in self._elements:
            v.width = value
    
    @property
    def height(self) -> list[int]:
        return [v.height for v in self._elements]
    
    @height.setter
    def height(self, value: int) -> None:
        for v in self._elements:
            v.height = value

    @property
    def total_duration(self) -> list[float]:
        return [v.total_duration for v in self._elements]
    
    @total_duration.setter
    def total_duration(self, value: float) -> None:
        for v in self._elements:
            v.total_duration = value

    @property
    def fps(self) -> list[float]:
        return [v.fps for v in self._elements]
    
    @fps.setter
    def fps(self, value: float) -> None:
        for v in self._elements:
            v.fps = value
    
    @property
    def count(self) -> list[int]:
        return [v.count for v in self._elements]
    
    @count.setter
    def count(self, value: int) -> None:
        for v in self._elements:
            v.count = value
    
    @property
    def niche(self) -> list[list[str]]:
        return [v.niche for v in self._elements]
    
    @niche.setter
    def niche(self, value: list[str]) -> None:
        for v in self._elements:
            v.niche = value
    
    @property
    def analysis(self) -> list[str]:
        return [v.analysis for v in self._elements]
    
    @analysis.setter
    def analysis(self, value: str) -> None:
        for v in self._elements:
            v.analysis = value
    
    @property
    def keywords(self) -> list[str]:
        return [v.keywords for v in self._elements]
    
    @keywords.setter
    def keywords(self, value: list[str]) -> None:
        for v in self._elements:
            v.keywords = value
    
    @property
    def scenes(self) -> list[list[Scene]]:
        return [v.scenes for v in self._elements]
    
    def scenes_info(self) -> str:
        return "\n".join(v.scenes_info() for v in self._elements) + f"\nTotal: {sum(len(e) for e in self._elements)}"

    def ai_analyze(self,
        threshold: int = 25,
        nbr_clips_limit: int = 100,
        min_clip_time: float | None = None,
        max_clip_time: float | None = None
    ) -> list[dict]:
        return [v.ai_analyze(threshold, nbr_clips_limit, min_clip_time, max_clip_time)
                for v in self._elements]
    
    @classmethod
    def sync_files(cls, send_to_trash: bool = False) -> None:
        scenepacks = cls.load()
        scenepack_paths = scenepacks.path

        for p in Paths('content_created/local_scenepacks'):
            if p not in scenepack_paths:
                p.remove(send_to_trash=send_to_trash)
                cls.logger.warn(f'Unsyncronized file: {p.relative} removed.')
        

ScenePack._E = UListScenePacks._E = ScenePack
ScenePack._TABLE_NAME = UListScenePacks._TABLE_NAME = ScenePack.__name__
ScenePack.logger = UListScenePacks.logger = Logger('[ScenePack]')
ScenePack.DBContext = UListScenePacks.DBContext = DBContext(ScenePack)

ScenePack._sdata = get_func_kwargs_an(ScenePack.__init__)
del ScenePack._sdata['id']
del ScenePack._sdata['auto_save']

ScenePack.create_table()
ScenePack.create_indexs()
