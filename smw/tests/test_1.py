#!/usr/bin/env python

import os
import sys
try:
    import unittest2 as unittest
except:
    import unittest

class test_0(unittest.TestCase):

    def test_success(self):
        a = 1
        pass

if __name__ == "__main__":
    unittest.main()
