#!/usr/bin/env python3

""" All exceptions raised by the Scraper class """

# typing
from typing import List

class InvalidCountryException(Exception):
    """ Raised when an invalid country is passed as an argument to a Driver. """
    def __init__(self, country: str, message: str = None) -> None:
        self.country = country
        if not message:
            message = f'Cannot find country {country}.'
        self.message = message
        super().__init__(self.message)

class InvalidCurrencyException(Exception):
    """ Raised when an invalid currency is passed as an argument to a Driver. """
    def __init__(self, currency: str, message: str = None) -> None:
        self.currency = currency
        if not message:
            message = f'Cannot find currency {currency}.'
        self.message = message
        super().__init__(self.message)

class InvalidXpathNavigationException(Exception):
    """
    Raised when there an element can't be found.
    Raised only when we search for the element by xpath.

    Attributes:
        xpath : string of the xpath that the search was made with
        elementName : optional name passed for the searched element
    """
    def __init__(self, xpath: str, message: str = None, elementName: str = None) -> None:

        self.xpath = xpath
        self.elementName = elementName
        if not message:
            message = f'Element with supposed xpath: {xpath}'
            if elementName:
                message += f' with the name of {elementName}'
            message += ' cannot be found.'
        self.message = message

        super().__init__(self.message)

class InvalidClassNameNavigationException(Exception):
    """
    Raised when there an element can't be found.
    Raised only when we search for the element by class name.

    Attributes:
        className : string of the class name that the search was made with
        elementName : optional name passed for the searched element
    """
    def __init__(self, className: str, message: str = None, elementName: str = None) -> None:

        self.className = className
        self.elementName = elementName
        if not message:
            message = f'Element with supposed className: {className}'
            if elementName:
                message += f' with the name of {elementName}'
            message += ' cannot be found.'
        self.message = message

        super().__init__(self.message)

class ItemPriceNotFoundException(Exception):
    """
    Raised when the Scraper can't find an item's price.

    Attributes:
        url : item page's url
        classes : list of classes tried to find the item price
        xpaths : list of xpaths tried to find the item price
    """
    def __init__(self, url: str, message: str = None, classes: List[str] = [], xpaths: List[str] = []) -> None:

        self.url = url
        self.classes = classes
        self.xpaths = xpaths
        if not message:
            message = f'Item price at {url} cannot be found.'
            if classes:
                message += f'\nClasses tried: {classes}'
            if xpaths:
                message += f'\nXpaths tried: {xpaths}'
        self.message = message
        super().__init__(self.message)

class ShippingPriceNotFoundException(Exception):
    """
    Raised when the Scraper can't find an item's shipping price.

    Attributes:
        url : item page's url
        classes : list of classes tried to find the shipping price
        xpaths : list of xpaths tried to find the shipping price
    """
    def __init__(self, url: str, message: str = None, classes: List[str] = [], xpaths: List[str] = []) -> None:

        self.url = url
        self.classes = classes
        self.xpaths = xpaths
        if not message:
            message = f'Item shipping price at {url} cannot be found.'
            if classes:
                message += f'\nClasses tried: {classes}'
            if xpaths:
                message += f'\nXpaths tried: {xpaths}'
        self.message = message
        super().__init__(self.message)
