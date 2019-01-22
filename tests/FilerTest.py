import unittest
from transput_filer import newTransput, FTPTransput, HTTPTransput
from exception import UnknownProtocol


class FilerTest(unittest.TestCase):

    # TODO move to another class? To a library?
    def assertThrows(self, func, exceptionClass, errorMessage = None):
        
        with self.assertRaises(exceptionClass) as cm:
            
            func()
            
        if errorMessage:
        
            self.assertEqual(str(cm.exception), errorMessage)
            

    def test_newTransput(self):
        
        self.assertEquals(newTransput('ftp')   , FTPTransput)
        self.assertEquals(newTransput('http')  , HTTPTransput)
        self.assertEquals(newTransput('https') , HTTPTransput)
        
        self.assertThrows( lambda: newTransput('svn')
                         , UnknownProtocol
                         , "Unknown protocol: 'svn'"
                         )




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()