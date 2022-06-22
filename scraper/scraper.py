#!/usr/bin/env python3

"""Scrape AliExpress."""

# stdlib modules
import os
import re
import sys
import platform

# third party modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# inner modules
from scraper import driver

# exceptions
from scraper.exceptions import *
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException

# typing
from typing import Union

# typedef
ChromeWebdriver: webdriver.chrome.webdriver.WebDriver
ChromeWebdriver = webdriver.chrome.webdriver.WebDriver


class Scraper(driver.Driver):
    """
    A class to scrape AliExpress.

    Raises:
    scraper.exceptions.InvalidCountryException
    """

    def __init__ (self, country: str = None, currency: str = None, headless: bool = True) -> None:
        super().__init__(country, currency, headless)
