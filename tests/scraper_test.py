#!/usr/bin/env python3

""" Tests for the scraper module """

# stdlib modules
import os
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

# typedef
Scraper: scraper.Scraper
Scraper = scraper.Scraper

class ScraperTest(unittest.TestCase):
    """ A class to test the Scraper class. """

    def setUp (self) -> None:
        """ Sets up a windowed Scraper to be used later. """
        self.scraper = scraper.Scraper(country='united states', currency='eur', headless=True)

    @unittest.skip
    def test_emptyScraper (self) -> None:
        """ Tests the functionality of a Scraper with no country or currency """
        try:
            scr = scraper.Scraper(headless=True, debug=True)
            print(f'empty scraper: {scr}')
            self.test_scrapeURL(scraper=scr)
        except AssertionError as e:
            print(e)
        except Exception as e:
            raise e
        finally:
            scr.close()

    # @unittest.skip
    def test_scrapeURL (self, scraper: Scraper = None) -> None:
        """ Tests the Scraper.scrapeURL method. """

        if not scraper:
            scraper = self.scraper

        print(f'running test_scrapeURL using {scraper} scraper')

        expected_values = [
            ('https://www.aliexpress.com/item/10000334245846.html', True, 11.0, 0),
            ('https://www.aliexpress.com/item/1005002202123037.html', True, 0, 0),
            ('https://www.aliexpress.com/item/32660648792.html', True, 10.8, 0),
            ('https://www.aliexpress.com/item/4000999946541.html', True, 35.22, 0),
            ('https://www.aliexpress.com/item/4000221687787.html', True, 2.78, 2.96),
            ('https://www.aliexpress.com/item/33052582900.html', True, 3.97, 3.11),
            ('https://www.aliexpress.com/item/4000790011174.html', True, 0, 0),
            ('https://www.aliexpress.com/item/1005003742432861.html', True, 18.32, 0),
            ('https://www.aliexpress.com/item/1005003365147552.html', False, 0, 0),
            ('https://www.aliexpress.com/item/1005003890863335.html', False, 16.46, 0),
            ('https://www.aliexpress.com/item/1005004047047021.html', True, 18.89, 0),
            ('https://www.aliexpress.com/item/1005003604897865.html', True, 4.69, 2.95)
        ]

        for url, tracking, itemPrice, shipPrice in expected_values:
            data: Tuple[float, float]
            data = scraper.scrapeURL(url, tracking)
            self.assertEqual(data[0], itemPrice, url)
            self.assertEqual(data[1], shipPrice, url)

    def tearDown (self) -> None:
        """ Closes running Scrapers """
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraper_debug.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.scraper.driver.page_source)
        self.scraper.close()
