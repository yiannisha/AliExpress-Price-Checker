#!/usr/bin/env python3

""" All exceptions raised by the Scraper class """

class InvalidCountryException(Exception):
    """ Raised when an invalid country is passed as an argument to a Scraper. """
    def __init__(self, country: str, message: str = None) -> None:
        self.country = country
        if not message:
            message = f'Cannot find country {country}.'
        self.message = message
        super().__init__(self.message)

class InvalidCurrencyException(Exception):
    """ Raised when an invalid currency is passed as an argument to a Scraper. """
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
