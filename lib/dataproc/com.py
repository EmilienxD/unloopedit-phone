import typing as ty
import subprocess
import pg8000 as sq

from atexit import register, unregister

from lib.modules.paths import PathLike
from lib.modules.display import _Logger
from lib.modules.basics.UList import UList

from lib.config import Paths
from lib import utils


T = ty.TypeVar('T', bound='_Com')
TE = ty.TypeVar('TE', bound='_ComE')
TES = ty.TypeVar('TES', bound='_ComES')


class DBContext:

        def __init__(self, cls: T) -> None:
            self.cls = cls

        def __enter__(self):
            self.cls.connect()
            return self

        def __exit__(self, exc_type, exc, tb):
            if exc_type and isinstance(exc_type(), sq.Error):
                try:
                    _Com._db_updated = False
                    self.cls._db.rollback()
                except Exception:
                    pass


class _Com:

    _E: TE
    _TABLE_NAME: str
    _db: sq.Connection
    _cursor: sq.Cursor
    _db_updated: bool = False
    DBContext: DBContext
    _sdata: dict[str, dict[str, ty.Any]]
    logger: _Logger
    metadata: str
    path: PathLike   # Specific property

    @classmethod
    def connect(cls) -> None:
        if not hasattr(cls, '_db'):
            db_config = Paths('lib/dataproc/config.json').read(default={})

            try:
                main_user = db_config['main']['user']
                main_host = db_config['main']['host']
                main_database = db_config['main']['database']
                main_port = db_config['main']['port']
                main_password = db_config['main']['password']
            except KeyError as e:
                raise ConnectionError(f'Missing db config data for connection | {e}')

            _Com._db = sq.connect(
                user=main_user,
                host=main_host,
                database=main_database,
                port=main_port,
                password=main_password    
            )
            _Com._cursor = _Com._db.cursor()
            register(cls.close)

        elif not hasattr(cls, '_cursor'):
            _Com._cursor = _Com._db.cursor()
            register(cls.close)

    @classmethod
    def close(cls) -> None:
        unregister(cls.close)

        try:
            _Com._cursor.close()
        except Exception:
            pass

        try:
            _Com._db.close()
        except Exception:
            pass

        if getattr(_Com, '_db_updated', False):
            cls.export_backup()

    def db_updated(*args):
        _Com._db_updated = True

    @classmethod
    def export_backup(cls) -> PathLike:
        backups = sorted((b for b in Paths('content_saved/data/backups') if b.name.startswith(cls._TABLE_NAME.lower())),
                             key=lambda p: utils.str_to_date(p.name.split('$')[-1]),
                             reverse=True)

        [b.remove(send_to_trash=True) for b in backups[2:]]

        db_config = Paths('lib/dataproc/config.json').read(default={})

        try:
            main_dbname = db_config['main']['dbname']
        except KeyError as e:
            raise ConnectionError(f'Missing db config data for connection | {e}')
        
        backup_path = Paths('content_saved/data/backups') * f"{cls._TABLE_NAME.lower()}$backup${utils.create_unique_date()}.dump"
        cls.logger.warn(f'Creating backup: {backup_path.relative}...')
            
        subprocess.run(['pg_dump', f'--dbname={main_dbname}', '-F', 'c', '-t', f'public."{cls._TABLE_NAME}"',
                        '-f', backup_path.fs])
        cls.logger.warn('Backup exported.')
        return backup_path

    @classmethod
    def create_table(cls: ty.Type[T]) -> None:
        with cls.DBContext:
            _Com._cursor.execute(utils.build_sql_table_command(cls._E))
            _Com._db.commit()

    @classmethod
    def clear_data(cls: ty.Type[T]) -> None:
        """Clear all the data in the data file."""
        with cls.DBContext:
            _Com._cursor.execute(f'''DELETE FROM "{cls._TABLE_NAME}";''')
            _Com._db.commit()
            _Com._cursor.execute("VACUUM;")
            _Com._db.commit()
            cls.db_updated()
            cls.logger.warn("Data cleared, you can recover it using 'recover_data' method.")

    @classmethod
    def recover_data(cls: ty.Type[T], backup_index: int = 0, raise_error: bool = False) -> None:
        """backup_index = 0 (latest)"""
        backups = sorted((b for b in Paths('content_saved/data/backups') if b.name.startswith(cls._TABLE_NAME.lower())),
                            key=lambda p: utils.str_to_date(p.name.split('$')[-1]),
                            reverse=True)
        
        backup = utils.list_get(backups, backup_index, None)

        if not backup:
            err = 'No backup found for data recovery.'
            cls.logger.warn(err)
            if raise_error:
                raise FileNotFoundError(err)
            return
        
        db_config = Paths('lib/dataproc/config.json').read(default={})

        try:
            main_dbname = db_config['main']['dbname']
        except KeyError as e:
            raise ConnectionError(f'Missing db config data for connection | {e}')

        subprocess.run(['pg_restore', f'--dbname={main_dbname}',
                        '--clean', '--if-exists', '--disable-triggers',
                        '-F', 'c', backup.fs])
        
        cls.logger.warn(f"Data recovered from {backup.relative}, previous data sent to trash.")

    @classmethod
    def refresh_data(cls: ty.Type[T]) -> None:
        with cls.DBContext:
            temp_table_name = cls._TABLE_NAME + '_TEMP'

            _Com._cursor.execute(utils.build_sql_table_command(cls._E).replace(cls._TABLE_NAME, temp_table_name))

            _Com._cursor.execute(f'''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{cls._TABLE_NAME}';
            ''')
            initial_keys = {row[0] for row in _Com._cursor.fetchall()}

            _Com._cursor.execute(f'''
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{temp_table_name}';
            ''')
            new_keys = {row[0] for row in _Com._cursor.fetchall()}

            keys = ', '.join(initial_keys.intersection(new_keys))
            _Com._cursor.execute(f'''
                INSERT INTO "{temp_table_name}" ({keys})
                SELECT {keys} FROM "{cls._TABLE_NAME}";
            ''')

            #_Com._cursor.execute(f'''DROP TABLE "{cls._TABLE_NAME}";''')
            _Com._cursor.execute(f'''ALTER TABLE "{temp_table_name}" RENAME TO "{cls._TABLE_NAME}1";''')

            _Com._db.commit()
            cls.db_updated()


