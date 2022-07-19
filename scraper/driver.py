#!/usr/bin/env python3

""" A driver for the Scraper class """

# stdlib modules
import os
import re
import sys
import time
import logging
import platform

# inner modules
from scraper import scraperutils as utils

# third party modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# exceptions
from scraper.exceptions import *
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchAttributeException

# constants
from scraper.const import NO_NEW_USER_BONUS_COOKIE_VALUE, NO_NEW_USER_BONUS_COOKIE_NAME

# typing
from typing import Union

# typedef
ChromeWebdriver: webdriver.chrome.webdriver.WebDriver
ChromeWebdriver = webdriver.chrome.webdriver.WebDriver
WebElement: webdriver.remote.webelement.WebElement
WebElement = webdriver.remote.webelement.WebElement

class Driver:
    """
    A class to wrap around selenium.webdriver to use with Scraper.
    """

    URL = 'https://www.aliexpress.com/'
    CHROMEDRIVER_PATH = ''
    RETRIES = 5
    RETRY_INTERVAL = 0.5

    def __init__(self, country: str, currency: str, headless: bool = True, debug: bool = False) -> None:
        self.setUpChromedriverPath()

        self.country = country
        self.currency = currency
        self.headless = headless
        self.debug = debug

        # enable info level logging when headless
        if headless:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().disable = True

        self.driver = self.setUpDriver(self.country, self.currency, self.headless, self.debug)

    def close (self) -> None:
        """
        Closes the driver.
        """
        logging.info('Closing Driver...')
        self.driver.quit()

    def resetDriver (self) -> None:
        """
        Resets the driver itself by closing it and setting it up again.
        """
        self.close()
        self.driver = self.setUpDriver(self.country, self.currency, self.headless, self.debug)

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

    def setUpDriver (self, country: Union[str, None], currency: Union[str, None], headless: bool, debug: bool = False) -> ChromeWebdriver:
        """
        Returns a Chrome driver at https://www.aliexpress.com.

        :param country: country to ship to (None for default country)
        :param currency: currency to show prices as (None for default currency)
        """

        logging.info('Now setting up driver...')

        # create driver
        if headless:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('window-size=1920x1080')
            driver = webdriver.Chrome(self.CHROMEDRIVER_PATH, options=options)
        else:
            driver = webdriver.Chrome(self.CHROMEDRIVER_PATH)

        # set logging to warnings only
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        logger.setLevel(logging.WARNING)

        try:

            # go to url
            driver.get(self.URL)
            self.closePopups(driver)

            # open settings tab for settings to change
            try:
                self.openSettingsMenu(driver)
            except ElementClickInterceptedException:
                logging.info('Something intercepted the clicking the button to open the Settings menu')
                # if the setting button cannot be clicked there must be some
                # some popups that are still open so we try to close them again
                self.closePopups(driver)
                # we do not catch the ElementClickInterceptedException the second
                # time because something must be wrong
                self.openSettingsMenu(driver)

            # set up country
            flagClass = ''
            flagClass = self.setUpCountry(driver, country)

            # set up currency
            currencyCode = ''
            currencyCode = self.setUpCurrency(driver, currency)

            # inject cookie to bypass the new user bonus
            utils.injectCookie(driver=driver,
                               cookieValue=NO_NEW_USER_BONUS_COOKIE_VALUE,
                               cookieName=NO_NEW_USER_BONUS_COOKIE_NAME)

            # click save in the setttings menu
            self.saveSettingsMenu(driver)

            # explicitly wait until the settings menu changes to the desired
            # country flag and currency

            locator = (By.CLASS_NAME, 'currency')
            text = currencyCode
            try:
                WebDriverWait(driver, 5).until(
                    EC.text_to_be_present_in_element(
                        locator,
                        text
                    )
                )
            except NoSuchElementException as e:
                raise InvalidClassNameNavigationException(url=self.URL, className=locator[1], elementName='currency code element') \
                from e
            except TimeoutException as e:
                if self.debug:
                    utils.savePageSource(driver)
                raise TimeoutException(f'"{text}" not present in element: {locator[1]}') \
                from e

            locator = (By.CLASS_NAME, 'ship-to')
            attribute = 'class'
            text = flagClass
            try:
                WebDriverWait(driver, 5).until(
                    utils.text_to_be_present_in_child_element_attribute(
                        locator,
                        attribute,
                        text
                    )
                )
            except NoSuchElementException as e:
                raise InvalidClassNameNavigationException(url=self.URL, className=locator[1], elementName='country flag') \
                from e
            except TimeoutException as e:
                if self.debug:
                    utils.savePageSource(driver)
                raise TimeoutException(f"'{text}' not present in attribute: {attribute} of element's: {locator[1]} child") \
                from e


            # no need to close the settings menu because the page refreshes on save
            #    self.closeSettingsMenu(driver)

        except Exception as e:
            # debug
            utils.savePageSource(driver)
            driver.quit()
            raise e

        logging.info('Driver setup complete.')

        return driver

    def closePopups (self, driver: ChromeWebdriver) -> None:
        """
        Closes the initial popups when visiting https://www.aliexpress.com.

        :param driver: driver at https://www.aliexpress.com
        """

        logging.info('Closing Popups...')

        classes = {
            'cookies': 'btn-accept',
            'notifications': '_24EHh',
            'welcome': 'btn-close',
        }

        # explicitly wait until all three popups are loaded
        for popup, className in classes.items():
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, className))
                )
                driver.find_element(By.CLASS_NAME, className).click()

            except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
                logging.info(f'Skipping {popup} popup. If it intercepts will try to close again.')

            except ElementClickInterceptedException:
                raise ElementClickInterceptedException(f'element with name {popup} and class {className} click intercepted.')


    def setUpCountry (self, driver: ChromeWebdriver, country: str) -> str:
        """
        Sets up the ship to country. Assumes that the settings menu is already open.
        Also returns the class string for the flag element.
        Raises InvalidCountryException if invalid country is passed.

        :param driver: driver at https://www.aliexpress.com ready for country set up
        :param country: country to set shipment to
        """

        logging.info('Setting up the country...')

        country_dropdown_class = 'address-select-trigger'

        # explicitly wait for the country list dropdown to load
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, country_dropdown_class))
            )
        except (NoSuchElementException, TimeoutException):
            raise InvalidClassNameNavigationException(url=self.URL, className=country_dropdown_class, elementName='country list dropdown')

        # click list once loaded
        utils.getElement(
            parent=driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=country_dropdown_class,
            url=self.URL,
            elementName='country list dropdown'
        ).click()

        # get input element
        input_class = 'filter-input'
        inp = utils.getElement(
            parent=driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=input_class,
            url=self.URL,
            elementName='country input'
        )

        # click and insert in input
        inp.click()
        inp.clear()
        inp.send_keys(country.lower())

        # iterate over all list items and get the first one that is visible
        result_class = 'address-select-item'
        flagClass = ''

        # iterate over all countries and click the first one that is not disabled
        results = utils.getElements(
            parent=driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=result_class,
            url=self.URL,
            elementName='country list element'
        )

        for result in results:
            # check that it is a valid item by getting the 'data-name' attribute
            if not result.get_attribute('data-name'):
                continue

            # get style to check display
            style = result.get_attribute('style')
            pattern = 'display: none'

            if not re.search(pattern, style):
                # get flag class, click and end loop if visible
                dataCode = result.get_attribute('data-code')
                flagClass = f'css_{dataCode}'
                result.click()
                break

        return flagClass

    def setUpCurrency (self, driver: ChromeWebdriver, currency: str) -> str:
        """
        Sets up the currency. Assumes that the settings menu is already open.
        Also returns a string of the currency's iso code.
        Raises InvalidCurrencyException if invalid currency is passed.

        :param driver: driver at https://www.aliexpress.com ready for country set up
        :param currency: currency to set shipment to (i.e. 'eur', 'USD', 'hKd')
        """

        logging.info('Setting up the currency...')

        currency_dropdown_class = 'select-item'

        # explicitly wait until the currency dropdown list is present
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, currency_dropdown_class))
            )
            driver.find_elements(By.CLASS_NAME, currency_dropdown_class)[1].click()
        except (NoSuchElementException, TimeoutException) as e:
            raise InvalidClassNameNavigationException(url=self.URL, className=currency_dropdown_class, elementName='currency list dropdown') \
            from e

        # click and insert in input
        input_class = 'search-currency'
        inp = [
            elem for elem in utils.getElements(
                parent=driver, locatorMethod=By.CLASS_NAME,
                locatorValue=input_class, url=self.URL, elementName='currency input')
            if not utils.getAttribute(element=elem, attribute='data-role')
            ][0]
        inp.click()
        inp.clear()
        inp.send_keys(currency.lower())


        # iterate over all list items and get the first one that is visible
        currency_list_parent_class = 'switcher-currency-c'
        list_tag_name = 'ul'
        result_xpath = './child::*'
        currencyCode = ''

        # get parent element
        parent = utils.getElements(
            parent=driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=currency_list_parent_class,
            url=self.URL,
            elementName='currency list parent',
        )[1]

        # get list
        result_list = utils.getElement(
            parent=parent,
            locatorMethod=By.TAG_NAME,
            locatorValue=list_tag_name,
            url=self.URL,
            elementName='currency list',
        )

        # get results
        results = utils.getElements(
            parent=result_list,
            locatorMethod=By.XPATH,
            locatorValue=result_xpath,
            url=self.URL,
            elementName='currency list items'
        )
        if not results:
            raise NoSuchElementException('List returned is empty.')

        for result in results:
            # get result's text to check if visible
            if not result.text:
                continue

            # click the first visible result's link and break the loop
            currencyCode = result.text[:3]
            result.click()
            break

        return currencyCode

    def openSettingsMenu (self, driver: ChromeWebdriver) -> None:
        """
        Opens the dropdown menu where the country and currency settings are.

        :param driver: driver at https://www.aliexpress.com to have the settings menu opened.
        """

        id = 'switcher-info'

        try:
            utils.getElement(
                parent=driver,
                locatorMethod=By.ID,
                locatorValue=id,
                url=self.URL,
                elementName='setting menu'
            ).click()
        # we want to explicitly catch and raise ElementClickInterceptedException so that it is handled
        except ElementClickInterceptedException as e:
            raise e

    def closeSettingsMenu (self, driver: ChromeWebdriver) -> None:
        """
        Closes the dropdown menu where the country and currency settings are.
        Assumes that the settings menu is open.

        :param driver: driver at https://www.aliexpress.com to have the settings menu closed.
        """

        id = 'switcher-info'

        utils.getElement(
            parent=driver,
            locatorMethod=By.ID,
            locatorValue=id,
            url=self.URL,
            elementName='settings menu'
        ).click()

    def saveSettingsMenu (self, driver: ChromeWebdriver) -> None:
        """
        Clicks the save button inside the settings menu.
        Assumes that the settings menu is open.

        :param driver: driver at https://www.aliexpress.com to have the settings saved.
        """

        className = 'ui-button'

        utils.getElement(
            parent=driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=className,
            url=self.URL,
            elementName='save button',
        ).click()
