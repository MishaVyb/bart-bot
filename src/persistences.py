import io
import pickle
from pathlib import Path

import yadisk
from telegram.ext import PicklePersistence
from telegram.ext._picklepersistence import _BotPickler, _BotUnpickler
from yadisk import YaDisk

from configurations import CONFIG, logger


# TODO try getbuffer() memoryview
#
class YandexDiskPicklePersistence(PicklePersistence):
    yadisk = YaDisk(token=CONFIG.yadisk_token.get_secret_value())

    def _download_from_remote(self, remote_path: str):
        logger.info('Dowloading data file from remote repository.  ')

        with io.BytesIO() as buffer:
            try:
                self.yadisk.download(remote_path, buffer)
            except yadisk.exceptions.PathNotFoundError:
                logger.warning(
                    'File not found on remote. That`s fine for the first time. '
                )
            return buffer.getvalue()

    def _upload_to_remote(self, remote_path: str, data: bytes):
        logger.info('Uploading data file to remote repository. ')
        with io.BytesIO(data) as buffer:
            try:
                self.yadisk.upload(buffer, remote_path)
            except yadisk.exceptions.PathExistsError:
                logger.debug(
                    'File already exists at remote repository. '
                    'It will be removed from remote and uploaded again. '
                )
                self.yadisk.remove(remote_path, permanently=False)
                self.yadisk.upload(buffer, remote_path)

    def _load_file(self, filepath: Path):
        remote = self._download_from_remote(filepath)
        try:
            with io.BytesIO(remote) as buffer:
                return _BotUnpickler(self.bot, buffer).load()
        except (OSError, EOFError) as e:
            logger.debug(f'No {CONFIG.appname} data. Return None. Detail: {e}')
            return None
        except pickle.UnpicklingError as exc:
            raise TypeError(f"File does not contain valid pickle data") from exc

    def _dump_file(self, filepath: Path, data: object):
        with io.BytesIO() as buffer:
            _BotPickler(self.bot, buffer, protocol=pickle.HIGHEST_PROTOCOL).dump(data)
            self._upload_to_remote(filepath, buffer.getvalue())

    def _load_singlefile(self):
        raise NotImplementedError

    def _dump_singlefile(self) -> None:
        raise NotImplementedError
