from lib.modules.paths import Path, PathLike

import logging
from datetime import datetime


class LoggerConfig:
    NAME = '[LOG]'
    LOG_DIR_PATH = None
    MAX_BACKUP_COUNT = None
    SEPARATOR_CHAR = '='
    FORMAT = '%(name)s - %(levelname)s - %(message)s'
    PROPAGATE = True


class _Logger:

    all_loggers: list['_Logger'] = []
    date_format = "%d-%m-%Y_%H'%M"

    def __init__(self,
            name: str | None = None,
            log_dir_path: PathLike | None = None,
            max_backup_count: int | None = None,
            separator_char: str | None = None,
            format: str | None = None):
        
        _Logger.all_loggers.append(self)

        self.name = name.split('.')[-1] if name is not None else LoggerConfig.NAME
        log_dir_path = Path(log_dir_path, 'Directory', assert_exists=True) if log_dir_path else LoggerConfig.LOG_DIR_PATH
        max_backup_count = max_backup_count if max_backup_count else LoggerConfig.MAX_BACKUP_COUNT
        if log_dir_path:
            if max_backup_count is not None:
                assert max_backup_count >= 0, f'max_backup_count need to be positive | current ({max_backup_count})'
                all_log_file_paths = [path for path in log_dir_path if path.extension == '.log']
                all_log_file_paths.sort(key=lambda x: datetime.strptime(x.name.replace('log_', ''), _Logger.date_format))
                while (len(all_log_file_paths) - max_backup_count) > 0:
                    all_log_file_paths.pop(0).remove(send_to_trash=False)
                    
            self.log_file_path = Path(log_dir_path * f"log_{datetime.now().strftime(_Logger.date_format)}.log", 'File')
            if not self.log_file_path.exists:
                self.log_file_path()
        else:
            self.log_file_path = None

        self.separator_char = separator_char if separator_char is not None else LoggerConfig.SEPARATOR_CHAR
        self.max_backup_count = max_backup_count if max_backup_count is not None else LoggerConfig.MAX_BACKUP_COUNT

        self._mess = self.__create_logger(
            name=self.name,
            propagate=True,
            format=format if format is not None else LoggerConfig.FORMAT
        )

        self._sep = self.__create_logger(
            name=self.name + '_sep',
            propagate=False,
            format=''
        )

    def __create_logger(self,
                name: str | None = None,
                propagate: bool | None = None,
                format: str | None = None
            ) -> logging.Logger:
        """
        Creates and configures a logger with specified formatting and propagation settings.
        """
        name = name if name is not None else LoggerConfig.NAME
        propagate = propagate if propagate is not None else LoggerConfig.PROPAGATE
        format = format if format is not None else LoggerConfig.FORMAT

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(format))
        logger.addHandler(stream_handler)

        if self.log_file_path is not None:
            file_handler = logging.FileHandler(self.log_file_path.fs)
            file_handler.setFormatter(logging.Formatter(format))
            logger.addHandler(file_handler)

        logger.propagate = propagate
        return logger
    
    def separator_line(self, separator_char: str=None, nbr_of_char: int=80, text1: str='', text2: str='') -> None:
        """
        Send a separator line for the readability.

        Parameters:
        ----------
            separator_char (str): the character to use in the line. Default to the initial separator_char attributes.
            nbr_of_char (int): the number of character in the line.
            text1 (str): A first text before the line.
            text2 (str): A last text after the line.
        """
        self._sep.info(text1 + (self.separator_char if separator_char is None else separator_char) * nbr_of_char + text2)
    
    def info(self, msg: str='', *args, **kwargs) -> None:
        """
        Send an info message.

        Parameters:
        ----------
            msg (str): The info message.
        """
        self._mess.info(msg.encode('charmap', errors='ignore').decode('charmap'), *args, **kwargs)

    def warn(self, msg: str='', *args, **kwargs) -> None:
        """
        Send a warning message.

        Parameters:
        ----------
            msg (str): The warning message.
        """
        self._mess.warn(msg.encode('charmap', errors='ignore').decode('charmap'), *args, **kwargs)

    def debug(self, msg: str='', *args, **kwargs) -> None:
        """
        Send a debug message.

        Parameters:
        ----------
            msg (str): The debug message.
        """
        self._mess.warn(msg.encode('charmap', errors='ignore').decode('charmap'), *args, **kwargs)

    def error(self, msg: str='', *args, skippable: bool=False, base_error: Exception | None=None, **kwargs) -> None:
        """
        Send an error message and raise it, if it's not skippable.

        Parameters:
        ----------
            msg (str): The error message.
            skippable (bool): Whether the error need to be raised or not.
            base_error (object): A raised error that can be the reason of calling this function.
        """
        msg = msg.encode('charmap', errors='ignore').decode('charmap')
        if base_error is None:
            self._mess.error(msg, *args, **kwargs)
        else:
            self._mess.exception(msg, *args, **kwargs)
        if not skippable:
            raise Exception(msg)

    def __eq__(self, _logger: '_Logger') -> bool:
        return self.name == _logger.name
    
    def close(self) -> None:
        """Close the logger's handlers explicitly."""
        for handler in self._mess.handlers:
            handler.close()
            self._mess.removeHandler(handler)
        for handler in self._sep.handlers:
            handler.close()
            self._sep.removeHandler(handler)
        logging.shutdown()

    def __enter__(self) -> '_Logger':
        self.separator_line()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.separator_line()
        self.close()

def Logger(
        name: str,
        log_dir_path: PathLike=None,
        max_backup_count: int | None=None,
        separator_char: str='=',
        format: str='%(name)s - %(levelname)s - %(message)s'
    ) -> '_Logger':
    name = name.split('.')[-1]
    for existing_logger in _Logger.all_loggers:
        if existing_logger.name == name:
            return existing_logger 
    return _Logger(
        name=name,
        log_dir_path=log_dir_path,
        max_backup_count=max_backup_count,
        separator_char=separator_char,
        format=format
    )


