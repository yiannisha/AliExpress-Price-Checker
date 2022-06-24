#!/usr/bin/env python3

""" A module to handle the communication with the Google Sheets API """

# stdlib
import os

# third party modules
import gspread

# typing
from typing import List

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
        """

        urls: List[str]
        urls = self.worksheet.col_values(1)[3:]

        return urls

    def getTracking (self) -> List[bool]:
        """
        Returns a list with the tracking booleans from the worksheet in the predetermined format.
        """

        tracking: List[bool]
        tracking = [bool(i) for i in self.worksheet.col_values(2)[3:]]

        return tracking

    def write (self, row: int, col: int, message: str) -> None:
        """
        Writes the message in the cell at (row, col) coords.

        :param col: vertical cell coordinate
        :param row: horizontal cell coordinate
        :param message: message to write in cell
        """

        self.worksheet.update_cell(row, col, message)