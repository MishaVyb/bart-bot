from pathlib import Path

import yadisk
from telegram.ext import PicklePersistence
from yadisk import YaDisk

from configurations import CONFIG, logger


class YandexDiskPicklePersistence(PicklePersistence):
    yadisk = YaDisk(token=CONFIG.yadisk_token.get_secret_value())

    def _download_file_from_remote(self):
        logger.info('Dowloading data file from remote repository.  ')
        try:
            self.yadisk.download(str(self.filepath), str(self.filepath))
        except yadisk.exceptions.PathNotFoundError:
            logger.warning(
                'File not found on remote. '
                'If it`s the first application launch, that`s fine. '
            )
            # NOTE:
            # ...
            Path.unlink(self.filepath)

    def _upload_file_to_remote(self):
        logger.info('Uploading data file to remote repository. ')

        try:
            self.yadisk.upload(str(self.filepath), str(self.filepath))
        except yadisk.exceptions.PathExistsError:
            logger.debug(
                'File already exists at remote repository. '
                'It will be removed from remote and uploaded again. '
            )
            self.yadisk.remove(str(self.filepath), permanently=False)
            self.yadisk.upload(str(self.filepath), str(self.filepath))

    def _load_file(self, filepath: Path):
        raise NotImplementedError

    def _load_singlefile(self):
        self._download_file_from_remote()
        super()._load_singlefile()

    def _dump_file(self, filepath: Path, data: object):
        raise NotImplementedError

    def _dump_singlefile(self) -> None:
        super()._dump_singlefile()
        self._upload_file_to_remote()