class _ComE(_Com):

    def __init__(self,
            id: str | None = None,
            auto_save: bool = False
        ) -> None:
        self.id = id or utils.create_unique_date()
        if auto_save:
            register(self.atexit)

    def atexit(self) -> None:
        try:
            self.save()
        except Exception as e:
            self.logger.error(f'Exception ignored saving {self}', skippable=True, base_error=e)

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
    
    def info(self) -> str:
        info = f'{self.__class__.__name__}:\n'
        for attr_name, attr_value in self.as_dict.items():
            info += f' - {attr_name}: {attr_value}\n'
        sep_bar = '_' * 80
        info = '\n' + sep_bar + '\n' + info + sep_bar + '\n'
        return info

    @classmethod
    def _load_sql_args(cls: ty.Type[TE],
            *args, **kwargs
        ) -> TE | None:
        """Load object args from SQLite database."""
        with cls.DBContext:
            query = f'''SELECT * FROM "{cls._TABLE_NAME}"'''
            query_filters = []
            query_params = []

            for arg in args:
                assert isinstance(arg, (list, tuple)) and len(arg) == 3, f"Invalid arg format for {arg}"
                key, op, value = arg
                assert key == 'id' or key in cls._E._sdata, f'Invalid key: {key}'
                
                if key != 'id' and not value:
                    op = 'IS NOT' if op in ('!=', '<>') else 'IS'
                    value = cls._E._sdata[key]['default']
                else:
                    if op == 'LIKE' and not str(value).startswith('%"'):
                        value = f'%"{value}"%'
                    elif op in ('!=', '<>'):
                        op = f'IS NULL OR {key} {op}'
                    else:
                        op = f'IS NOT NULL AND {key} {op}'

                query_filters.append(f"{key} {op} ${len(query_params) + 1}")
                query_params.append(value)

            for key, value in kwargs.items():
                assert key == 'id' or key in cls._E._sdata, f'Invalid key: {key}'
                if key != 'id' and not value:
                    op = 'IS'
                    value = cls._E._sdata[key]['default']
                else:
                    op = '='

                query_filters.append(f'{key} {op} ${len(query_params) + 1}')
                query_params.append(value)

            if query_filters:
                query += " WHERE " + " AND ".join(query_filters)

            _Com._cursor.execute(query, query_params)
            row = _Com._cursor.fetchone()
            if not row:
                cls.logger.warn(f"Object not found with query: {query}.")
                return None

            return utils.parse_sql_args(cls, dict(zip([description[0] for description in _Com._cursor.description], row)))

    @classmethod
    def load(cls: ty.Type[TE], *args,
            auto_save: bool = False, **kwargs
        ) -> TE | None:
        """Load object(s) from SQLite database."""
        sql_args = cls._load_sql_args(*args, **kwargs)
        if sql_args is None:
            return None
        obj = cls._E(**sql_args, auto_save=auto_save)
        cls.logger.info(f"{obj} loaded.")
        return obj

    def save(self) -> None:
        """Saves or updates the current video in the SQLite database."""
        with self.DBContext:
            self._cursor.execute(utils.build_sql_save_command(self._E), utils.build_sql_args(self))
            self._db.commit()
            self.db_updated()
            self.logger.info(f"{self} saved.")

    def delete(self,
            remove_file: bool = True,
            send_to_trash: bool = False,
            not_exists_ok: bool = True
        ) -> None:
        with self.DBContext:
            self._cursor.execute(f'''DELETE FROM "{self._TABLE_NAME}" WHERE id = $1''', (self.id,))
            self._db.commit()
            self._cursor.execute("VACUUM;")
            self._db.commit()
            self.db_updated()

            if remove_file:
                self.path.remove(send_to_trash=send_to_trash, not_exists_ok=not_exists_ok)

            self.logger.info(f"{self} deleted.")


