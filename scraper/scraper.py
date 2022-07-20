#!/usr/bin/env python3

"""Scrape AliExpress."""

# stdlib modules
import os
import re
import sys
import time
import logging

# third party modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# inner modules
from scraper import driver
from scraper import scraperutils as utils

# exceptions
from scraper.exceptions import *
from requests.exceptions import ConnectionError
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import JavascriptException

# typing
from typing import Tuple

class Scraper(driver.Driver):
    """
    A class to scrape AliExpress.

    Raises:
    scraper.exceptions.InvalidCountryException
    """

    def __init__ (self, country: str, currency: str, headless: bool = True, debug: bool = False) -> None:
        super().__init__(country, currency, headless, debug)

        # a variable used to count the retries done for scraping url
        self.retryCount = 0

    def scrapeURL (self, url: str, tracking: bool) -> Tuple[float, float]:
        """
        Scrapes the given AliExpress url for the item price and the shipping price.

        :param url: item page url
        :param tracking: whether or not to get the cheapest tracking option in shipping
        """

        url = self.sanitizeURL(url)

        logging.info(f'Now scraping: {url}')
        try:

            self.current_url = url
            self.driver.get(url)

            # initialy check that the product page is not deleted
            if not self.checkPageAvailability():
                return (0, 0)

            # check that the product is available to be sent at the requested country
            if not self.checkAvailability():
                return (0, 0)

            # select all first options (color, size etc.)
            self.selectFirstOptions(url)

            # get item price
            itemPrice = self.getItemPrice()
            logging.info(f'Got item price: {itemPrice}')

            # get the shipping price string
            # firstly validate that tracking is available if tracking is true
            if tracking:
                self.setShippingTracking()
            shippingPriceString = self.getShippingPriceString().replace(',', '.')
            if re.search('Free Shipping', shippingPriceString):
                shippingPrice = 0
            else:
                shippingPrice = self.convertPriceToFloat(shippingPriceString)
            logging.info(f'Got item shipping price: {shippingPrice}')
        except ConnectionError as e:
            if self.retryCount >= self.RETRIES:
                logging.error(f'Retried {self.retryCount} times. Error occured at last try: {e}')

            logging.error(f'There was an error in the connection. Resetting driver and retrying...')
            self.retryCount += 1
            self.resetDriver()
            return self.scrapeURL(url, tracking)

        # reset retry count if successful
        self.retryCount = 0

        return (itemPrice, shippingPrice)

    def checkPageAvailability (self) -> bool:
        """
        Returns true if the product page is not removed.
        """

        logging.info('Checking product page...')

        className = 'not-found-page'
        try:
            self.driver.find_element(By.CLASS_NAME, className)
            logging.info('Product page unavailable.')
            return False
        except NoSuchElementException:
            return True
        except Exception as e:
            raise e

    def checkAvailability (self) -> bool:
        """
        Returns true if product is available.
        """

        logging.info('Checking item availability...')

        # there are two levels of availability that we need to check

        # first level: the item is at all available

        # if this element exists then the item is not at all available
        try:
            unavailability_class = 'next-message-content'
            utils.getElement(
                parent=self.driver,
                locatorMethod=By.CLASS_NAME,
                locatorValue=unavailability_class,
                url=self.current_url,
                elementName='"item unavailable" message'
            )

            logging.info('Item is unavailable.')

            return False

        except InvalidClassNameNavigationException:
            pass

        # second level: the item is available to be shipped

        # make sure that parent element is loaded
        # (parent element is present no matter the item's availability)
        parentClassName = 'dynamic-shipping'
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, parentClassName))
            )
        except (NoSuchElementException, TimeoutException) as e:
            raise InvalidClassNameNavigationException(className=parentClassName, elementName='shipping availability element', url=self.current_url) \
            from e

        # try to find element present when item is not available
        className = 'dynamic-shipping-unreachable'
        try:
            self.driver.find_element(By.CLASS_NAME, className)
            logging.info('Item is unavailable.')
            return False
        except NoSuchElementException:
            return True
        except Exception as e:
            raise e

    def selectFirstOptions (self, url: str) -> None:
        """
        Selects the first available option for every one of the item's properties.
        Assumes that driver is already at an item's page.

        :param url: needed for error messages
        """

        logging.info('Selecting the first option for all available properties...')

        className = 'sku-property-list'
        try:
            lists = self.driver.find_elements(By.CLASS_NAME, className)
            for list in lists:
                # select first available option

                # get options
                option_class = 'sku-property-item'
                options = utils.getElements(
                    parent=list,
                    locatorMethod=By.CLASS_NAME,
                    locatorValue=option_class,
                    url=self.current_url,
                    elementName='property options'
                )
                for option in options:
                    if not 'disabled' in option.get_attribute('class'):
                        option.click()
                        break

                # explicitly wait for the more options button to reload
                self.waitMoreOptionsButton()
                # the more options button updates everytime an option is selected
                # and it always finishes loading after the price has been updated
                # if it needs to, so it is the perfect wait time after a click

                # there is a possibility that after clicking a tooltip remains open
                # that may obscure the next button
                # we remove that tooltip using javascript
                try:
                    self.driver.execute_script(
                    ''' let tooltip = document.getElementsByClassName("next-overlay-wrapper opened")[0];
                        if (tooltip) {
                            document.body.remove(tooltip);
                        }'''
                    )
                except JavascriptException as e:
                    logging.error(f'An error occured while trying to delete the potential tooltip.\n{e}')

        except NoSuchElementException:
            sys.stderr.write(f'No properties found at {url}\n')

    def waitMoreOptionsButton (self) -> None:
        """
        Explicitly wait until the 'More Options' button is loaded.
        """

        buttonClassName = 'comet-btn'
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, buttonClassName))
            )
        except (NoSuchElementException, TimeoutException) as e:
            raise InvalidClassNameNavigationException(url=self.current_url, className=buttonClassName, elementName='shipping options button') \
            from e

    def getItemPrice (self) -> float:
        """
        Wraps the getItemPriceString.
        """
        return self.convertPriceToFloat(self.getItemPriceString().replace(',', '.'))

    def getItemPriceString (self) -> str:
        """
        Scrapes the item price from an item page by trying to get the price from
        different possible elements.
        Assumes that driver is already at the page.
        Raises ItemPriceNotFoundException if string itemPriceString is empty.
        """

        possible_classes = [
            'uniform-banner-box-price',
            'product-price-value',
        ]

        itemPriceString = ''

        for className in possible_classes:
            try:
                price_elem = self.driver.find_element(By.CLASS_NAME, className)
                itemPriceString = price_elem.text
                break
            except NoSuchElementException:
                sys.stderr.write(f'No element with class {className}, trying next one...\n')

        if not itemPriceString:
            raise ItemPriceNotFoundException(url=self.current_url, classes=possible_classes)

        return itemPriceString

    def getShippingPriceString (self) -> str:
        """
        Scrapes the shipping price from an item page by trying to get the price from
        different possible elements.
        Assumes that driver is already at the page.
        Raises ShippingPriceNotFoundException if string to be returned is empty.
        """

        possible_classes = [
            'dynamic-shipping',
        ]

        shippingPriceString = ''

        for className in possible_classes:
            try:
                price_elem = self.driver.find_element(By.CLASS_NAME, className)
                shippingPriceString = price_elem.text
                break
            except NoSuchElementException:
                sys.stderr.write(f'No element with class {className}, trying next one...\n')

        if not shippingPriceString:
            raise ShippingPriceNotFoundException(url=self.current_url, classes=possible_classes)

        return shippingPriceString

    def setShippingTracking (self) -> None:
        """
        Sets the shipping option to the cheapest tracking option.
        """

        logging.info('Setting shipping to the cheapest option with tracking available...')

        # explicitly wait until the page is loaded
        # by checking whether the button for more shipping options is loaded
        buttonClassName = 'comet-btn'
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, buttonClassName))
            )
        except (NoSuchElementException, TimeoutException) as e:
            raise InvalidClassNameNavigationException(url=self.current_url, className=buttonClassName, elementName='shipping options button') \
            from e


        # press button to open shipping options
        elem = utils.getElement(
            parent=self.driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=buttonClassName,
            url=self.current_url,
            elementName='shipping options button'
        )
        elem.click()

        # explicitly wait for the list to open by checking for list elements
        listElementClass = 'dynamic-shipping-mark'
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, listElementClass))
            )
        except (NoSuchElementException, TimeoutException) as e:
            raise InvalidClassNameNavigationException(url=self.current_url, className=listElementClass, elementName='shipping options list element') \
            from e

        # press button for more options if available
        try:
            elems = self.driver.find_elements(By.CLASS_NAME, buttonClassName)
            if len(elems) > 1:
                elems[1].click()
        except NoSuchElementException:
            sys.stderr.write('No "More options" button.\n')

        # get first element with tracking available (already sorted from cheapest to most expensive)
        trackingClassName = 'dynamic-shipping-mark'
        shippingOptions = utils.getElements(
            parent=self.driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=trackingClassName,
            url=self.current_url,
            elementName='shipping options list element'
        )

        found = False
        for option in shippingOptions:
            if option.text == 'Tracking Available':
                found = True
                option.click()
                break

        # there are no tracking available options so just click the first option to close the list
        if not found:
            shippingOptions[0].click()

    def convertPriceToFloat (self, price: str) -> float:
        """
        Converts a string with a price to a float value. (the price)

        :param price: the price string
        """

        pattern = '([\d.,]+)'
        return float(re.search(pattern, price).groups()[0])

    def sanitizeURL (self, url: str) -> str:
        """
        Removes all parameters from the url.

        :param url: url to sanitize
        """

        index = url.find('?')
        if index >= 0:
            return url[:index]

        return url
