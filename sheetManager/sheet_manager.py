#!/usr/bin/env python3

""" A module to handle the communication with the Google Sheets API """

# stdlib
import os

# third party modules
import gspread

# typing
from typing import List, Tuple

class SheetManager:
    """
    Can read and write in a particular sheet.

    :param url: google sheet url
    """
    def __init__ (self, url: str) -> None:
        self.service_account = gspread.service_account(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        )
        self.worksheet = self.service_account.open_by_url(url).sheet1

    def getItemUrls (self) -> List[str]:
        """
        Returns a list with the item urls from the worksheet in the predetermined format.
        Skips items that already have an item price.
        """

        # get all urls
        urls: List[str]
        all_urls = self.worksheet.col_values(1)[3:]

        # get all item prices
        prices: List[str]
        prices = self.worksheet.col_values(3)[3:]

        urls = [url for url, price in zip(all_urls, prices) if not price]
        urls.extend(all_urls[len(prices):])

        return urls

    def getTracking (self, urlNum: int) -> List[bool]:
        """
        Returns a list with the tracking booleans from the worksheet in the predetermined format.
        In case not a single tracking is written then it will return a list of length urlNum with None's.

        :param urlNum: length of corresponding url list
        """

        tracking: List[bool]
        tracking = [bool(i) for i in self.worksheet.col_values(2)[3:]]

        if len(tracking) != urlNum:
            while len(tracking) < urlNum:
                tracking.append(False)

        if not tracking:
            tracking = [False for i in range(0, urlNum)]

        return tracking

    def itemPriceCells (self) -> Tuple[str, str]:
        """
        Returns the next available (empty) item price cell and the tracking cell next to it.
        """
        enum = 4
        col = 'C{}'
        tracking = 'D{}'
        while True:
            cell = self.worksheet.acell(col.format(enum))
            if not cell.value:
                yield (col.format(enum), tracking.format(enum))
            enum += 1

    def shipPriceCells (self) -> str:
        """
        Returns the next available (empty) shipping price cell.
        """
        enum = 4
        col = 'D{}'
        while True:
            cell = self.worksheet.acell(col.format(enum))
            if not cell.value:
                yield col.format(enum)
            enum += 1

    def write (self, name: str, message: str) -> None:
        """
        Writes the message in the cell with the passed name.

        :param name: the cell's name
        :param message: message to write in cell
        """

        self.worksheet.update(name, message)
