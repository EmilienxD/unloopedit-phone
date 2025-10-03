import asyncio

from datetime import timedelta
from enum import Enum

from src.modules.paths import PathLike, Path
from src.modules.display import Logger
from src.modules.internal_script import GlobalPostLoad, classproperty

from src.cloud.megacloud import MegaCloud

from src.config import Paths, VideoFFMPEGBuilder
from src import utils
from src.dataproc.com import _ComE, _ComES, DBContext

from src.uploaders import UPLOADERS
from src.dataproc.accounts import get_platforms
from src.niches import COMMON_NICHE, Niche


class Global(metaclass=GlobalPostLoad):
    mega: MegaCloud
    def mega() -> MegaCloud:
        mega = MegaCloud(Paths.getenv('MEGA_UNIQUENAME'))
        mega.login()
        mega.create_folder('content_automation/_auto_')
        return mega
    mega: MegaCloud


class Statuses(Enum):
    BANNED = 'BANNED'
    PROCESSING = DEFAULT = 'PROCESSING'
    FLAGGED = 'FLAGGED'
    READY = 'READY'
    DONE = 'DONE'


class UploadStatuses(Enum):
    UNPROCESSED = DEFAULT = 'UNPROCESSED'
    READY = 'READY'
    INITIATED = 'INITIATED'
    SKIPPED = 'SKIPPED'
    UPLOADED = 'UPLOADED'


