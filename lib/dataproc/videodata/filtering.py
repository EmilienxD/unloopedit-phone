from lib.modules.display import Logger

from lib.config import Paths
from . import UListVideoDatas


logger = Logger('[FILTER]')

DEFAULT_SETTINGS = Paths('lib/dataproc/videodata/filtering_settings.json').read(default={})


def complete_filter_videos(
        videos: UListVideoDatas,
        min_duration: float | None = None,
        max_duration: float | None = None,
        min_fps: float | None = None,
        max_fps: float | None = None,
        min_width: int | None = None,
        min_height: int | None = None,
        max_width: int | None = None,
        max_height: int | None = None,
        excluded_langs: list[str] | None = None,
        min_age_in_hours: int | None = None, 
        max_age_in_days: int | None = None, 
        min_ratio_views_days: tuple[int] | None = None, 
        views_reach: int | None = None,
        min_ratio_likes_days: tuple[int] | None = None, 
        likes_reached: int | None = None, 
        min_ratio_comms_days: tuple[int] | None = None, 
        comms_reached: int | None = None          
    ) -> tuple[UListVideoDatas, UListVideoDatas, UListVideoDatas]:
    """
    Used to filters videos into useful and useless videos based on various metrics.
    IMPORTANT: Every VideoData attributes not setted wouldn't do anything if they are optional else the video is automaticly considered as useless

    Parameters:
    ----------
        videos (UListVideoDatas): List of VideoData objects to filter
        min_duration (float): Minimum duration of the video in seconds to be considered
        max_duration (float): Maximum duration of the video in seconds to be considered
        min_fps (float): Minimum fps of the video to be considered
        max_fps (float): Maximum fps of the video to be considered
        min_width (int): Minimum width of the video to be considered
        min_height (int): Minimum height of the video to be considered
        max_width (int): Maximum width of the video to be considered
        max_height (int): Maximum height of the video to be considered
        excluded_langs (list[str]): List of languages to exclude
        min_age_in_hours (int): Minimum age of the video in hours to be considered
        max_age_in_days (int): Maximum age of the video in days to be considered
        min_ratio_views_days (tuple[int]): Minimum ratio of views to days
        views_reach (int): Views threshold where any video above this is considered useful regardless of ratio
        min_ratio_likes_days: (tuple[int]) Minimum ratio of likes to days
        likes_reached (int): Likes threshold where any video above this is considered useful regardless of ratio
        min_ratio_comms_days (tuple[int]): Minimum ratio of comments to days
        comms_reached (int): Comments threshold where any video above this is considered useful regardless of ratio

    Returns:
    -------
        tuple[UListVideoDatas, UListVideoDatas]: useful videos and useless videos which are VideoData objects
    """
    logger.info(f'Filtering data ({len(videos)} VideoData objects)...')
    good_videos = videos.copy()
    bad_videos = UListVideoDatas()
    for source in set(videos.source):
        min_duration = DEFAULT_SETTINGS[source]['min_duration'] if min_duration is None else min_duration
        max_duration = DEFAULT_SETTINGS[source]['max_duration'] if max_duration is None else max_duration
        min_fps = DEFAULT_SETTINGS[source]['min_fps'] if min_fps is None else min_fps
        max_fps = DEFAULT_SETTINGS[source]['max_fps'] if max_fps is None else max_fps
        min_width = DEFAULT_SETTINGS[source]['min_width'] if min_width is None else min_width
        min_height = DEFAULT_SETTINGS[source]['min_height'] if min_height is None else min_height
        max_width = DEFAULT_SETTINGS[source]['max_width'] if max_width is None else max_width
        max_height = DEFAULT_SETTINGS[source]['max_height'] if max_height is None else max_height
        excluded_langs = DEFAULT_SETTINGS[source]['excluded_langs'] if excluded_langs is None else excluded_langs
        min_age_in_hours = DEFAULT_SETTINGS[source]['min_age_in_hours'] if min_age_in_hours is None else min_age_in_hours
        max_age_in_days = DEFAULT_SETTINGS[source]['max_age_in_days'] if max_age_in_days is None else max_age_in_days
        min_ratio_views_days = DEFAULT_SETTINGS[source]['min_ratio_views_days'] if min_ratio_views_days is None else min_ratio_views_days
        views_reach = DEFAULT_SETTINGS[source]['views_reach'] if views_reach is None else views_reach
        min_ratio_likes_days = DEFAULT_SETTINGS[source]['min_ratio_likes_days'] if min_ratio_likes_days is None else min_ratio_likes_days
        likes_reached = DEFAULT_SETTINGS[source]['likes_reached'] if likes_reached is None else likes_reached
        min_ratio_comms_days = DEFAULT_SETTINGS[source]['min_ratio_comms_days'] if min_ratio_comms_days is None else min_ratio_comms_days
        comms_reached = DEFAULT_SETTINGS[source]['comms_reached'] if comms_reached is None else comms_reached
        for video in videos.filter_attrs(source=source):
            if not (video.has_correct_duration(min_duration, max_duration) and
                    video.has_correct_fps(min_fps, max_fps) and
                    video.has_correct_size(min_width, max_width, min_height, max_height) and
                    video.has_correct_lang(excluded_langs) and
                    video.is_popular_by_publication_date(min_age_in_hours, max_age_in_days) and
                    video.is_popular_by_views(min_ratio_views_days, views_reach) and
                    video.is_popular_by_likes(min_ratio_likes_days, likes_reached) and
                    video.is_popular_by_comms(min_ratio_comms_days, comms_reached)):
                bad_videos.append(video)
                good_videos.remove(video)

    logger.info(f'{len(good_videos)}/{len(videos)} good VideoData objects filtered')
    return good_videos, bad_videos, videos

