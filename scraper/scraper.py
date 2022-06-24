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

# exceptions
from scraper.exceptions import *
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException

# typing
from typing import Tuple

class Scraper(driver.Driver):
    """
    A class to scrape AliExpress.

    Raises:
    scraper.exceptions.InvalidCountryException
    """

    def __init__ (self, country: str = None, currency: str = None, headless: bool = True) -> None:
        super().__init__(country, currency, headless)

    def scrapeURL (self, url: str, tracking: bool) -> Tuple[float, float]:
        """
        Scrapes the given AliExpress url for the item price and the shipping price.

        :param url: item page url
        :param tracking: whether or not to get the cheapest tracking option in shipping
        """

        logging.info(f'Now scraping: {url}')
        self.current_url = url
        self.driver.get(url)

        # initialy check that the product is available to be shipped
        if not self.checkAvailability():
            return (0, 0)

        # select all first options (color, size etc.)
        self.selectFirstOptions(url)

        # get item price string
        itemPriceString = self.getItemPriceString().replace(',', '.')
        # and convert it to a float
        itemPrice = self.convertPriceToFloat(itemPriceString)
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

        return (itemPrice, shippingPrice)

    def checkAvailability (self) -> bool:
        """
        Returns true if product is available.
        """

        logging.info('Checking item availability...')

        # make sure that parent element is loaded
        # (parent element is present no matter the item's availability)
        parentClassName = 'dynamic-shipping'
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, parentClassName))
            )
        except NoSuchElementException:
            raise InvalidClassNameNavigationException(className=parentClassName, elementName='shipping availability element', url=self.current_url)

        # try to find element present when item is not available
        className = 'dynamic-shipping-unreachable'
        try:
            self.driver.find_element(By.CLASS_NAME, className)
            return False
        except NoSuchElementException:
            return True
        except Exception as e:
            raise e

    def selectFirstOptions (self, url: str) -> None:
        """
        Selects the first option for every one of the item's property.
        Assumes that driver is already at an item's page.

        :param url: needed for error messages
        """

        logging.info('Selecting the first option for all available properties...')

        className = 'sku-property-list'
        try:
            lists = self.driver.find_elements(By.CLASS_NAME, className)

            for list in lists:
                # select first option
                child_xpath = './child::*'
                try:
                    list.find_element(By.XPATH, child_xpath).click()
                except NoSuchElementException:
                    raise InvalidXpathNavigationException(xpath=child_xpath, elementName='first property option element', url=self.current_url)

        except NoSuchElementException:
            sys.stderr.write(f'No properties found at {url}\n')

    def getItemPriceString (self) -> str:
        """
        Scrapes the item price from an item page by trying to get the price from
        different possible elements.
        Assumes that driver is already at the page.
        Raises ItemPriceNotFoundException if string to be returned is empty.
        """

        possible_classes = [
            'product-price-current',
            'uniform-banner-box-price',
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
            # '//*[@id="root"]/div/div[2]/div/div[2]/div[12]/div/div/div[1]/span/span/strong',
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
        except:
            raise InvalidClassNameNavigationException(className=buttonClassName, elementName='shipping options button', url=self.current_url)


        # press button to open shipping options
        try:
            elem = self.driver.find_element(By.CLASS_NAME, buttonClassName)
            elem.click()
        except NoSuchElementException:
            raise InvalidClassNameNavigationException(className=buttonClassName, elementName='shipping options button', url=self.current_url)

        # explicitly wait for the list to open by checking for list elements
        listElementClass = 'dynamic-shipping-mark'
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, listElementClass))
            )
        except NoSuchElementException:
            raise InvalidClassNameNavigationException(className=listElementClass, elementName='shipping options list element', url=self.current_url)

        # press button for more options if available
        try:
            elems = self.driver.find_elements(By.CLASS_NAME, buttonClassName)
            if len(elems) > 1:
                elems[1].click()
        except NoSuchElementException:
            sys.stderr.write('No "More options" button.\n')

        # get first element with tracking available (already sorted from cheapest to most expensive)
        trackingClassName = 'dynamic-shipping-mark'
        try:
            shippingOptions = self.driver.find_elements(By.CLASS_NAME, trackingClassName)
        except NoSuchElementException:
            raise InvalidClassNameNavigationException(className=trackingClassName, elementName='shipping options list element', url=self.current_url)

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
