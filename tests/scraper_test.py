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

class ScraperTest (unittest.TestCase):
    """ A class to test the Scraper class """

    def setUp (self) -> None:
        """ Sets up a Scraper with default country and currency for the tests. """
        pass
        # self.scraper = scraper.Scraper()

    def test_TestClassWorking (self) -> None:
        """ Simple test that the test class is working """
        self.assertEqual(1, 1)

    def test_ScraperWindowedSetUp (self) -> None:
        """ Tests that the debug windowed Scraper set up is working as intended """
        scr = scraper.Scraper(country='china', currency='usd', headless=False)
        scr.close()

    # @unittest.skip
    def test_ScraperHeadlessSetUp (self) -> None:
        """ Tests that the headless Scraper set up is working as intended """
        self.scraper = scraper.Scraper(country='china', currency='usd', headless=True)

        # debug
        with open('debug.html', 'w', encoding='utf-8') as f:
            f.write(self.scraper.driver.page_source)

        # verify that save button is clicked
        self.scraper.driver.refresh()

        flag_xpath = '//*[@id="switcher-info"]/span[1]/i'
        try:
            flag = self.scraper.driver.find_element(By.XPATH, flag_xpath)
        except NoSuchElementException:
            raise exceptions.InvalidXpathNavigationException(xpath=flag_xpath, elementName='settings menu flag')

        currency_xpath = '//*[@id="switcher-info"]/span[5]'
        try:
            currency = self.scraper.driver.find_element(By.XPATH, currency_xpath)
        except NoSuchElementException:
            raise exceptions.InvalidXpathNavigationException(xpath=currency_xpath, elementName='settings menu currency')

        expected_values = {
            'flag': 'css_flag css_hk',
            'currency': 'USD'
        }

        self.assertEqual(flag.get_attribute('class'), expected_values['flag'])
        self.assertEqual(currency.text, expected_values['currency'])



    def tearDown (self) -> None:
        """ Closes all drivers opened due to tests. """
        try:
            self.scraper.close()
        except Exception as e:
            print(e)
            pass