def popularity_filter_videos(
            videos: UListVideoDatas,
            excluded_langs: list[str] | None = None,
            min_age_in_hours: int | None = None, 
            max_age_in_days: int | None = None, 
            min_ratio_views_days: tuple[int] | None = None, 
            views_reach: int | None = None,
            min_ratio_likes_days: tuple[int] | None = None, 
            likes_reached: int | None = None, 
            min_ratio_comms_days: tuple[int] | None = None, 
            comms_reached: int | None = None
        ) -> tuple[UListVideoDatas, UListVideoDatas, UListVideoDatas]:
    """
    Used to filters videos into useful and useless videos based on various metrics.
    IMPORTANT: Every VideoData attributes not setted wouldn't do anything if they are optional else the video is automaticly considered as useless

    Parameters:
    ----------
        videos (UListVideoDatas): List of VideoData objects to filter
        excluded_langs (list[str]): List of languages to exclude
        min_age_in_hours (int): Minimum age of the video in hours to be considered
        max_age_in_days (int): Maximum age of the video in days to be considered
        min_ratio_views_days (tuple[int]): Minimum ratio of views to days
        views_reach (int): Views threshold where any video above this is considered useful regardless of ratio
        min_ratio_likes_days: (tuple[int]) Minimum ratio of likes to days
        likes_reached (int): Likes threshold where any video above this is considered useful regardless of ratio
        min_ratio_comms_days (tuple[int]): Minimum ratio of comments to days
        comms_reached (int): Comments threshold where any video above this is considered useful regardless of ratio

    Returns:
    -------
        tuple[UListVideoDatas, UListVideoDatas]: useful videos and useless videos which are VideoData objects
    """
    logger.info(f'Filtering data ({len(videos)} VideoData objects)...')
    good_videos = videos.copy()
    bad_videos = UListVideoDatas()
    for source in set(videos.source):
        excluded_langs = DEFAULT_SETTINGS[source]['excluded_langs'] if excluded_langs is None else excluded_langs
        min_age_in_hours = DEFAULT_SETTINGS[source]['min_age_in_hours'] if min_age_in_hours is None else min_age_in_hours
        max_age_in_days = DEFAULT_SETTINGS[source]['max_age_in_days'] if max_age_in_days is None else max_age_in_days
        min_ratio_views_days = DEFAULT_SETTINGS[source]['min_ratio_views_days'] if min_ratio_views_days is None else min_ratio_views_days
        views_reach = DEFAULT_SETTINGS[source]['views_reach'] if views_reach is None else views_reach
        min_ratio_likes_days = DEFAULT_SETTINGS[source]['min_ratio_likes_days'] if min_ratio_likes_days is None else min_ratio_likes_days
        likes_reached = DEFAULT_SETTINGS[source]['likes_reached'] if likes_reached is None else likes_reached
        min_ratio_comms_days = DEFAULT_SETTINGS[source]['min_ratio_comms_days'] if min_ratio_comms_days is None else min_ratio_comms_days
        comms_reached = DEFAULT_SETTINGS[source]['comms_reached'] if comms_reached is None else comms_reached
        for video in videos.filter_attrs(source=source):
            if not (video.has_correct_lang(excluded_langs) and
                    video.is_popular_by_publication_date(min_age_in_hours, max_age_in_days) and
                    video.is_popular_by_views(min_ratio_views_days, views_reach) and
                    video.is_popular_by_likes(min_ratio_likes_days, likes_reached) and
                    video.is_popular_by_comms(min_ratio_comms_days, comms_reached)):
                bad_videos.append(video)
                good_videos.remove(video)

    logger.info(f'{len(good_videos)}/{len(videos)} good VideoData objects filtered')
    return good_videos, bad_videos, videos