class _ComES(_Com, UList[TE]):

    def __init__(self, objs: TES | None = None, auto_save: bool = False) -> None:
        super().__init__(objs)
        if auto_save:
            register(self.atexit)

    def atexit(self) -> None:
        try:
            self.save()
        except Exception as e:
            self.logger.error(f'Exception ignored saving {self}', skippable=True, base_error=e)
            self.logger.warn('Trying to save objects one by one (This can take considerable time for large data set)')
            for e in self._elements:
                e.atexit()

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
    def path(self) -> list[PathLike]:
        return [v.path for v in self._elements]

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
    def _load_iter_args(cls: ty.Type[TES],
            *args, **kwargs
        ) -> ty.Iterator[dict]:
        """Load object args from the database and filter them based on attributes or a custom function."""
        with cls.DBContext:
            query = f'''SELECT * FROM "{cls._TABLE_NAME}"'''
            query_filters = []
            query_params = []

            for arg in args:
                assert isinstance(arg, (list, tuple)) and len(arg) == 3, f"Invalid arg format for {arg}"
                key, op, value = arg
                assert key == 'id' or key in cls._E._sdata, f'Invalid key: {key}'
                
                if key != 'id' and not value:
                    op = 'IS NOT' if op in ('!=', '<>') else 'IS'
                    value = cls._E._sdata[key]['default']
                else:
                    if op == 'LIKE' and not str(value).startswith('%"'):
                        value = f'%"{value}"%'
                    elif op in ('!=', '<>'):
                        op = f'IS NULL OR {key} {op}'
                    else:
                        op = f'IS NOT NULL AND {key} {op}'

                query_filters.append(f"{key} {op} ${len(query_params) + 1}")
                query_params.append(value)

            for key, value in kwargs.items():
                assert key == 'id' or key in cls._E._sdata, f'Invalid key: {key}'
                if key != 'id' and not value:
                    op = 'IS'
                    value = cls._E._sdata[key]['default']
                else:
                    op = '='

                query_filters.append(f'{key} {op} ${len(query_params) + 1}')
                query_params.append(value)

            if query_filters:
                query += " WHERE " + " AND ".join(query_filters)
            
            _Com._cursor.execute(query, query_params)

            keys = [description[0] for description in _Com._cursor.description]
            return (utils.parse_sql_args(cls._E, dict(zip(keys, row))) for row in _Com._cursor.fetchall())

    @classmethod
    def load_iter(cls: ty.Type[TES],
            *args, auto_save: bool = False, **kwargs
        ) -> ty.Iterator[TE]:
        """Load objects from the database and filter them based on attributes or a custom function."""
        return (cls._E(**sql_args, auto_save=auto_save) for sql_args in cls._load_iter_args(*args, **kwargs))
    
    @classmethod
    def load(cls: ty.Type[TES],
            *args, filter_key: ty.Callable[[TE], bool] | None = None,
            auto_save: bool = False, **kwargs
        ) -> TES:
        """Load videos from the database and filter them based on attributes or a custom function."""
        with cls.DBContext:
            gen = cls.load_iter(*args, **kwargs, auto_save=False)
            objs = cls(gen if filter_key is None else filter(filter_key, gen), auto_save=auto_save)
            cls.logger.info(f'{len(objs)} {cls._E.__name__} objects loaded')
            return objs
    
    @classmethod
    def load_column(cls, column_name: str) -> list[str]:
        """Fetches all video IDs from the database."""
        with cls.DBContext:
            assert column_name == 'id' or column_name in cls._E._sdata, f'Unknown column name: {column_name}'
            
            _Com._cursor.execute(f'''SELECT {column_name} FROM "{cls._TABLE_NAME}";''')
            rows = [row[0] for row in _Com._cursor.fetchall()]
            cls.logger.info(f'{len(rows)} {column_name} rows loaded.')
            return rows

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
                self.db_updated()

                self.logger.info(f'{len(self._elements)} {self._E.__name__} objects saved')

    def delete(self,
            remove_file: bool = True,
            send_to_trash: bool = False,
            not_exists_ok: bool = True
        ) -> None:
        i_len = len(self._elements)
        if i_len:
            with self.DBContext:
                query = f'''DELETE FROM "{self._TABLE_NAME}" WHERE id IN ({', '.join(f'${i+1}' for i in range(len(self._elements)))})'''
                self._cursor.execute(query, self.id)
                self._db.commit()
                self._cursor.execute("VACUUM;")
                self._db.commit()
                self.db_updated()

                if remove_file:
                    [v.path.remove(send_to_trash=send_to_trash, not_exists_ok=not_exists_ok) for v in self._elements]

                self._elements.clear()
            self.logger.info(f'{i_len - len(self._elements)} {self._E.__name__} objects deleted')

