import typing as ty
import pg8000 as sq

from atexit import register
from time import sleep
from datetime import datetime
from enum import Enum

from src.modules.paths import PathLike
from src.modules.display import Logger, Logger
from src.modules.basics.ulist import UList

from src.config import Paths
from src import utils
from src.exceptions import ConfigError


T = ty.TypeVar('T', bound='_Com')
TE = ty.TypeVar('TE', bound='_ComE')
TES = ty.TypeVar('TES', bound='_ComES')


class DBContext:

        def __init__(self, cls: TE) -> None:
            self.cls = cls
            self.cls._E._db_updated = False

        def __enter__(self):
            self.cls.connect()
            return self

        def __exit__(self, exc_type, exc, tb):
            if exc_type and isinstance(exc_type(), sq.Error):
                try:
                    self.cls._db.rollback()
                except Exception:
                    pass


class _DB:
    _db: sq.Connection | None = None
    _cursor: sq.Cursor | None = None
    logger = Logger('[DB]')
    
    @classmethod
    def connect(cls) -> None:
        if not getattr(_DB, '_db', None):
            user = Paths.getenv('DB_USER')
            if user is None:
                raise ConfigError('Missing db user')
            host = Paths.getenv('DB_HOST')
            if host is None:
                raise ConfigError('Missing db host')
            database = Paths.getenv('DB_DATABASE')
            if database is None:
                raise ConfigError('Missing db database')
            port = Paths.getenv('DB_PORT')
            if port is None:
                raise ConfigError('Missing db port')
            try:
                port = int(port)
            except ValueError:
                raise ConfigError(f'Invalid db port: {port}')
            password = Paths.getenv('DB_PASSWORD')
            if password is None:
                raise ConfigError('Missing db password')

            max_retries = 10
            for i in range(max_retries):
                try:
                    _DB._db = sq.connect(
                        user=user,
                        host=host,
                        database=database,
                        port=port,
                        password=password,
                        timeout=10
                    )
                    cls.logger.info('Connection to db successful')
                    break
                except sq.InterfaceError as e:
                    if i == max_retries - 1:
                        raise
                    cls.logger.warning(f'Connection to db failed, retrying ({i+1}/{max_retries})')
                    sleep(1)

            _DB._cursor = _DB._db.cursor()

            cls.create_table()
            cls.create_indexs()

        elif not getattr(_DB, '_cursor', None):
            _DB._cursor = _DB._db.cursor()

    @classmethod
    def disconnect(cls) -> None:
        try:
            if getattr(_DB, '_cursor', None) is not None:
                _DB._cursor.close()
                _DB._cursor = None
        except Exception as e:
            cls.logger.error('Exception ignored closing cursor', skippable=True, base_error=e)

        try:
            if getattr(_DB, '_db', None) is not None:
                _DB._db.close()
                _DB._db = None
        except Exception as e:
            cls.logger.error('Exception ignored closing db connection', skippable=True, base_error=e)
            
    @classmethod
    def create_table(cls) -> None:
        pass
    
    @classmethod
    def create_indexs(cls) -> None:
        pass


