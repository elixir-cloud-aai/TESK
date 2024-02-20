

class AssertThrowsMixin(object):
    
    def assertThrows(self, func, exceptionClass, errorMessage = None):
        
        with self.assertRaises(exceptionClass) as cm:
            
            func()
            
        if errorMessage:
        
            self.assertEqual(str(cm.exception), errorMessage)


