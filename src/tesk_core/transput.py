import enum
import os
import netrc
import logging
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


@enum.unique
class Type(enum.Enum):
    File = 'FILE'
    Directory = 'DIRECTORY'


class Transput:
    def __init__(self, path, url, ftype):
        self.path = path
        self.url = url
        self.ftype = ftype

        parsed_url = urlparse(url)
        self.netloc = parsed_url.netloc
        self.url_path = parsed_url.path
        self.netrc_file = None
        try:
            netrc_path = os.path.join(os.environ['HOME'], '.netrc')
        except KeyError:
            netrc_path = '/.netrc'
        try:
            self.netrc_file = netrc.netrc(netrc_path)
        except IOError as fnfe:
            logging.error(fnfe)
        except netrc.NetrcParseError as err:
            logging.error('netrc.NetrcParseError')
            logging.error(err)
        except Exception as er:
            logging.error(er)

    def upload(self):
        logging.debug('%s uploading %s %s', self.__class__.__name__,
                      self.ftype, self.url)
        if self.ftype == Type.File:
            return self.upload_file()
        if self.ftype == Type.Directory:
            return self.upload_dir()
        return 1

    def download(self):
        logging.debug('%s downloading %s %s', self.__class__.__name__,
                      self.ftype, self.url)
        if self.ftype == Type.File:
            return self.download_file()
        if self.ftype == Type.Directory:
            return self.download_dir()
        return 1

    def delete(self):
        pass

    def download_file(self):
        raise NotImplementedError()

    def download_dir(self):
        raise NotImplementedError()

    def upload_file(self):
        raise NotImplementedError()

    def upload_dir(self):
        raise NotImplementedError()

    # make it compatible with contexts (with keyword)
    def __enter__(self):
        return self

    def __exit__(self, error_type, error_value, traceback):
        self.delete()
        # Swallow all exceptions since the filer mostly works with error codes
        return False
