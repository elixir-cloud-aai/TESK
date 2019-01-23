import os
from os.path import relpath
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse



HOST_BASE_PATH      = os.environ.get('HOST_BASE_PATH')
CONTAINER_BASE_PATH = os.environ.get('CONTAINER_BASE_PATH')


def getPath(url):
    
    parsed_url = urlparse(url)

    return parsed_url.path

    
def containerPath(path):
    
    relPath = relpath(path, HOST_BASE_PATH)
    
    return os.path.join(CONTAINER_BASE_PATH, relPath)
    
    

