import os
from os.path import relpath
from exception import InvalidHostPath
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse



def getPathEnv(varName):
    '''
    Gets a path from env var 'varName' and normalizes it
    
    e.g. removes trailing slashes.
    This removes some cases from the rest of the code.
    '''
    
    varContent = os.environ.get(varName)
    
    return os.path.normpath(varContent) if varContent else None


HOST_BASE_PATH      = getPathEnv('HOST_BASE_PATH')
CONTAINER_BASE_PATH = getPathEnv('CONTAINER_BASE_PATH')


def getPath(url):
    
    parsed_url = urlparse(url)

    return parsed_url.path

    
def isDescendant(base, path):
    '''
    Is 'path' is a descendant of 'base'?
    '''
    
    return os.path.commonpath([base, path]) == base


def validatePath(path):
    
    if not isDescendant(HOST_BASE_PATH, path):
        
        raise InvalidHostPath(f"'{path}' is not a descendant of 'HOST_BASE_PATH' ({HOST_BASE_PATH})")


def containerPath(path):
    
    validatePath(path)
    
    relPath = relpath(path, HOST_BASE_PATH)
    
    return os.path.join(CONTAINER_BASE_PATH, relPath)
    
    