class _Com(_DB):

    _E: TE
    _ES: TES
    _TABLE_NAME: str
    _db_updated: bool
    DBContext: DBContext
    _sdata: dict[str, dict[str, ty.Any]]
    logger: Logger
    metadata: str
    parent_path: PathLike
    path: PathLike
    statuses: type[Enum]

    @classmethod
    def close(cls, backup: bool = True) -> None:
        try:
            saver = cls._ES(e for e in cls._E._cache if e.auto_save)
            try:
                saver.save()
            except Exception as e:
                cls.logger.error(f'Exception ignored saving {saver}', skippable=True, base_error=e)
                cls.logger.warning('Trying to save objects one by one (This can take considerable time for large data set)')
                for e in saver._elements:
                    e.save()
            
            for e in saver._elements:
                e.auto_save = False

        except Exception as e:
            cls.logger.error(f'Exception ignored saving {cls._E.__name__} objects', skippable=True, base_error=e)
        finally:
            cls.auto_save = False

        try:
            deleter = cls._ES(e for e in cls._E._cache if e.auto_delete)
            try:
                deleter.delete()
            except Exception as e:
                cls.logger.error(f'Exception ignored deleting {deleter}', skippable=True, base_error=e)
                cls.logger.warning('Trying to delete objects one by one (This can take considerable time for large data set)')
                for e in deleter._elements:
                    e.delete()
            
            for e in deleter._elements:
                e.auto_delete = False

        except Exception as e:
            cls.logger.error(f'Exception ignored deleting {cls._E.__name__} objects', skippable=True, base_error=e)
        finally:
            cls.auto_delete = False

    @classmethod
    def register(cls) -> None:
        register(cls.close)

    @classmethod
    def create_table(cls: ty.Type[T]) -> None:
        with cls.DBContext:
            _DB._cursor.execute(utils.build_sql_table_command(cls._E))
            _DB._db.commit()

    @classmethod
    def create_indexs(cls) -> None:
        pass
    
    @classmethod
    def _build_query(cls, *args, limit: int | None = None, **kwargs) -> tuple[str, list]:
        """Builds the SQL query and parameters for loading objects."""
        query = f"""SELECT * FROM "{cls._TABLE_NAME}" WHERE (status IS NOT NULL)"""
        query_filters = []
        query_params = []

        def add_filter(key, op, value):
            if op.lower() in ('!=', '<>', 'not in'):
                if value is None:
                    query_filters.append(f"{key} IS NOT NULL")
                elif op.lower() == 'not in':
                    if value:
                        query_filters.append(f"{key} {op} ({','.join(f'${i}' for i in range(len(query_params) + 1, len(value) + len(query_params) + 1))})")
                        query_params.extend(value)
                else:
                    query_filters.append(f"{key} {op} ${len(query_params) + 1}")
                    query_params.append(value)
            else:
                if value is None:
                    query_filters.append(f"{key} IS NULL")
                elif op.lower() == 'in':
                    if value:
                        query_filters.append(f"{key} {op} ({','.join(f'${i}' for i in range(len(query_params) + 1, len(value) + len(query_params) + 1))})")
                        query_params.extend(value)
                else:
                    query_filters.append(f"{key} {op} ${len(query_params) + 1}")
                    query_params.append(value)

        for arg in args:
            assert isinstance(arg, (list, tuple)) and len(arg) == 3, f"Invalid arg format for {arg}"
            key, op, value = arg
            assert key == 'id' or key in cls._E._sdata, f'Invalid key: {key}'

            add_filter(key, op, value)

        for key, value in kwargs.items():
            assert key == 'id' or key in cls._E._sdata, f'Invalid key: {key}'
            op = '='
            add_filter(key, op, value)

        if query_filters:
            query += " AND " + " AND ".join(query_filters)

        if limit is not None:
            query += f" LIMIT {int(limit)}"

        query += ';'
        return query, query_params
    

register(_Com.disconnect)


