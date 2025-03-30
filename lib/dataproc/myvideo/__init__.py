from __future__ import annotations
import typing as ty
import asyncio

from lib.modules.paths import PathLike, Path
from lib.modules.display import Logger
from lib.modules.internal_script import get_func_kwargs_an

from lib.cloud.megacloud import MegaCloud

from lib.config import Paths, VideoExportSettings
from lib import utils
from lib.dataproc.com import _ComE, _ComES, DBContext

if ty.TYPE_CHECKING:
    from lib.dataproc.scenepack import Scene


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

class UploadStatuss(metaclass=StatussType):
    UNPROCESSED = 0
    READY = 1
    INITIATED = 2
    UPLOADED = 3
    ALL: dict[str, int]

UploadStatuss.ALL = {name: value for name, value in UploadStatuss.__dict__.items() 
                if not name.startswith('_') and isinstance(value, int)}

class MyVideo(_ComE):

    _E: 'MyVideo'
    Statuss = Statuss
    UploadStatuss = UploadStatuss
    DEFAULT_QUALITY = VideoExportSettings.OPTIONS['LT']['quality']

    def __init__(self,
            id: str = None,
            metadata: str = None,
            status: int = Statuss.PROCESSING,
            niche: str = None,
            account: str = None,
            urls: dict[str, str] = None,
            cloud_loc: str = None,
            title: str = None,
            description: str = None,
            hashtags: list[str] = None,
            OCR: str = None,
            command: list[str] = None,
            analysis: str = None,
            keywords: list[str] = None,
            scenes_data: list[dict] = None,
            auto_save: bool = False
        ):
        super().__init__(id, auto_save)
        self.metadata = metadata or ''
        self.set_status(status)
        self.urls = urls or {}
        self.cloud_loc = cloud_loc or ''
        self.title = title or ''
        self.description = description or ''
        self.hashtags = hashtags or []
        self.OCR = OCR or ''
        self.niche = niche or ''
    
        self.analysis = analysis or ''
        self.keywords = keywords or []
        self.scenes_data = scenes_data or []
        self.account = account or ''

        self.path = Paths('content_created/FINAL') * self.id
        self.uncompressed_path = self.path * (f"uncompressed_{self.id}{VideoExportSettings.OPTIONS[self.DEFAULT_QUALITY]['extension']}")
        self._converted_paths = {pl: (self.path * f"{pl}_{self.id}{VideoExportSettings.OPTIONS[pl]['extension']}") for pl in utils.PLATEFORMS}

    @classmethod
    def create_indexs(cls) -> None:
        with cls.DBContext:
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status ON "{cls._TABLE_NAME}" (status);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_account ON "{cls._TABLE_NAME}" (account);''')
            cls._cursor.execute(f'''CREATE INDEX IF NOT EXISTS idx_status_account ON "{cls._TABLE_NAME}" (status, account);''')
            cls._db.commit()

    @property
    def is_exported(self) -> bool:
        return self.uncompressed_path.exists
    
    @property
    def is_uploaded(self) -> bool:
        return self.urls and all(utils.extract_video_info(url)[0] in utils.PLATEFORMS for url in self.urls)
    
    def add_url(self, plateform: str, url: str | None = None) -> str:
        plateform = plateform.lower()
        assert plateform in utils.PLATEFORMS, f'Invalid plateform: {plateform}'
        self.urls[plateform] = url or ''
        return url
    
    def get_url(self, plateform: str) -> str:
        plateform = plateform.lower()
        assert plateform in utils.PLATEFORMS, f'Invalid plateform: {plateform}'
        return self.urls.get(plateform, '')
    
    def get_upload_status(self, plateform: str) -> int:
        if not plateform:
            return self.UploadStatuss.UNPROCESSED
        
        plateform = plateform.lower()
        assert plateform in utils.PLATEFORMS, f'Invalid plateform: {plateform}'

        if plateform in self.urls:
            if self.urls.get(plateform, ''):
                return self.UploadStatuss.UPLOADED
            else:
                return self.UploadStatuss.INITIATED

        elif self.path.exists:
            for p in self.path:
                if p.name.split('_', 1)[0] == plateform:
                    return self.UploadStatuss.READY

        return self.UploadStatuss.UNPROCESSED
    
    def get_converted_path(self, plateform: str, assert_exists: bool = False) -> PathLike | None:
        plateform = plateform.lower()
        assert plateform in utils.PLATEFORMS, f'Invalid plateform: {plateform}'

        p = self._converted_paths[plateform]

        if assert_exists and not p.exists:
            raise FileNotFoundError(f'{plateform} converted video not found.')
        
        return p

    def set_status(self, status: int | None = None) -> None:
        if status is None:
            self.status = self.Statuss.PROCESSING
        else:
            assert status in self.Statuss, f'Invalid status: {status}'
            self.status = status
        
    def done(self) -> None:
        self.remove(send_to_trash=False, not_exists_ok=True)
        self.set_status(self.Statuss.DONE)

    async def send_to_mega_async(self, skip_on_exists: bool = True, max_concurrent: int = 6) -> None:
        max_concurrent = max_concurrent or 1
        assert max_concurrent > 0, f'Invalid max concurrent value: {max_concurrent}'

        cloud_path = Path(f'automation/_auto_/{self.account}/{self.path.name}', 'Directory')

        with MegaCloud(self.cloud_loc or None) as mega:
            mega.rotate_until_enough_storage(self.path.size)

            mega.create_folder(cloud_path, exists_ok=True)

            sema = asyncio.Semaphore(max_concurrent)

            async def task(p: PathLike, cp: PathLike):
                async with sema:
                    await mega.upload_async(p, cp)

            tasks = []
            for converted_path in self._converted_paths.values():
                if converted_path.exists:
                    if skip_on_exists and mega.exists(converted_path):
                        continue
                    
                    tasks.append(task(converted_path, cloud_path * converted_path.full_name))
                    
            tasks.append(task(self.uncompressed_path, cloud_path * self.uncompressed_path.full_name))

            await asyncio.gather(*tasks)
            self.cloud_loc = mega.account.uniquename
            self.save()
        
    def send_to_mega(self, skip_on_exists: bool = True, max_concurrent: int = 6) -> None:
        asyncio.run(self.send_to_mega_async(skip_on_exists=skip_on_exists, max_concurrent=max_concurrent))
        
    async def download_from_mega_async(self,
            folder: bool = True,
            uncompressed: bool = False,
            plateforms: str | list[str] | None = None,
            overwrite: bool = True,
            max_concurrent: int = 6
        ) -> None:
        if plateforms is None and not folder:
            plateforms = utils.PLATEFORMS
        else:
            folder = False
            if isinstance(plateforms, str):
                plateforms = [plateforms]
        
            [pl.lower() for pl in plateforms]
            assert all(pl in utils.PLATEFORMS for pl in plateforms), f'Invalid plateform'
            
        max_concurrent = max_concurrent or 1
        assert max_concurrent > 0, f'Invalid max concurrent value: {max_concurrent}'

        cloud_path = Path(f'automation/_auto_/{self.account}/{self.path.name}', 'Directory')

        with MegaCloud(self.cloud_loc or None) as mega:
            acci = mega.account.uniquename

            while not mega.exists(cloud_path):
                mega.rotate_account()

                if mega.account.uniquename == acci:
                    err = f'{self} not found in MEGA.'
                    if self.cloud_loc:
                        err += f' Removing deprecated cloud location: {self.cloud_loc}'
                        self.cloud_loc = ''
                        self.save()
                    raise FileNotFoundError(err)

            sema = asyncio.Semaphore(max_concurrent)

            async def task(cp: PathLike, p: PathLike):
                async with sema:
                    await mega.download_async(
                        cloud_path=cp,
                        path=p,
                        overwrite=True,
                        send_to_trash=False,
                        max_concurrent=max_concurrent
                    )

            tasks = []
            if folder and (overwrite or not self.exists):
                tasks.append(task(cloud_path, self.path))
            else:
                if uncompressed and (overwrite or not self.is_exported):
                    tasks.append(task(cloud_path * self.uncompressed_path.full_name, self.uncompressed_path))

                for pl in plateforms:
                    p = self._converted_paths[pl]
                    if (overwrite or not p.exists):
                        tasks.append(task(cloud_path * p.full_name, p))

            await asyncio.gather(*tasks)

    def download_from_mega(self,
            folder: bool = True,
            uncompressed: bool = False,
            plateforms: str | list[str] | None = None,
            overwrite: bool = True,
            max_concurrent: int = 6
        ) -> None:
        asyncio.run(self.download_from_mega_async(
            folder=folder,
            uncompressed=uncompressed,
            plateforms=plateforms,
            overwrite=overwrite,
            max_concurrent=max_concurrent
        ))

    def ai_analyze(self,
        analysis_prediction: str | None = None,
        scenes_predictions: list[dict[str | dict[str, float]]] | None = None,
        setter: bool = True
    ) -> dict:
        raise NotImplementedError()
        if getattr(MyVideo, '_video_analyst', None) is None:
            from lib.analysts.video import VideoAnalyst
            MyVideo._video_analyst = VideoAnalyst(response_schema=VideoAnalyst.MODE.MYVIDEO.OUT())
            MyVideo._video_analyst.login()

        MyVideo._video_analyst.start_chat()
        data = MyVideo._video_analyst.analyze(
            video_path=self.path,
            query=VideoAnalyst.MODE.MYVIDEO.IN(analysis_prediction, scenes_predictions)
        )
        if setter:
            [setattr(self, k, v) for k, v in data.items() if hasattr(self, k)]
        return data


class UListMyVideos(_ComES[MyVideo]):

    Statuss = Statuss
    UploadStatuss = UploadStatuss

    @property
    def status(self) -> list[str]:
        return [v.status for v in self._elements]
    
    @status.setter
    def status(self, value: bool) -> None:
        for v in self._elements:
            v.set_status(value)
    
    @property
    def urls(self) -> list[dict[str, str]]:
        return [v.urls for v in self._elements]
    
    @urls.setter
    def urls(self, value: dict[str, str]) -> None:
        for v in self._elements:
            v.urls = value

    @property
    def cloud_loc(self) -> list[str]:
        return [v.cloud_loc for v in self._elements]
    
    @cloud_loc.setter
    def cloud_loc(self, value: str) -> None:
        for v in self._elements:
            v.cloud_loc = value

    @property
    def title(self) -> list[str]:
        return [v.title for v in self._elements]
    
    @title.setter
    def title(self, value: str) -> None:
        for v in self._elements:
            v.title = value

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
    def uncompressed_path(self) -> list[PathLike]:
        return [v.uncompressed_path for v in self._elements]
    
    @uncompressed_path.setter
    def uncompressed_path(self, value: PathLike) -> None:
        for v in self._elements:
            v.uncompressed_path = value

    @property
    def is_exported(self) -> list[bool]:
        return [v.is_exported for v in self._elements]
    
    @property
    def is_uploaded(self) -> list[bool]:
        return [v.is_uploaded for v in self._elements]

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
    def scenes_data(self) -> list[str]:
        return [v.scenes_data for v in self._elements]
    
    @scenes_data.setter
    def scenes_data(self, value: list[dict]) -> None:
        for v in self._elements:
            v.scenes_data = value
    
    @property
    def account(self) -> list[str]:
        return [v.account for v in self._elements]
    
    @account.setter
    def account(self, value: str) -> None:
        for v in self._elements:
            v.account = value
    
    def done(self) -> None:
        [v.done() for v in self._elements]
    
    @classmethod
    def sync_files(cls, send_to_trash: bool = False) -> None:
        paths = cls.load().path
        for p in Paths('content_created/FINAL'):
            if p not in paths:
                p.remove(send_to_trash=send_to_trash)
                cls.logger.warn(f'Unsyncronized file: {p.relative} removed.')


MyVideo._E = UListMyVideos._E = MyVideo
MyVideo._TABLE_NAME = UListMyVideos._TABLE_NAME = MyVideo.__name__
MyVideo.logger = UListMyVideos.logger = Logger('[MyVideo]')
MyVideo.DBContext = UListMyVideos.DBContext = DBContext(MyVideo)

MyVideo._sdata = get_func_kwargs_an(MyVideo.__init__)
del MyVideo._sdata['id']
del MyVideo._sdata['auto_save']

MyVideo.create_table()
MyVideo.create_indexs()