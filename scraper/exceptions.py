#!/usr/bin/env python3

""" All exceptions raised by the Scraper class """

class InvalidCountryException(Exception):
    """ Raised when an invalid country is passed as an argument to a Scraper. """
    pass

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