class _M:

    logger = Logger('[MyVideo]')
    parent_path = Paths('content_created/FINAL')
    statuses: type[Statuses] = Statuses
    _cache = set()
    uploadstatuses: type[UploadStatuses] = UploadStatuses
    DEFAULT_QUALITY = 'HQ'
    DEFAULT_CLOUD = 'mega'

    @classproperty
    def EXT(cls) -> str:
        return VideoFFMPEGBuilder.OPTIONS[cls.DEFAULT_QUALITY]['extension']

    @classmethod
    def create_indexs(cls) -> None:
        with cls.DBContext:
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status ON "{cls._TABLE_NAME}" (status);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_account ON "{cls._TABLE_NAME}" (account);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status_account ON "{cls._TABLE_NAME}" (status, account);''')
            cls._db.commit()


class MyVideo(_M, _ComE):

    def __init__(self,
            id: str = None,
            creation_date: str | None = None,
            metadata: str = None,
            status: str = None,
            niche: str = None,
            account: str = None,   # uniquename
            urls: list[str] = None,
            long_description: str = None,
            description: str = None,
            hashtags: list[str] = None,
            OCR: str = None,
            scene_ids: list[str] = None,
            publication_dates: dict[str, str] = None,
            auto_save: bool = False,
            auto_delete: bool = False
        ):
        super().__init__(id, creation_date, metadata, status, auto_save=auto_save, auto_delete=auto_delete)
        
        self.urls = urls or []
        self.long_description = long_description or ''
        self.description = description or ''
        self.hashtags = hashtags or []
        self.OCR = OCR or ''
        self.niche = niche or ''

        self.publication_dates: dict[str, str] = publication_dates or {}
        if self.status == self.statuses.DONE and not self.publication_dates:
            self.publication_dates = {u.name: utils.date_to_str() for u in self.uploaders}
    
        self.account = account or ''

        self.scene_ids = scene_ids or []
        self._scenes = None

        self.path = self.parent_path * self.id
        self.uncompressed_path = self.path * (f"{self.id}_uncompressed{VideoFFMPEGBuilder.OPTIONS[self.DEFAULT_QUALITY]['extension']}")

        self.status = self.status    # Use property setter for updates

    @property
    def account(self) -> str:
        return self._account
    
    @account.setter
    def account(self, value: str) -> None:
        unsafe_chars = set(r' %&?#[]{}<>\\^`"\'|@:+,;=')
        if any(char in unsafe_chars for char in value):
            raise ValueError(f"Unsafe account name: '{value}' not allowed.")
        self._account = value

    @property
    def niche(self) -> str:
        return self._niche
    
    @niche.setter
    def niche(self, niche: str | Enum) -> str:
        if isinstance(niche, str):
            niche = niche.upper()
        elif isinstance(niche, Enum):
            niche = niche.value
        if niche and (niche != COMMON_NICHE):
            assert niche in (n.value for n in Niche), f'Target niche: {niche} not in allowed niches: {", ".join((n.value for n in Niche))}'
            self._niche = Niche[niche].value if isinstance(niche, str) else niche.value
        else:
            self._niche = COMMON_NICHE

    def update_status(self) -> None:
        # Can not use self.exists had the upload process can come from a cloud
        # MyVideo with no uploaders can not be treated, and even more considered as posted
        if (((self.status == self.statuses.DONE and (not self.is_posted)))):
            self._status = self.statuses.FLAGGED
        elif self.uploaders and self.is_posted:
            self._status = self.statuses.DONE

    def delete(self, archive = False, remove_file = True, send_to_trash = False, not_exists_ok = True):
        self.delete_from_mega(skip_errors=True)
        return super().delete(archive, remove_file=remove_file, send_to_trash=send_to_trash, not_exists_ok=not_exists_ok)

    def banned(self) -> None:
        self.update_status()
        if self.status != self.statuses.BANNED:
            return
        self.delete(archive=False, remove_file=True, send_to_trash=True, not_exists_ok=True)
    
    def done(self) -> None:
        self.update_status()
        if self.status != self.statuses.DONE:
            return
        
        valid_dates = []
        for d in self.publication_dates.values():
            try:
                d = utils.str_to_date(d)
            except ValueError:
                continue
            valid_dates.append(d)

        # Use (not self.publication_dates) to prevent removing videos with only initiated statuses (invalid date format)
        if (not self.publication_dates) or ((max(valid_dates) + timedelta(days=31)) < utils.str_to_date()):
            self.delete(archive=False, remove_file=True, send_to_trash=True, not_exists_ok=True)

    def update_data(self) -> None:
        self.update_status()

    @property
    def valid_publication_dates(self) -> dict[str, str]:
        valid_dates = {}
        for pl, d in self.publication_dates.items():
            try:
                utils.str_to_date(d)
            except ValueError:
                continue
            valid_dates[pl] = d
        return valid_dates

    @property
    def caption(self) -> str:
        return f"{self.description}{''.join(' #' + h for h in self.hashtags)}".strip()

    @property
    def is_exported(self) -> bool:
        return self.uncompressed_path.exists
    
    @property
    def uploaders(self):
        return [u for u in UPLOADERS if self.account in u.get_account_uniquenames()]
    
    @property
    def unprocessed_uploaders(self):
        processed_platforms = [p for p, date in self.publication_dates.items() if date]    # Filter initiated
        return [u for u in self.uploaders if u.name not in processed_platforms]
    
    @property
    def is_posted(self) -> bool:
        if (not self.uploaders) or (not self.publication_dates):
            return False
        
        uploader_names = {u.name for u in self.uploaders}

        for pl, date in self.publication_dates.items():
            if not date:
                return False
            elif pl in uploader_names:
                uploader_names.remove(pl)
        return not uploader_names
    
    def cancel_post(self, platform: str) -> bool:
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'
        if platform not in {u.name for u in self.uploaders}:
            return None
        
        self.remove_url(platform)

        st = False
        if platform in self.publication_dates:
            self.publication_dates.pop(platform)
            st = True
            
        if self.status == self.statuses.DONE:
            self.status = self.statuses.READY
        
        return st

    def initiate_post(self, platform: str, skip_on_exists: bool = True, cloud: str | None = 'default') -> bool | None:
        # Try forcing READY status, auto update will handle setted status
        if self.status != self.statuses.READY:
            self.status = self.statuses.READY
        if self.status != self.statuses.READY:
            return False
        
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'
        if platform not in {u.name for u in self.uploaders}:
            return None
        
        if cloud == 'default':
            cloud = self.DEFAULT_CLOUD

        if cloud == 'mega':
            self.send_to_mega([platform], skip_on_exists=skip_on_exists)

        if self.get_upload_status(platform) == self.uploadstatuses.INITIATED:
            return False
    
        self.publication_dates[platform] = ''
        return True

    def register_post(self, platform: str, date: str = '') -> bool | None:
        # Try forcing READY status, auto update will handle setted status
        if self.status != self.statuses.READY:
            self.status = self.statuses.READY
        if self.status != self.statuses.READY:
            return False

        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'
        if platform not in {u.name for u in self.uploaders}:
            return None
        
        if self.get_upload_status(platform) == self.uploadstatuses.UPLOADED:
            return False
        
        date = date or utils.date_to_str()
        self.publication_dates[platform] = date

        if self.is_posted:
            self.status = self.statuses.DONE

        return True
    
    def skip_post(self, platform: str) -> bool | None:
        # Try forcing READY status, auto update will handle setted status
        if self.status != self.statuses.READY:
            self.status = self.statuses.READY
        if self.status != self.statuses.READY:
            return False

        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'
        if platform not in {u.name for u in self.uploaders}:
            return None
        
        self.remove_url(platform)

        if self.get_upload_status(platform) == self.uploadstatuses.SKIPPED:
            return False
        
        self.publication_dates[platform] = 'skipped'

        if self.is_posted:
            self.status = self.statuses.DONE

        return True
    
    def get_upload_status(self, platform: str) -> UploadStatuses:
        if not platform:
            return self.uploadstatuses.UNPROCESSED
        
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'

        if platform in self.publication_dates:
            date = self.publication_dates[platform]
            if not date:
                return self.uploadstatuses.INITIATED
            try:
                utils.str_to_date(date)
                return self.uploadstatuses.UPLOADED
            except ValueError:
                # Use any placeholders to indicate that the post was skipped (not empty, but invalid date)
                return self.uploadstatuses.SKIPPED

        elif self.path.exists:
            for p in self.path:
                if p.full_name == self.get_post_filename(platform):
                    return self.uploadstatuses.READY

        return self.uploadstatuses.UNPROCESSED
    
    def get_converted_path(self, platform: str, assert_exists: bool = False) -> PathLike | None:
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'

        p = self.path * self.get_post_filename(platform)

        if assert_exists and not p.exists:
            raise FileNotFoundError(f'{platform} converted video not found.')
        
        return p
    
    def get_post_filename(self, platform: str) -> str:
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'

        return f"{platform}={self.account}={self.id}{VideoFFMPEGBuilder.OPTIONS[platform]['extension']}"    
        
    def get_post_info(self, platform: str) -> dict:
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'

        return {
            "id": self.id,
            "platform": platform,
            "account": self.account,
            "caption": self.caption,
            "song": ""    # TODO: Add song
        }
    
    def get_url(self, platform: str) -> str | None:
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'

        for url in self.urls:
            if platform == utils.extract_video_info(url)[0]:
                return url
        return None
    
    def add_url(self, url: str, override: bool = True) -> str | None:
        platform = utils.extract_video_info(url)[0]
        if not platform:
            return None
        if (existing_url := self.get_url(platform)) is not None:
            if override:
                self.urls.remove(existing_url)
            else:
                return existing_url
        self.urls.append(url)
        return url
    
    def remove_url(self, platform: str) -> str | None:
        platform = platform.lower()
        assert platform in get_platforms(), f'Invalid platform: {platform}'

        url_found = None
        for url in self.urls:
            if platform == utils.extract_video_info(url)[0]:
                url_found = url
                break
        if url_found is not None:
            self.urls.remove(url_found)
        return url_found
    
    async def send_to_mega_async(self,
            platforms: str | list[str] | None = None,
            skip_on_exists: bool = True,
            max_concurrent: int = 6
        ) -> None:
        if platforms is None:
            platforms = [u.name for u in self.uploaders]

        elif platforms:
            if isinstance(platforms, str):
                platforms = [platforms]
        
            [pl.lower() for pl in platforms]
            assert all(pl in get_platforms() for pl in platforms), f'Invalid platform'
        else:
            return

        max_concurrent = max(1, max_concurrent or 1)
        sema = asyncio.Semaphore(max_concurrent)
        cloud_path = Path(f'content_automation/_auto_/{self.path.name}', 'Directory')

        async def task(p: PathLike, cp: PathLike):
                async with sema:
                    if ((not skip_on_exists) or (not Global.mega.exists(cp))):
                        await Global.mega.upload_async(p, cp, max_concurrent=max_concurrent,
                                                       overwrite=(not skip_on_exists), send_to_trash=True,
                                                       exists_ok=skip_on_exists)
        
        tasks = []
        #tasks.append(task(self.uncompressed_path, cloud_path * self.uncompressed_path.full_name))
        for pl in platforms:
            p = self.get_converted_path(pl)
            if p.exists:
                tasks.append(task(p, cloud_path * p.full_name))

        if tasks:
            Global.mega.create_folder(cloud_path, exists_ok=True)        
            await asyncio.gather(*tasks)

    def send_to_mega(self, platforms: str | list[str] | None = None, skip_on_exists: bool = True, max_concurrent: int = 6) -> None:
        asyncio.run(self.send_to_mega_async(platforms=platforms, skip_on_exists=skip_on_exists, max_concurrent=max_concurrent))

    async def download_from_mega_async(self,
            platforms: str | list[str] | None = None,
            overwrite: bool = True,
            max_concurrent: int = 6,
            skip_errors: bool = True
        ) -> None:
        if platforms is None:
            platforms = get_platforms()

        elif platforms:
            if isinstance(platforms, str):
                platforms = [platforms]
        
            [pl.lower() for pl in platforms]
            assert all(pl in get_platforms() for pl in platforms), f'Invalid platform'
        else:
            return

        max_concurrent = max(1, max_concurrent or 1)
        sema = asyncio.Semaphore(max_concurrent)
        cloud_path = Path(f'content_automation/_auto_/{self.path.name}', 'Directory')

        self.path(exist_ok=True)

        async def task(cp: PathLike, p: PathLike):
            async with sema:
                try:
                    await Global.mega.download_async(
                        cloud_path=cp,
                        path=p,
                        overwrite=True,
                        send_to_trash=False,
                        max_concurrent=max_concurrent
                    )
                except FileNotFoundError as e:
                    if not skip_errors:
                        raise
                    self.logger.warning(f'Error downloading from Mega: {e}')

        tasks = []
        #if overwrite or (not self.is_exported): tasks.append(task(cloud_path * self.uncompressed_path.full_name, self.uncompressed_path))

        for u in self.uploaders:
            p = self.get_converted_path(u.name)
            if p and (overwrite or (not p.exists)):
                tasks.append(task(cloud_path * p.full_name, p))

        if tasks:
            await asyncio.gather(*tasks)

    def download_from_mega(self,
            platforms: str | list[str] | None = None,
            overwrite: bool = True,
            max_concurrent: int = 6,
            skip_errors: bool = True
        ) -> None:
        asyncio.run(self.download_from_mega_async(
            platforms=platforms,
            overwrite=overwrite,
            max_concurrent=max_concurrent,
            skip_errors=skip_errors
        ))
    
    def delete_from_mega(self,
            platforms: str | list[str] | None = None,
            send_to_trash: bool = True,
            skip_errors: bool = True
        ) -> None:
        cloud_path = Path(f'content_automation/_auto_/{self.path.name}', 'Directory')

        if platforms is None:
            Global.mega.delete(cloud_path, send_to_trash=send_to_trash, skip_errors=skip_errors)
            return

        elif platforms:
            if isinstance(platforms, str):
                platforms = [platforms]
        
            [pl.lower() for pl in platforms]
            assert all(pl in get_platforms() for pl in platforms), f'Invalid platform'
        else:
            return

        for pl in platforms:
            Global.mega.delete(cloud_path * self.get_converted_path(pl).full_name,
                               send_to_trash=send_to_trash, skip_errors=skip_errors)
            
        # Delete empty folder
        if Global.mega.exists(cloud_path) and (not Global.mega.list_files(cloud_path)):
            Global.mega.delete(cloud_path, send_to_trash=send_to_trash, skip_errors=skip_errors)


_M._E = MyVideo
_M._TABLE_NAME = MyVideo.__name__
_M.DBContext = DBContext(MyVideo)
_M._sdata = utils.get_table_items_from_object(MyVideo)
del _M._sdata['id']
del _M._sdata['auto_save']
del _M._sdata['auto_delete']


class UListMyVideos(_M, _ComES[MyVideo]):

    def delete(self, archive = False, remove_file = True, send_to_trash = False, not_exists_ok = True):
        self.delete_from_mega(skip_errors=True)
        return super().delete(archive, remove_file=remove_file, send_to_trash=send_to_trash, not_exists_ok=not_exists_ok)

    @property
    def urls(self) -> list[list[str]]:
        return [v.urls for v in self._elements]
    
    @urls.setter
    def urls(self, value: list[str]) -> None:
        for v in self._elements:
            v.urls = value

    @property
    def publication_dates(self) -> list[dict[str, str]]:
        return [v.publication_dates for v in self._elements]
    
    @publication_dates.setter
    def publication_dates(self, value: list[dict[str, str]]) -> None:
        for v in self._elements:
            v.publication_dates = value

    @property
    def long_description(self) -> list[str]:
        return [v.long_description for v in self._elements]
    
    @long_description.setter
    def long_description(self, value: str) -> None:
        for v in self._elements:
            v.long_description = value

    @property
    def description(self) -> list[str]:
        return [v.description for v in self._elements]
    
    @description.setter
    def description(self, value: str) -> None:
        for v in self._elements:
            v.description = value

    @property
    def hashtags(self) -> list[list[str]]:
        return [v.hashtags for v in self._elements]
    
    @hashtags.setter
    def hashtags(self, value: list[str]) -> None:
        for v in self._elements:
            v.hashtags = value

    @property
    def OCR(self) -> list[str]:
        return [v.OCR for v in self._elements]
    
    @OCR.setter
    def OCR(self, value: str) -> None:
        for v in self._elements:
            v.OCR = value
    
    @property
    def niche(self) -> list[str]:
        return [v.niche for v in self._elements]
    
    @niche.setter
    def niche(self, value: str) -> None:
        for v in self._elements:
            v.niche = value
        
    @property
    def caption(self) -> list[str]:
        return [v.caption for v in self._elements]

    @property
    def is_posted(self) -> list[bool]:
        return [v.is_posted for v in self._elements]
    
    @property
    def account(self) -> list[str]:
        return [v.account for v in self._elements]
    
    @account.setter
    def account(self, value: str) -> None:
        for v in self._elements:
            v.account = value
    
    @property
    def scene_ids(self) -> list[list[str]]:
        return [v.scene_ids for v in self._elements]
    
    @scene_ids.setter
    def scene_ids(self, value: list[str]) -> None:
        for v in self._elements:
            v.scene_ids = value

    def update_data(self) -> None:
        [v.update_data() for v in self._elements]

    def update_status(self) -> None:
        [v.update_status() for v in self._elements]
    
    def done(self) -> None:
        [v.done() for v in self._elements]

    async def send_to_mega_async(self,
        skip_on_exists: bool = True,
        max_concurrent: int = 6
    ) -> None:
        await asyncio.gather(*(v.send_to_mega_async(
            skip_on_exists=skip_on_exists,
            max_concurrent=max_concurrent
        ) for v in self._elements))

    async def download_from_mega_async(self,
        platforms: str | list[str] | None = None,
        overwrite: bool = True,
        max_concurrent: int = 6,
        skip_errors: bool = True
    ) -> None:
        await asyncio.gather(*(v.download_from_mega_async(
            platforms=platforms,
            overwrite=overwrite,
            max_concurrent=max_concurrent,
            skip_errors=skip_errors
        ) for v in self._elements))

    def delete_from_mega(self,
            platforms: str | list[str] | None = None,
            skip_errors: bool = True
        ) -> None:
        for v in self._elements:
            v.delete_from_mega(
                platforms=platforms,
                skip_errors=skip_errors
            )

_M._ES = UListMyVideos
MyVideo.register()

