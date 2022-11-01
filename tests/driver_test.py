#!/usr/bin/env python3

""" Tests for the driver module """

# stdlib modules
import unittest

# thrid-party modules
from selenium.webdriver.common.by import By

# module to be tested
from __main__ import driver

# exception modules
from __main__ import exceptions
from selenium.common.exceptions import NoSuchElementException

class DriverTest (unittest.TestCase):
    """ A class to test the Driver class """

    def setUp (self) -> None:
        """ Sets up a Driver with default country and currency for the tests. """
        pass

    def test_TestClassWorking (self) -> None:
        """ Simple test that the test class is working """
        self.assertEqual(1, 1)

    @unittest.skip
    def test_DriverWindowedSetUp (self) -> None:
        """ Tests that the debug windowed Driver set up is working as intended """
        scr = driver.Driver(country='united states', currency='usd', headless=True, debug=True)
        scr.close()

    # @unittest.skip
    def test_DriverHeadlessSetUp (self) -> None:
        """ Tests that the headless Driver set up is working as intended """
        self.driver = driver.Driver(country='united states', currency='usd', headless=True, debug=True)

        # verify that save button is clicked
        self.driver.driver.refresh()

        flag_parent_class = 'ship-to'
        try:
            flag_parent = self.driver.driver.find_element(By.CLASS_NAME, flag_parent_class)
        except NoSuchElementException:
            raise exceptions.InvalidClassNameNavigationException(url=self.driver.URL, className=flag_parent_class, elementName='settings menu flag parent')

        flag_xpath = './child::*'
        try:
            flag = flag_parent.find_element(By.XPATH, flag_xpath)
        except NoSuchElementException:
            raise exceptions.InvalidXpathNavigationException(url=self.driver.URL, xpath=flag_xpath, elementName='settings menu flag')

        currency_class = 'currency'
        try:
            currency = self.driver.driver.find_element(By.CLASS_NAME, currency_class)
        except NoSuchElementException:
            raise exceptions.InvalidClassNameNavigationException(url=self.driver.URL, className=currency_class, elementName='settings menu currency')

        expected_values = {
            'flag': 'css_flag css_hk',
            'currency': 'USD'
        }

        self.assertEqual(currency.text, expected_values['currency'])
        self.assertEqual(flag.get_attribute('class'), expected_values['flag'])

    def tearDown (self) -> None:
        """ Closes all drivers opened due to tests. """
        try:
            self.driver.close()
        except Exception as e:
            print(e)
            pass
