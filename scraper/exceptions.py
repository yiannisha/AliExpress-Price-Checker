#!/usr/bin/env python3

""" All exceptions raised by the Scraper class """

class InvalidCountryException(Exception):
    """ Raised an invalid country is passed as an argument to a Scraper. """
    pass
