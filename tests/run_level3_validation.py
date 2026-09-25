import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if __name__ == '__main__':
    tests = unittest.TestLoader().discover('tests', pattern='test_level3_*.py')
    unittest.TextTestRunner(verbosity=2).run(tests)
