#!/usr/bin/env python3

"""Scrape AliExpress."""

# stdlib modules
import os
import re
import sys
import time

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

        self.driver.get(url)

        # select all first options (color, size etc.)
        self.selectFirstOptions(url)

        # get item price string
        itemPriceString = self.getItemPriceString(url).replace(',', '.')
        # and convert it to a float
        itemPrice = self.convertPriceToFloat(itemPriceString)

        # get the shipping price string
        # firstly validate that tracking is available if tracking is true
        if tracking:
            self.setShippingTracking()
        shippingPriceString = self.getShippingPriceString(url).replace(',', '.')
        if re.search('Free Shipping', shippingPriceString):
            shippingPrice = 0
        else:
            shippingPrice = self.convertPriceToFloat(shippingPriceString)

        return (itemPrice, shippingPrice)

    def selectFirstOptions (self, url: str) -> None:
        """
        Selects the first option for every one of the item's property.
        Assumes that driver is already at an item's page.

        :param url: needed for error messages
        """

        className = 'sku-property-list'
        try:
            lists = self.driver.find_elements(By.CLASS_NAME, className)

            for list in lists:
                # select first option
                child_xpath = './child::*'
                try:
                    list.find_element(By.XPATH, child_xpath).click()
                except NoSuchElementException:
                    raise InvalidXpathNavigationException(xpath=child_xpath, elementName='first property option element')

        except NoSuchElementException:
            sys.stderr.write(f'No properties found at {url}\n')

    def getItemPriceString (self, url: str) -> str:
        """
        Scrapes the item price from an item page by trying to get the price from
        different possible elements.
        Assumes that driver is already at the page.
        Raises ItemPriceNotFoundException if string to be returned is empty.

        :param url: needed for ItemPriceNotFoundException to be raised
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
            raise ItemPriceNotFoundException(url=url, classes=possible_classes)

        return itemPriceString

    def getShippingPriceString (self, url: str) -> str:
        """
        Scrapes the shipping price from an item page by trying to get the price from
        different possible elements.
        Assumes that driver is already at the page.
        Raises ShippingPriceNotFoundException if string to be returned is empty.

        :param url: needed for ShippingPriceNotFoundException to be raised
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
            raise ShippingPriceNotFoundException(url=url, classes=possible_classes)

        return shippingPriceString

    def setShippingTracking (self) -> None:
        """
        Sets the shipping option to the cheapest tracking option.
        """

        # press button to open shipping options
        buttonClassName = 'comet-btn'
        try:
            elem = self.driver.find_element(By.CLASS_NAME, buttonClassName)
            elem.click()
        except NoSuchElementException:
            raise InvalidClassNameNavigationException(className=buttonClassName, elementName='shipping options button')

        # explicitly wait for the list to open by checking for list elements
        listElementClass = 'dynamic-shipping-mark'
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, listElementClass))
            )
        except NoSuchElementException:
            raise InvalidClassNameNavigationException(className=listElementClass, elementName='shipping options list element')

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
            raise InvalidClassNameNavigationException(className=trackingClassName, elementName='shipping options list element')

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