class _ComE(_Com):

    def __new__(cls, *args, **kwargs):
        id = kwargs.get('id', None)
        if (id is None) and args:
            id = args[0]

        if id is not None:
            for ce in cls._E._cache:
                if ce.id == id:
                    return ce

        return super().__new__(cls)

    def __init__(self,
            id: str | None = None,
            creation_date: str | None = None,
            metadata: str = '',
            status: str = None,
            auto_save: bool = False,
            auto_delete: bool = False
        ) -> None:
        self.creation_date = creation_date or utils.create_unique_date()
        self.id = id or self.creation_date
        self.metadata = metadata or ''
        self._status = status
        self.auto_save = auto_save
        self.auto_delete = auto_delete
        self._E._cache.add(self)

    @property
    def auto_delete(self) -> bool:
        return self._auto_delete
    
    @auto_delete.setter
    def auto_delete(self, value: bool) -> None:
        # Auto save has the advantage
        self._auto_delete = (not self.auto_save) and value 

    @property
    def status(self) -> Enum:
        return self._status
    
    @status.setter
    def status(self, status: str | Enum | None = None) -> None:
        status = self.statuses.DEFAULT if status is None else (getattr(self.statuses, status) if isinstance(status, str) else status)
        assert status in self.statuses, f'Invalid status: {status}'
        self._status = status
        self.update_status()
        
    def update_status(self) -> None:
        pass

    def update_data(self) -> None:
        pass

    def status_action(self) -> None:
        if ((f := getattr(self, self.status.name.lower(), None)) is not None) and callable(f):
            f()

    def __bool__(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: TE) -> bool:
        return hasattr(other, 'id') and self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)

    def remove(self, send_to_trash: bool = False, not_exists_ok: bool = True) -> None:
        self.path.remove(send_to_trash=send_to_trash, not_exists_ok=not_exists_ok)
    
    @property
    def exists(self) -> bool:
        return self.path.exists
    
    @property
    def as_dict(self) -> dict[str, ty.Any]:
        return {'id': self.id, **{k: getattr(self, k) for k in self._sdata.keys()}}
    
    @property
    def modification_date(self) -> str:
        return utils.date_to_str(datetime.fromtimestamp(self.path.mtime)) if self.path.exists else self.creation_date
    
    def info(self) -> str:
        info = f'{self.__class__.__name__}:\n'
        for attr_name, attr_value in self.as_dict.items():
            info += f' - {attr_name}: {attr_value}\n'
        sep_bar = '_' * 80
        info = '\n' + sep_bar + '\n' + info + sep_bar + '\n'
        return info

    @classmethod
    def _load_args(cls: ty.Type[TE], *args, **kwargs) -> TE | None:
        """Load a single object by arguments."""
        with cls.DBContext:
            query, query_params = cls._build_query(*args, **kwargs)
            _DB._cursor.execute(query, query_params)
            row = _DB._cursor.fetchone()

            if not row:
                cls.logger.warning(f"Object not found with query: {query} params: {query_params}")
                return None

            columns = [description[0] for description in _DB._cursor.description]

        return utils.parse_sql_args(cls, dict(zip(columns, row)))

    @classmethod
    def load(cls: ty.Type[TE], *args,
            auto_save: bool = False, auto_delete: bool = False, **kwargs
        ) -> TE | None:
        """load method"""
        sql_args = cls._load_args(*args, **kwargs)
        if sql_args is None:
            return None
        obj: TE = cls._E(**sql_args, auto_save=auto_save, auto_delete=auto_delete)
        cls.logger.info(f"{obj} loaded.")
        return obj
    
    def save(self) -> None:
        """Saves or updates the current video in the PostGreSQL database."""
        with self.DBContext:
            self._cursor.execute(utils.build_sql_save_command(self._E), utils.build_sql_args(self))
            self._db.commit()
        self._E._db_updated = True
        self.logger.info(f"{self} saved.")

    def delete(self,
            archive: bool = False,
            remove_file: bool = True,
            send_to_trash: bool = False,
            not_exists_ok: bool = True
        ) -> None:
        if self not in self._E._cache:
            self.logger.warning(f'{self} already deleted, this instance is detached from any database saving process.')
            return
            
        with self.DBContext:
            query = (f'''UPDATE "{self._TABLE_NAME}" SET {', '.join((f"{col} = NULL" for col in self._sdata.keys()))} WHERE id = $1''' 
                     if archive
                     else f'''DELETE FROM "{self._TABLE_NAME}" WHERE id = $1''')
            self._cursor.execute(query, (self.id,))
            self._db.commit()
            
        if remove_file:
            self.path.remove(send_to_trash=send_to_trash, not_exists_ok=not_exists_ok)

            self.auto_save = False
            self.auto_delete = False

        self._E._db_updated = True
        self._E._cache.remove(self)
        self.logger.info(f"{self} deleted.")


