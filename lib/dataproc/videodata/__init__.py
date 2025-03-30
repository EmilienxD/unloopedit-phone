import typing as ty
from functools import wraps
from datetime import datetime, timedelta
from time import time

from lib.modules.display import Logger
from lib.modules.internal_script import get_func_kwargs_an

from lib.config import Paths
from lib import utils
from lib.dataproc.com import _ComE, _ComES, DBContext


P = ty.ParamSpec('P')
T = ty.TypeVar('T')


def obligatory(*items) -> ty.Callable[P, T]:
    """
    Decorator for video utility filter.
    Use it for an obligatory utility method filter.
    If the `Videodata` object dosn't have the given attributs, the video will be considered as an useless video.
    Do not use this decorator for functions not used to check video utility
    """
    def decorator(func: ty.Callable[P, T]) -> ty.Callable[P, T]:
        @wraps(func)
        def wrapper(self: 'VideoData', *args: P.args, **kwargs: P.kwargs) -> T:
            if all(getattr(self, item) for item in items):
                return func(self, *args, **kwargs)
            return False
        return wrapper
    return decorator

def optional(*items) -> ty.Callable[P, T]:
    """
    Decorator for video utility filter.
    Use it for an optional utility method filter.
    If the `Videodata` object dosn't have the given attributs, the video will be considered as a useful video.
    Do not use this decorator for functions not used to check video utility
    """
    def decorator(func: ty.Callable[P, T]) -> ty.Callable[P, T]:
        @wraps(func)
        def wrapper(self: 'VideoData', *args: P.args, **kwargs: P.kwargs) -> bool:
            if all(getattr(self, item) for item in items):
                return func(self, *args, **kwargs)
            return True
        return wrapper
    return decorator

def only_if_downloaded(func: ty.Callable[P, T]) -> ty.Callable[P, T]:
    """
    Use this decorator if the function need the video to be downloaded, to be executed
    """
    @wraps(func)
    def wrapper(self: 'VideoData', *args: P.args, **kwargs: P.kwargs) -> T:
        if self.is_downloaded:
            return func(self, *args, **kwargs)
        raise ValueError(f"Function '{func.__name__}' bloqued | video {self.path.relative} need to be downloaded") 
    return wrapper


class StatussType(type):
    def __contains__(cls, item):
        return item in cls.__dict__.values()

class Statuss(metaclass=StatussType):
    PROCESSING = 0
    FLAGGED = 1
    READY = 2
    DONE = 3
    ALL: dict[str, int]

Statuss.ALL = {name: value for name, value in Statuss.__dict__.items() 
                if not name.startswith('_') and isinstance(value, int)}

