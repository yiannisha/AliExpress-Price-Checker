#!/usr/bin/env python3

""" A module for helper functions for the ui module """

import re

def exceptionName (exception: Exception) -> str:
    """
    Returns a string of the exceptions full name including the package.

    :param exception: exception to get the full name of
    """

    pattern = "\'(.*)\'"
    text = str(type(exception))

    return re.search(pattern, text).groups()[0]