class _ComES(_Com, UList[TE]):

    def __init__(self, objs: TES | None = None, auto_save: bool = False, auto_delete: bool = False) -> None:
        super().__init__(objs)
        self.auto_save = auto_save
        self.auto_delete = auto_delete
        register(self.atexit)

    def atexit(self) -> None:
        if self.auto_save:
            for e in self._elements:
                e.auto_save = True

        if self.auto_delete:
            for e in self._elements:
                e.auto_delete = True

    @property
    def auto_delete(self) -> bool:
        return self._auto_delete
    
    @auto_delete.setter
    def auto_delete(self, value: bool) -> None:
        # Auto save has the advantage
        self._auto_delete = (not self.auto_save) and value 

    @property
    def id(self) -> list[str]:
        return [v.id for v in self._elements]

    @property
    def metadata(self) -> list[str]:
        return [v.metadata for v in self._elements]
    
    @metadata.setter 
    def metadata(self, value: str) -> None:
        for v in self._elements:
            v.metadata = value

    @property
    def parent_path(self) -> list[PathLike]:
        return [v.parent_path for v in self._elements]
    
    @parent_path.setter 
    def parent_path(self, value: PathLike) -> None:
        for v in self._elements:
            v.parent_path = value
    
    @property
    def path(self) -> list[PathLike]:
        return [v.path for v in self._elements]
    
    @property
    def exists(self) -> list[bool]:
        return [v.exists for v in self._elements]
    
    @property
    def status(self) -> list[Enum]:
        return [v.status for v in self._elements]
    
    @status.setter
    def status(self, value: str | Enum) -> None:
        for e in self._elements:
            e.status = value
    
    def status_action(self) -> None:
        for e in self._elements:
            e.status_action()

    def info(self) -> str:
        return "\n".join(v.info() for v in self._elements) + f"\nTotal: {len(self._elements)}"

    def filter_attrs(self: TES,
            self_apply: bool = False,
            filter_key: ty.Callable[[TE], bool] | None = None,
            **attrs
        ) -> TES:
        filtered_objs = self if self_apply else self.copy()
        for obj in reversed(filtered_objs):
            if filter_key is not None and not filter_key(obj):
                filtered_objs.remove(obj)
                continue

            for attr_name, attr_value in attrs.items():
                if not hasattr(obj, attr_name):
                    raise AttributeError(f'Invalid filter name: {attr_name}')
                elif getattr(obj, attr_name) != attr_value:
                    filtered_objs.remove(obj)
                    break
                    
        return filtered_objs
    
    @classmethod
    def clear_data(cls: ty.Type[TES]) -> None:
        """Clear all the data in the data file."""
        cls.clear_load_cache()
        
        with cls.DBContext:
            _DB._cursor.execute(f'''DELETE FROM "{cls._TABLE_NAME}";''')
            _DB._db.commit()

        cls._E._db_updated = True
        cls.logger.warning("Data cleared, you can recover it using 'recover_data' method.")

    @classmethod
    def refresh_data(cls: ty.Type[TES]) -> None:
        cls._E._cache.clear()

        with cls.DBContext:
            temp_table_name = cls._TABLE_NAME + '_TEMP'

            _DB._cursor.execute(utils.build_sql_table_command(cls._E).replace(cls._TABLE_NAME, temp_table_name))

            _DB._cursor.execute(f'''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{cls._TABLE_NAME}';
            ''')
            initial_keys = {row[0] for row in _DB._cursor.fetchall()}

            _DB._cursor.execute(f'''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{temp_table_name}';
            ''')
            new_keys = {row[0] for row in _DB._cursor.fetchall()}

            keys = ', '.join(initial_keys.intersection(new_keys))
            _DB._cursor.execute(f'''
                INSERT INTO "{temp_table_name}" ({keys})
                SELECT {keys} FROM "{cls._TABLE_NAME}";
            ''')

            _DB._cursor.execute(f'''DROP TABLE "{cls._TABLE_NAME}";''')
            _DB._cursor.execute(f'''ALTER TABLE "{temp_table_name}" RENAME TO "{cls._TABLE_NAME}";''')

            _DB._db.commit()

        cls._E._db_updated = True
        cls.logger.warning(f'{cls._TABLE_NAME} table refreshed.')
        
    @classmethod
    def _load_iter_args(cls: ty.Type[TES], *args, limit: int | None = None, **kwargs) -> ty.Iterator[dict]:
        """Load multiple objects by arguments."""
        with cls.DBContext:
            query, query_params = cls._build_query(*args, limit=limit, **kwargs)
            #print(query, query_params)
            _DB._cursor.execute(query, query_params)
            columns = [description[0] for description in _DB._cursor.description]
            gen = (utils.parse_sql_args(cls._E, dict(zip(columns, row))) for row in _DB._cursor.fetchall())
        return gen

    @classmethod
    def load_iter(cls: ty.Type[TES],
            *args, auto_save: bool = False, auto_delete: bool = False, limit: int | None = None, **kwargs
        ) -> ty.Iterator[TE]:
        """Load objects from the database and filter them based on attributes or aqution."""
        return (cls._E(**sql_args, auto_save=auto_save, auto_delete=auto_delete) for sql_args in cls._load_iter_args(*args, **kwargs, limit=limit))
    
    @classmethod
    def load(cls: ty.Type[TES],
            *args, filter_key: ty.Callable[[TE], bool] | None = None,
            auto_save: bool = False, auto_delete: bool = False, limit: int | None = None, **kwargs
        ) -> TES:
        """Cached implementation of load method for collections"""
        gen = cls.load_iter(*args, **kwargs, auto_save=False, auto_delete=False, limit=limit)
        objs = cls(gen if filter_key is None else filter(filter_key, gen), auto_save=auto_save, auto_delete=auto_delete)
        cls.logger.info(f'{len(objs)} {cls._E.__name__} objects loaded')
        return objs

    def save(self,
            batch_size: int = 1000
        ) -> None:
        """Saves a list of objects"""
        if self._elements:
            with self.DBContext:
                query = utils.build_sql_save_command(self._E)
                [[self._cursor.executemany(
                    query, map(utils.build_sql_args, self._elements[i:i + batch_size])
                )] for i in range(0, len(self._elements), batch_size)]
                self._db.commit()
            
            self._E._db_updated = True
            self.logger.info(f'{len(self._elements)} {self._E.__name__} objects saved')
            # Clear caches to ensure fresh data is loaded next time
            self._E._cache = self._E._cache.difference(self._elements)

    def delete(self,
            archive: bool = False,
            remove_file: bool = True,
            send_to_trash: bool = False,
            not_exists_ok: bool = True
        ) -> None:
        if self._elements:
            with self.DBContext:
                query = (f'''UPDATE "{self._TABLE_NAME}" SET {', '.join((f"{col} = NULL" for col in self._sdata.keys()))} WHERE id IN ({', '.join(f'${i+1}' for i in range(len(self._elements)))})'''
                         if archive
                         else f'''DELETE FROM "{self._TABLE_NAME}" WHERE id IN ({', '.join(f'${i+1}' for i in range(len(self._elements)))})''')
                self._cursor.execute(query, [e.id for e in self._elements])
                self._db.commit()
                
            if remove_file:
                [v.path.remove(send_to_trash=send_to_trash, not_exists_ok=not_exists_ok) for v in self._elements]

            self._elements.clear()

            for e in self._elements:
                e.auto_save = False
                e.auto_delete = False
            
            self._E._db_updated = True
            self.logger.info(f'{len(self._elements)} {self._E.__name__} objects deleted')
            # Clear caches to ensure fresh data is loaded next time
            self._E._cache = self._E._cache.difference(self._elements)
            self._elements.clear()

    @classmethod
    def load_column(cls, column_name: str) -> list[str]:
        """Fetches all video column items from the database."""
        with cls.DBContext:
            assert column_name == 'id' or column_name in cls._E._sdata, f'Unknown column name: {column_name}'
            
            _DB._cursor.execute(f'''SELECT {column_name} FROM "{cls._TABLE_NAME}";''')
            rows = [row[0] for row in _DB._cursor.fetchall()]

        cls.logger.info(f'{len(rows)} {column_name} rows loaded.')
        return rows
    
    @classmethod
    def delete_row(cls, row_id: str) -> None:
        """Fetches all video column items from the database."""
        with cls.DBContext:
            cls._cursor.execute(f'''DELETE FROM "{cls._TABLE_NAME}" WHERE id = $1''', (row_id,))
            cls._db.commit()

        cls.logger.info(f'Deleted row with id: {row_id}.')
        # Clear caches to ensure fresh data is loaded next time
        cls._E._cache.clear()

    @classmethod
    def unban(cls, ids: list[str] | None = None) -> None:
        with cls.DBContext:
            if ids is None:
                _DB._cursor.execute(f'''DELETE FROM "{cls._TABLE_NAME}" WHERE status IS NULL;''')
                _DB._db.commit()
                cls.logger.warning(f'All ids unbanned.')
                cls._E._cache.clear()
            else:
                _DB._cursor.execute(f'''DELETE FROM "{cls._TABLE_NAME}" WHERE (id = ANY($1)) AND (status IS NULL);''', (ids,))
                _DB._db.commit()
                cls.logger.warning(f'{len(ids)} ids unbanned.')