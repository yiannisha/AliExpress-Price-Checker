#!/usr/bin/env python3

""" A module for helper functions for the scraper module """

# stdlib modules
import os
import re
import sys
import time
import logging
import platform

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

# typing
from typing import Union, Tuple

# typedef
ChromeWebdriver: webdriver.chrome.webdriver.WebDriver
ChromeWebdriver = webdriver.chrome.webdriver.WebDriver
WebElement: webdriver.remote.webelement.WebElement
WebElement = webdriver.remote.webelement.WebElement

def getElement (parent: Union[ChromeWebdriver, WebElement], locatorMethod: str, locatorValue: str, url: str, elementName: str = None) -> WebElement:
    """
    Returns a webdriver WebElement.
    Locates it by the locatorMethod with the locatorValue.
    (i.e. locatorMethod = By.XPATH, locatorValue="./child::*")

    :param parent: chromewebdriver or parent element to search for the element
    :param locatorMethod: method to locate the element, should be value of selenium By
    :param locatorValue: value to locate the element corresponding to the locatorMethod
    :param url: current page's url - required for better error logging
    :param elementName: target element's name in logging
    """

    elem = None

    try:
        elem = parent.find_element(locatorMethod, locatorValue)
    except NoSuchElementException as e:
        # raise appropriate exception if element not found
        exceptions = {
            By.XPATH : InvalidXpathNavigationException(url=url, xpath=locatorValue, elementName=elementName),
            By.CLASS_NAME : InvalidClassNameNavigationException(url=url, className=locatorValue, elementName=elementName),
            By.ID : InvalidIdNavigationException(url=url, id=locatorValue, elementName=elementName),
            By.TAG_NAME : InvalidTagNameNavigationException(url=url, tagName=locatorValue, elementName=elementName),
        }
        raise exceptions[locatorMethod] from e

    return elem

def getElements (parent: Union[ChromeWebdriver, WebElement], locatorMethod: str, locatorValue: str, url: str, elementName: str = None) -> List[WebElement]:
    """
    Returns a list of webdriver WebElements.
    Locates it by the locatorMethod with the locatorValue.
    (i.e. locatorMethod = By.XPATH, locatorValue="./child::*")

    :param parent: chromewebdriver or parent element to search for the elements
    :param locatorMethod: method to locate the elements, should be value of selenium By
    :param locatorValue: value to locate the elements corresponding to the locatorMethod
    :param url: current page's url - required for better error logging
    :param elementName: target elements' name in logging
    """

    elems = []

    try:
        elems = parent.find_elements(locatorMethod, locatorValue)
    except NoSuchElementException as e:
        # raise appropriate exception if element not found
        exceptions = {
            By.XPATH : InvalidXpathNavigationException(url=url, xpath=locatorValue, elementName=elementName),
            By.CLASS_NAME : InvalidClassNameNavigationException(url=url, className=locatorValue, elementName=elementName),
            By.ID : InvalidIdNavigationException(url=url, id=locatorValue, elementName=elementName),
            By.TAG_NAME : InvalidTagNameNavigationException(url=url, tagName=locatorValue, elementName=elementName),
        }
        raise exceptions[locatorMethod] from e

    return elems

def getAttribute (element: WebElement, attribute: str) -> Union[str, None]:
    """
    Returns the element's attribute value.
    Returns None if the element has no such attribute.

    :param element: element to get the attribute of
    :param attribute: the name of the attribute
    """

    attr = None

    try:
        attr = element.get_attribute(attribute)
    except NoSuchAttributeException:
        pass

    return attr

def savePageSource (driver: ChromeWebdriver, filepath: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'driver_debug.html')) -> None:
    """
    Writes the page source of the page currently
    open in the driver to the specified file.

    :param driver: driver with currently open page that we need the page source
    :param filepath: path to file to write page source to, defaults to debug.html in tests
    """

    logging.info(f'Writing page source in {filepath}')

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(driver.page_source)

def injectCookie (driver: ChromeWebdriver, cookieValue: str, cookieName: str) -> None:
    """
    Injects cookie with name cookieName and value cookieValue
    into the current page open in the driver.
    If there is a cookie with the same name already it will
    replace that cookie using the original cookie's attributes.
    (i.e. expiry date)

    :param cookieValue: value of the cookie to be injected
    :param cookieName: name of the cookie to be injected
    """

    cookie = driver.get_cookie(cookieName)
    if not cookie:
        cookie = {}

    cookie['name'] = cookieName
    cookie['value'] = cookieValue

    driver.add_cookie(cookie)

def acceptCookies (driver: ChromeWebdriver, persist: bool = False) -> None:
    """
    Tries to find and close the global cookie banner by accepting cookies.

    :param driver: driver with currently open page that has a cookie banner
    :param persit: set to True to throw an exception if a cookie banner is not found
    """

    logging.info('Closing cookie banner...')

    cookieBannerClassName = 'global-gdpr-container'
    acceptButtonClassName = 'btn-accept'

    try:
        cookieBanner = getElement(
            parent=driver,
            locatorMethod=By.CLASS_NAME,
            locatorValue=cookieBannerClassName,
            url=driver.current_url,
            elementName='global cookie banner'
        )
    except InvalidClassNameNavigationException as e:
        if persist:
            raise e
        else:
            # no reason to keep going if there is no cookie banner
            return

    acceptButton = getElement(
        parent=cookieBanner,
        locatorMethod=By.CLASS_NAME,
        locatorValue=acceptButtonClassName,
        url=driver.current_url,
        elementName='cookie banner accept button'
    )

    acceptButton.click()

class text_to_be_present_in_child_element_attribute (object):
    """
    Custom expected condition for WebDriverWait.
    Waits until the specified text exists in the specified attribute
    of the first child of the element corresponding to the passed locator.

    :param locator: the same as driver.find_element
    :param attribute: attribute of the child to check
    :param text: text to look for in the child's attribute
    """

    def __init__ (self, locator: Tuple[str, str], attribute: str, text: str) -> None:
        self.locator = locator
        self.attribute = attribute
        self.text = text

    def __call__ (self, driver) -> Union[bool, WebElement]:
        parent = driver.find_element(*self.locator)
        child = parent.find_element(By.XPATH, './child::*')
        if self.text in child.get_attribute(self.attribute):
            return child
        else:
            return False