def quality_filter_videos(
        videos: UListVideoDatas,
        min_duration: float | None = None,
        max_duration: float | None = None,
        min_fps: float | None = None,
        max_fps: float | None = None,
        min_width: int | None = None,
        min_height: int | None = None,
        max_width: int | None = None,
        max_height: int | None = None
    ) -> tuple[UListVideoDatas, UListVideoDatas, UListVideoDatas]:
    """
    Used to filters videos into useful and useless videos based on various metrics.
    This function can work even if the videos are not downloaded yet thanks to the extracted web data, but it can be less accurate.

    Parameters:
    ----------
        videos (UListVideoDatas): List of VideoData objects to filter
        min_duration (float): Minimum duration of the video in seconds to be considered
        max_duration (float): Maximum duration of the video in seconds to be considered
        min_fps (float): Minimum fps of the video to be considered
        max_fps (float): Maximum fps of the video to be considered
        min_width (int): Minimum width of the video to be considered
        min_height (int): Minimum height of the video to be considered
        max_width (int): Maximum width of the video to be considered
        max_height (int): Maximum height of the video to be considered
    """
    logger.info(f'Filtering data ({len(videos)} VideoData objects)...')
    good_videos = videos.copy()
    bad_videos = UListVideoDatas()
    for source in set(videos.source):
        min_duration = DEFAULT_SETTINGS[source]['min_duration'] if min_duration is None else min_duration
        max_duration = DEFAULT_SETTINGS[source]['max_duration'] if max_duration is None else max_duration
        min_fps = DEFAULT_SETTINGS[source]['min_fps'] if min_fps is None else min_fps
        max_fps = DEFAULT_SETTINGS[source]['max_fps'] if max_fps is None else max_fps
        min_width = DEFAULT_SETTINGS[source]['min_width'] if min_width is None else min_width
        min_height = DEFAULT_SETTINGS[source]['min_height'] if min_height is None else min_height
        max_width = DEFAULT_SETTINGS[source]['max_width'] if max_width is None else max_width
        max_height = DEFAULT_SETTINGS[source]['max_height'] if max_height is None else max_height
        for video in videos.filter_attrs(source=source):
            if not (video.has_correct_duration(min_duration, max_duration) and
                    video.has_correct_fps(min_fps, max_fps) and
                    video.has_correct_size(min_width, max_width, min_height, max_height)):
                bad_videos.append(video)
                good_videos.remove(video)

    logger.info(f'{len(good_videos)}/{len(videos)} good VideoData objects filtered')
    return good_videos, bad_videos, videos

def type_filter_videos(
        videos: UListVideoDatas,
        types_target: list[str] = ['short', 'live', 'caroussel']
    ) -> tuple[UListVideoDatas, UListVideoDatas, UListVideoDatas]:
    """
    Used to filters videos into useful and useless videos based on various metrics.
    This function can work even if the videos are not downloaded yet thanks to the extracted web data, but it can be less accurate.

    Parameters:
    ----------
        videos (UListVideoDatas): List of VideoData objects to filter
    """
    logger.info(f'Filtering data ({len(videos)} VideoData objects)...')
    good_videos = videos.copy()
    bad_videos = UListVideoDatas()
    for video in videos:
        if not (video.type in types_target):
            bad_videos.append(video)
            good_videos.remove(video)

    logger.info(f'{len(good_videos)}/{len(videos)} good VideoData objects filtered')
    return good_videos, bad_videos, videos