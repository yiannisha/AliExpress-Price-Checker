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

# typing
from typing import Tuple

class ScraperTest(unittest.TestCase):
    """ A class to test the Scraper class. """

    def setUp (self) -> None:
        """ Sets up a windowed Scraper to be used later. """
        self.scraper = scraper.Scraper(country='china', currency='eur', headless=False)

    def test_scrapeURL (self) -> None:
        """ Tests the Scraper.scrapeURL method. """

        expected_values = [
            ('https://www.aliexpress.com/item/1005003742432861.html', True, 24, 0),
            ('https://www.aliexpress.com/item/1005004285231560.html', False, 14.02, 9.21),
            ('https://www.aliexpress.com/item/1005003890863335.html', False, 17.05, 3.11),
            ('https://www.aliexpress.com/item/1005004047047021.html', True, 0, 0),
            ('https://www.aliexpress.com/item/1005003604897865.html', True, 3.92, 3.63)
        ]

        for url, tracking, itemPrice, shipPrice in expected_values:
            data: Tuple[float, float]
            data = self.scraper.scrapeURL(url, tracking)
            self.assertEqual(data[0], itemPrice)
            self.assertEqual(data[1], shipPrice)

    def tearDown (self) -> None:
        """ Closes running Scrapers """
        with open('debug.html', 'w', encoding='utf-8') as f:
            f.write(self.scraper.driver.page_source)
        self.scraper.close()
