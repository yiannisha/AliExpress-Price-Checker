#!/usr/bin/env python3

""" Runs the tests. """

from typing import List

import unittest

# internal modules
from scraper import scraper

# Test classes
from tests.scraper_test import ScraperTest

def runTests (tests: List[unittest.TestCase]) -> unittest.runner.TextTestRunner:
    """
    Runs tests of all passed unittest.TestCase classes

    :param tests: list of unittest.TestCase classes
    """

    loader = unittest.TestLoader()

    suitesList = []
    for test in tests:
        suite = loader.loadTestsFromTestCase(test)
        suitesList.append(suite)

    bigSuite = unittest.TestSuite(suitesList)

    runner = unittest.TextTestRunner()
    results = runner.run(bigSuite)

    return results

if __name__ == '__main__':
    tests = [ScraperTest, ]
    runTests(tests)
