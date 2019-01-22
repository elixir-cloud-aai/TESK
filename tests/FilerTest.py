import unittest
from transput_filer import newTransput, FTPTransput, HTTPTransput
from exception import UnknownProtocol


class FilerTest(unittest.TestCase):

    
    def test_newTransput(self):
        
        self.assertEquals(newTransput('ftp')   , FTPTransput)
        self.assertEquals(newTransput('http')  , HTTPTransput)
        self.assertEquals(newTransput('https') , HTTPTransput)
        
        with self.assertRaises(UnknownProtocol) as cm:
             
            newTransput('svn')
             
        self.assertEqual(str(cm.exception), "Unknown protocol: 'svn'")




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()