#!/usr/bin/env python3

""" Tests for the scraper module """

import unittest

from __main__ import scraper

class ScraperTest (unittest.TestCase):
    """ A class to test the Scraper class """

    def setUp (self) -> None:
        """ Sets up a Scraper with default country and currency for the tests. """
        pass
        # self.scraper = scraper.Scraper()

    def test_TestClassWorking (self) -> None:
        """ Simple test that the test class is working """
        self.assertEqual(1, 1)

    def test_ScraperSetUp (self) -> None:
        self.scraper = scraper.Scraper(country = 'china')

    def tearDown (self) -> None:
        """ Closes all drivers opened due to tests. """
        try:
            self.scraper.close()
        except Exception as e:
            print(e)
            pass
