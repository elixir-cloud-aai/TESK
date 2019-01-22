import unittest
from transput_filer import newTransput, FTPTransput, HTTPTransput, FileTransput
from exception import UnknownProtocol
from assertThrows import AssertThrowsMixin


class FilerTest(unittest.TestCase, AssertThrowsMixin):

    def test_newTransput(self):
        
        self.assertEquals(newTransput('ftp')   , FTPTransput)
        self.assertEquals(newTransput('http')  , HTTPTransput)
        self.assertEquals(newTransput('https') , HTTPTransput)
        self.assertEquals(newTransput('file')  , FileTransput)
        
        self.assertThrows( lambda: newTransput('svn')
                         , UnknownProtocol
                         , "Unknown protocol: 'svn'"
                         )




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()