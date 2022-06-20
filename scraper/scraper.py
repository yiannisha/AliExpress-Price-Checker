#!/usr/bin/env python3

"""Scrape AliExpress."""

import os
import re
import sys
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# exceptions
from scraper.exceptions import *
from selenium.common.exceptions import NoSuchElementException

# typedef
ChromeWebdriver: webdriver.chrome.webdriver.WebDriver
ChromeWebdriver = webdriver.chrome.webdriver.WebDriver


class Scraper:
    """
    A class to scrape AliExpress.

    Raises:
    scraper.exceptions.InvalidCountryException
    """

    URL = 'https://www.aliexpress.com/'
    CHROMEDRIVER_PATH = ''
    RETRIES = 5

    def __init__ (self, country: str = None, currency: str = None) -> None:
        self.setUpChromedriverPath()
        self.driver = self.setUpDriver(country, currency)

    def close (self) -> None:
        """
        Closes the driver.
        """
        self.driver.close()

    def setUpChromedriverPath (self) -> None:
        """
        Sets up the self.CHROMEDRIVER_PATH attribute.
        """
        self.CHROMEDRIVER_PATH = os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    'dependencies',
                                    'chromedriver'
                                    )

        if platform.system() == 'Windows':
            self.CHROMEDRIVER_PATH += '.exe'

    def setUpDriver (self, country: str = None, currency: str = None) -> ChromeWebdriver:
        """
        Returns a Chrome driver at https://www.aliexpress.com.

        :param country: country to ship to (None for default country)
        :param currency: currency to show prices as (None for default currency)
        """

        # create driver
        driver = webdriver.Chrome(self.CHROMEDRIVER_PATH)

        # go to url
        driver.get(self.URL)
        self.closePopups(driver)

        # set up country
        if country:
            self.setUpCountry(driver, country)

        # set up currency
        # if currency:
        #     self.setUpCurrency(driver, currency)

        return driver

    def closePopups (self, driver: ChromeWebdriver) -> None:
        """
        Closes the initial popups when visiting https://www.aliexpress.com.

        :param driver: driver at https://www.aliexpress.com
        """

        xpaths = {
            'cookies': '//*[@id="gdpr-new-container"]/div/div[2]/button[2]',
            'notifications': '/html/body/div[4]/div/img',
            'welcome': '/html/body/div[8]/div/div/img[2]',
        }
        # get the close button for each popup and click it
        for key, value in xpaths.items():
            try:
                elem = driver.find_element(By.XPATH, value)
                elem.click()
            except NoSuchElementException:
                sys.stderr.write(f'{key.capitalize()} Popup not found in startup.\n')
                for i in range(self.RETRIES):
                    # implicitly wait
                    driver.implicitly_wait(0.2)
                    sys.stderr.write(f'Retrying...\n')
                    try:
                        elem = driver.find_element(By.XPATH, value)
                        elem.click()
                    except NoSuchElementException:
                        sys.stderr.write(f'{key.capitalize()} Popup not found in startup. Retry {i+1}\n')
                # raise custom navigation exception

    def setUpCountry (self, driver: ChromeWebdriver, country: str) -> None:
        """
        Sets up the ship to country.
        Raises InvalidCountryException if invalid country is passed.

        :param driver: driver at https://www.aliexpress.com ready for country set up
        :param country: country to set shipment to
        """

        dropdown_xpaths = ['//*[@id="switcher-info"]',
                           '//*[@id="nav-global"]/div[4]/div/div/div/div[1]/div/a[1]',
                          ]

        # click first dropdown
        try:
            driver.find_element(By.XPATH, dropdown_xpaths[0]).click()
        except NoSuchElementException:
            pass
            # raise custom navigation exception

        # click second dropdown
        try:
            driver.find_element(By.XPATH, dropdown_xpaths[1]).click()
        except NoSuchElementException:
            pass
            # raise custom navigation exception

        # click and insert in input
        try:
            input_xpath = '//*[@id="nav-global"]/div[4]/div/div/div/div[1]/div/div[1]/div/input'
            inp = driver.find_element(By.XPATH, input_xpath)
            inp.click()
            inp.clear()
            inp.send_keys(country.lower())
        except NoSuchElementException:
            pass
            # raise custom navigation exception

        # wait for list elements to update
        # driver.implicitly_wait(2)

        # iterate over all list items and get the first one that is visible
        result_xpath = '//*[@id="nav-global"]/div[4]/div/div/div/div[1]/div/div[1]/ul/li[{}]'
        enum = 1
        while True:
            try:
                result = driver.find_element(By.XPATH, result_xpath.format(enum))
                # get element's style to check if visible
                style = result.get_attribute('style')
                pattern = 'display: none'
                if not re.search(pattern, style):
                    # click and end loop if it is visible
                    result.click()
                    break

            except NoSuchElementException:
                # raise InvalidCountryException because there are no results
                raise InvalidCountryException(f'No such country as {country}')
                # end loop after it checks all list elements
                break

            enum += 1

        # close dropdown
        driver.find_element(By.XPATH, dropdown_xpaths[0]).click()
