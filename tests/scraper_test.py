#!/usr/bin/env python3

""" Tests for the scraper module """

# stdlib modules
import unittest

# thrid-party modules
from selenium.webdriver.common.by import By

# module to be tested
from __main__ import scraper

# exception modules
from __main__ import exceptions
from selenium.common.exceptions import NoSuchElementException

class ScraperTest(unittest.TestCase):
    """ A class to test the Scraper class. """

    def setUp (self) -> None:
        """ Sets up a windowed Scraper to be used later. """
        self.scraper = scraper.Scraper(country='china', currency='usd', headless=False)

    def test_scrapeURL (self) -> None:
        """ Tests the Scraper.scrapeURL method. """
        self.scraper.scrapeURL('url')

    def tearDown (self) -> None:
        """ Closes running Scrapers """
        self.scraper.close()