class VideoData(_ComE):

    _E: 'VideoData'
    Statuss = Statuss

    def __init__(self,
            id: str = None,
            metadata: str = None,
            status: int | None = Statuss.PROCESSING,
            wid: str = None,
            source: str = None,
            author: str = None,
            url: str = None,
            description: str = None,
            title: str = None,
            publication_date: str = None,
            type: str = None,
            views: int = None,
            likes: int = None,
            total_comms: int = None,
            comms: list[str] = None,
            hashtags: list[str] = None,
            song_id: str = None,
            found_by: str = None,
            OCR: str = None,
            width: int = None,
            height: int = None,
            duration: float = None,
            fps: float = None,
            niche: str = None,
            analysis: str = None,
            keywords: list[str] = None,
            scenes_data: list[dict] = None,
            auto_save: bool = False
            ):
        super().__init__(id, auto_save)
        self.metadata = metadata or ''
        self.set_status(status)
        self.wid = wid
        self.source = source
        self.author = author
        self.url = url or utils.build_url(self.source, self.author, self.wid)
        if not self.url:
            raise TypeError(f'url must be setted for: {self}')
        elif not (self.source or self.author or self.wid):
            source, author, wid = utils.extract_video_info(self.url)
            self.source = self.source or source
            self.author = self.author or author
            self.wid = self.wid or wid            

        self.path = (Paths('content_saved/downloaded/videos')
                                     * utils.url_to_filename(self.url, '.mp4'))
        self.description = description or ''
        self.title = title or ''
        self.publication_date = publication_date or self.id
        self.type = type or ''
        self.views = views or 0
        self.likes = likes or 0
        self.total_comms = total_comms or 0
        self.comms = comms or []
        self.hashtags = hashtags or []
        self.song_id = song_id or ''
        self.found_by = found_by or ''
        self.OCR = OCR or ''
        self.width = width or 0
        self.height = height or 0
        self.duration = duration or 0.0
        self.fps = fps or 0.0
        self.niche = niche or ''
        self.analysis = analysis or ''
        self.keywords = keywords or []
        self.scenes_data = scenes_data or []

    @classmethod
    def create_indexs(cls) -> None:
        with cls.DBContext:
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status ON "{cls._TABLE_NAME}" (status);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_niche ON "{cls._TABLE_NAME}" (niche);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status_niche ON "{cls._TABLE_NAME}" (status, niche);''')
            cls._db.commit()

    def __eq__(self, other: 'VideoData') -> bool:
        return super().__eq__(other) and hasattr(other, 'wid') and self.wid == other.wid

    def __hash__(self):
        return hash(self.id + self.wid)

    @property
    def is_downloaded(self) -> bool:
        return self.path.exists
    
    def update_status(self) -> None:
        if self.status in (self.Statuss.READY, self.Statuss.DONE) and not self.is_downloaded:
            self.set_status(self.Statuss.FLAGGED)

    @property
    def is_standardized(self) -> bool:
        """
        Checks if the video is standardized.
        """
        return (self.width, self.height) in (size for reso in utils.STANDARD_SIZES.values() for size in reso)

    @property
    def time_since_publication(self) -> timedelta:
        """
        Calculates the time since the video was published.

        Returns:
        -------
            timedelta: The time since the video was published.
        """
        return datetime.now() - utils.str_to_date(self.publication_date)
    
    @property
    def lang_clue(self) -> list[str]:
        lang_clue = []
        if self.title:
            lang_clue.append(self.title)
        if self.description:
            lang_clue.append(self.description)
        if self.comms:
            lang_clue.extend([hashtag.replace('_', ' ').strip() for hashtag in self.hashtags if len(hashtag) > 3 and not '@' in hashtag])
        return lang_clue

    @optional('duration')
    def has_correct_duration(self, min_duration: float | None = None, max_duration: float | None = None) -> bool:
        if min_duration is None or max_duration is None:
            return True
        return min_duration <= self.duration <= max_duration
    
    @optional('fps')
    def has_correct_fps(self, min_fps: float | None = None, max_fps: float | None = None) -> bool:
        if min_fps is None or max_fps is None:
            return True
        return min_fps <= self.fps <= max_fps
    
    @optional('width', 'height')
    def has_correct_size(self, min_width: int | None = None, max_width: int | None = None, min_height: int | None = None, max_height: int | None = None) -> bool:
        if min_width is None or max_width is None or min_height is None or max_height is None:
            return True
        return min_width <= self.width <= max_width and min_height <= self.height <= max_height

    @optional('publication_date')
    def is_popular_by_publication_date(self, min_age_in_hours: int | None = None, max_age_in_days: int | None = None) -> bool:
        """
        Checks if the video is popular based on its publication date.

        Parameters:
        ----------
            min_age_in_hours (int): Minimum age of the video in hours.
            max_age_in_days (int): Maximum age of the video in days.

        Returns:
        -------
            bool: True if the video is popular based on its publication date, False otherwise.
        """
        if min_age_in_hours is None or max_age_in_days is None:
            return True
        return timedelta(hours=min_age_in_hours) <= self.time_since_publication <= timedelta(days=max_age_in_days)
    
    @obligatory('views')
    def is_popular_by_views(self, min_views_day: int | None = None, views_reach: int | None = None) -> bool:
        """
        Checks if the video is popular based on its views.

        Parameters:
        ----------
            min_views_day (tuple[int]): Minimum ratio of views per day.
            views_reach (int): Minimum number of views to be considered popular.

        Returns:
        -------
            bool: True if the video is popular based on its views, False otherwise.
        """
        if views_reach is not None and self.views >= views_reach:
            return True
        
        if min_views_day is None:
            return True

        return self.views / max(self.time_since_publication.days, 1) >= min_views_day    # To avoid division by zero

    @optional('likes')
    def is_popular_by_likes(self, min_likes_day: int | None = None, likes_reached: int | None = None) -> bool:
        """
        Checks if the video is popular based on its likes.

        Parameters:
        ----------
            min_ratio_likes_days (tuple[int]): Minimum ratio of likes per day.
            likes_reached (int): Minimum number of likes to be considered popular.

        Returns:
        -------
            bool: True if the video is popular based on its likes, False otherwise.
        """
        if likes_reached is not None and self.views >= likes_reached:
            return True
        
        if min_likes_day is None:
            return True

        return self.likes / max(self.time_since_publication.days, 1) >= min_likes_day    # To avoid division by zero

    @optional('comms')
    def is_popular_by_comms(self, min_comms_day: int | None = None, comms_reached: int | None = None) -> bool:
        """
        Checks if the video is popular based on its comments.

        Parameters:
        ----------
            min_ratio_comms_days (tuple[int]): Minimum ratio of comments per day.
            comms_reached (int): Minimum number of comments to be considered popular.

        Returns:
        -------
            bool: True if the video is popular based on its comments, False otherwise.
        """
        if comms_reached is not None and self.views >= comms_reached:
            return True
        
        if min_comms_day is None:
            return True

        return self.total_comms / max(self.time_since_publication.days, 1) >= min_comms_day   # To avoid division by zero
    
    def is_popular(self,
        min_age_in_hours: int | None = None, 
        max_age_in_days: int | None = None, 
        min_views_day: int | None = None, 
        views_reach: int | None = None,
        min_likes_day: int | None = None, 
        likes_reached: int | None = None, 
        min_comms_day: int | None = None, 
        comms_reached: int | None = None
    ) -> bool:
        return (self.is_popular_by_publication_date(min_age_in_hours, max_age_in_days) and
                self.is_popular_by_views(min_views_day, views_reach) and
                self.is_popular_by_likes(min_likes_day, likes_reached) and
                self.is_popular_by_comms(min_comms_day, comms_reached))

    def delete(self,
            remove_file: bool = True,
            remove_wid: bool = True,
            send_to_trash: bool = False,
            not_exists_ok: bool = True
        ) -> None:
        super().delete(
            remove_file=remove_file,
            send_to_trash=send_to_trash,
            not_exists_ok=not_exists_ok
        )

    def ban(self,
            remove_file: bool = True,
            send_to_trash: bool = False,
            not_exists_ok: bool = True
        ) -> None:
        self.delete(
            remove_file=remove_file,
            remove_wid=False,
            send_to_trash=send_to_trash,
            not_exists_ok=not_exists_ok
        )
    
    def set_status(self, status: int = Statuss.PROCESSING) -> None:
        assert status in self.Statuss, f'Invalid status: {status}'
        self.status = status     

    @only_if_downloaded
    def ai_analyze(self,
        initial_api_key: str | None = None,
        max_retries: int = 1,
        auth_save: bool = True,
        increment_key_usage: bool = True,
        rotate_key: bool = True,
        timeline: list[tuple[float, float]] | None = None,
        setter: bool = True
    ) -> dict:
        from lib.analysts.video import VideoAnalyst
        ai_analyst = VideoAnalyst(initial_api_key=initial_api_key,
                                  response_schema=VideoAnalyst.MODE.VIDEODATA.OUT(),
                                  max_retries=max_retries,
                                  auth_save=auth_save)
        ai_analyst.login()
        ai_analyst.start_chat()
        video_file = ai_analyst.upload_file(self.path)

        t_start = time()

        params = self.as_dict.copy()

        if timeline is not None:
            params['timeline'] = timeline

        data = ai_analyst.analyze(
            video_file,
            query=VideoAnalyst.MODE.VIDEODATA.IN(**params),
            sleep_time=max(0, ai_analyst.DEFAULT_UPLOAD_TIME - time() + t_start),
            response_delay_limit=300,
            increment_key_usage=increment_key_usage,
            rotate_key=rotate_key
        )
        if any(k not in data for k in ['analysis', 'keywords', 'scenes_data']):
            raise ValueError(f'Invalid data from analyzer')

        if setter:
            self.analysis: str = data['analysis']
            self.keywords: list[str] = data['keywords']
            self.scenes_data: list[dict] = data['scenes_data']
        return data
    
    @only_if_downloaded
    async def ai_analyze_async(self,
        initial_api_key: str | None = None,
        max_retries: int = 1,
        auth_save: bool = True,
        increment_key_usage: bool = True,
        rotate_key: bool = True,
        timeline: list[tuple[float, float]] | None = None,
        setter: bool = True
    ) -> dict:
        from lib.analysts.video import VideoAnalyst
        ai_analyst = VideoAnalyst(initial_api_key=initial_api_key,
                                  response_schema=VideoAnalyst.MODE.VIDEODATA.OUT(),
                                  max_retries=max_retries,
                                  auth_save=auth_save)
        ai_analyst.login()
        ai_analyst.start_chat()
        video_file = ai_analyst.upload_file(self.path)

        t_start = time()

        params = self.as_dict.copy()

        if timeline is not None:
            params['timeline'] = timeline

        data = await ai_analyst.analyze_async(
            video_file,
            query=VideoAnalyst.MODE.VIDEODATA.IN(**params),
            sleep_time=max(0, ai_analyst.DEFAULT_UPLOAD_TIME - time() + t_start),
            response_delay_limit=180,
            increment_key_usage=increment_key_usage,
            rotate_key=rotate_key
        )
        if any(k not in data for k in ['analysis', 'keywords', 'scenes_data']):
            raise ValueError(f'Invalid data from analyzer')

        if setter:
            self.analysis: str = data['analysis']
            self.keywords: list[str] = data['keywords']
            self.scenes_data: list[dict] = data['scenes_data']
        return data


class UListVideoDatas(_ComES[VideoData]):

    Statuss = Statuss

    @classmethod
    def from_videos_items(cls, videos_items: list[dict[str, ty.Any]]) -> 'UListVideoDatas':
        """
        Creates a UListVideoDatas instance from a list of video items.

        Parameters:
        ----------
            videos_items (list[dict[str, any]]): List of video items.

        Returns:
        -------
            UListVideoDatas: A UListVideoDatas instance.
        """
        return cls(VideoData(**video_items) for video_items in videos_items)

    @property
    def wid(self) -> list[str]:
        return [v.wid for v in self._elements]

    @property
    def url(self) -> list[str]:
        return [v.url for v in self._elements]

    @property
    def source(self) -> list[str]:
        return [v.source for v in self._elements]
    
    @source.setter 
    def source(self, value: str) -> None:
        for v in self._elements:
            v.source = value

    @property
    def author(self) -> list[str]:
        return [v.author for v in self._elements]
    
    @author.setter 
    def author(self, value: str) -> None:
        for v in self._elements:
            v.author = value
    
    @property
    def type(self) -> list[str]:
        return [v.type for v in self._elements]
    
    @type.setter
    def type(self, value: str) -> None:
        for v in self._elements:
            v.type = value

    @property
    def description(self) -> list[str]:
        return [v.description for v in self._elements]
    
    @description.setter
    def description(self, value: str) -> None:
        for v in self._elements:
            v.description = value

    @property
    def title(self) -> list[str]:
        return [v.title for v in self._elements]
    
    @title.setter
    def title(self, value: str) -> None:
        for v in self._elements:
            v.title = value

    @property
    def publication_date(self) -> list[str]:
        return [v.publication_date for v in self._elements]
    
    @publication_date.setter
    def publication_date(self, value: str) -> None:
        for v in self._elements:
            v.publication_date = value

    @property
    def views(self) -> list[int]:
        return [v.views for v in self._elements]
    
    @views.setter
    def views(self, value: int) -> None:
        for v in self._elements:
            v.views = value

    @property
    def likes(self) -> list[int]:
        return [v.likes for v in self._elements]
    
    @likes.setter
    def likes(self, value: int) -> None:
        for v in self._elements:
            v.likes = value

    @property
    def total_comms(self) -> list[int]:
        return [v.total_comms for v in self._elements]
    
    @total_comms.setter
    def total_comms(self, value: int) -> None:
        for v in self._elements:
            v.total_comms = value

    @property
    def comms(self) -> list[list[str]]:
        return [v.comms for v in self._elements]
    
    @comms.setter
    def comms(self, value: list[str]) -> None:
        for v in self._elements:
            v.comms = value

    @property
    def hashtags(self) -> list[list[str]]:
        return [v.hashtags for v in self._elements]
    
    @hashtags.setter
    def hashtags(self, value: list[str]) -> None:
        for v in self._elements:
            v.hashtags = value

    @property
    def found_by(self) -> list[str]:
        return [v.found_by for v in self._elements]
    
    @found_by.setter
    def found_by(self, value: str) -> None:
        for v in self._elements:
            v.found_by = value

    @property
    def OCR(self) -> list[str]:
        return [v.OCR for v in self._elements]
    
    @OCR.setter
    def OCR(self, value: str) -> None:
        for v in self._elements:
            v.OCR = value

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
    def duration(self) -> list[float]:
        return [v.duration for v in self._elements]
    
    @duration.setter
    def duration(self, value: int) -> None:
        for v in self._elements:
            v.duration = value

    @property
    def fps(self) -> list[float]:
        return [v.fps for v in self._elements]
    
    @fps.setter
    def fps(self, value: float) -> None:
        for v in self._elements:
            v.fps = value

    @property
    def niche(self) -> list[str]:
        return [v.niche for v in self._elements]
    
    @niche.setter
    def niche(self, value: str) -> None:
        for v in self._elements:
            v.niche = value

    @property
    def is_downloaded(self) -> list[bool]:
        return [v.is_downloaded for v in self._elements]

    @property
    def is_standardized(self) -> list[bool]:
        return [v.is_standardized for v in self._elements]
    
    @is_standardized.setter
    def is_standardized(self, value: bool) -> None:
        for v in self._elements:
            v.is_standardized = value
   
    def update_status(self) -> None:
        [v.update_status() for v in self._elements]
    
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
    def scenes_data(self) -> list[list[dict]]:
        return [v.scenes_data for v in self._elements]
    
    @scenes_data.setter
    def scenes_data(self, value: list[dict]) -> None:
        for v in self._elements:
            v.scenes_data = value

    @property
    def time_since_publication(self) -> list[bool]:
        return [v.time_since_publication for v in self._elements]

    @property
    def lang_clue(self) -> list[list[str]]:
        return [v.lang_clue for v in self._elements]
    
    @property
    def status(self) -> list[bool]:
        return [v.status for v in self._elements]
    
    @status.setter
    def status(self, value: bool) -> None:
        for v in self._elements:
            v.set_status(value)

    def set_status(self, status: int = Statuss.PROCESSING) -> None:
        [v.set_status(status) for v in self._elements]

    def has_correct_duration(self, min_duration: float | None = None, max_duration: float | None = None) -> list[bool]:
        return [v.has_correct_duration(min_duration, max_duration) for v in self._elements]

    def is_popular_by_publication_date(self, min_age_in_hours: int | None = None, max_age_in_days: int | None = None) -> list[bool]:
        """
        Checks if each video is popular based on its publication date.

        Parameters:
        ----------
            min_age_in_hours (int, optional): Minimum age of the video in hours. Defaults to 5.
            max_age_in_days (int, optional): Maximum age of the video in days. Defaults to 730.

        Returns:
        -------
            list[bool]: A list of booleans indicating if each video is popular based on its publication date.
        """
        return [v.is_popular_by_publication_date(min_age_in_hours, max_age_in_days) for v in self._elements]

    def is_popular_by_views(self, min_ratio_views_days: tuple[int, int] | None = None, views_reach: int | None = None) -> list[bool]:
        """
        Checks if each video is popular based on its views.

        Parameters:
        ----------
            min_ratio_views_days (tuple[int, int], optional): Minimum ratio of views per day. Defaults to (4000, 1).
            views_reach (int, optional): Minimum number of views to be considered popular. Defaults to 100000.

        Returns:
        -------
            list[bool]: A list of booleans indicating if each video is popular based on its views.
        """
        return [v.is_popular_by_views(min_ratio_views_days, views_reach) for v in self._elements]

    def is_popular_by_likes(self, min_ratio_likes_days: tuple[int, int] | None = None, likes_reached: int | None = None) -> list[bool]:
        """
        Checks if each video is popular based on its likes.

        Parameters:
        ----------
            min_ratio_likes_days (tuple[int, int], optional): Minimum ratio of likes per day. Defaults to (300, 1).
            likes_reached (int, optional): Minimum number of likes to be considered popular. Defaults to 50000.

        Returns:
        -------
            list[bool]: A list of booleans indicating if each video is popular based on its likes.
        """
        return [v.is_popular_by_likes(min_ratio_likes_days, likes_reached) for v in self._elements]

    def is_popular_by_comms(self, min_ratio_comms_days: tuple[int, int] | None = None, comms_reached: int | None = None) -> list[bool]:
        """
        Checks if each video is popular based on its comments.

        Parameters:
        ----------
            min_ratio_comms_days (tuple[int, int], optional): Minimum ratio of comments per day. Defaults to (10, 1).
            comms_reached (int, optional): Minimum number of comments to be considered popular. Defaults to 300.

        Returns:
        -------
            list[bool]: A list of booleans indicating if each video is popular based on its comments.
        """
        return [v.is_popular_by_comms(min_ratio_comms_days, comms_reached) for v in self._elements]
    
    def is_popular(self,
        min_age_in_hours: int | None = None, 
        max_age_in_days: int | None = None, 
        min_ratio_views_days: tuple[int] | None = None, 
        views_reach: int | None = None,
        min_ratio_likes_days: tuple[int] | None = None, 
        likes_reached: int | None = None, 
        min_ratio_comms_days: tuple[int] | None = None, 
        comms_reached: int | None = None
    ) -> list[bool]:
        return [v.is_popular(
            min_age_in_hours, max_age_in_days,
            min_ratio_views_days, views_reach,
            min_ratio_likes_days, likes_reached,
            min_ratio_comms_days, comms_reached
        ) for v in self._elements]

    @classmethod
    def sync_files(cls, send_to_trash: bool = False) -> None:
        video_paths = cls.load().path
        for p in Paths('content_saved/downloaded/videos'):
            if p not in video_paths:
                p.remove(send_to_trash=send_to_trash)
                cls.logger.warn(f'Unsyncronized file: {p.relative} removed.')


VideoData._E = UListVideoDatas._E = VideoData
VideoData._TABLE_NAME = UListVideoDatas._TABLE_NAME = VideoData.__name__
VideoData.logger = UListVideoDatas.logger = Logger('[VideoData]')
VideoData.DBContext = UListVideoDatas.DBContext = DBContext(VideoData)

VideoData._sdata = get_func_kwargs_an(VideoData.__init__)
del VideoData._sdata['id']
del VideoData._sdata['auto_save']

VideoData.create_table()
VideoData.create_indexs()


