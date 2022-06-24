#!/usr/bin/env python3

""" A module for the UI """

# stdlib
import sys

# inner modules
from ui import const
from scraper import scraper
from sheetManager import sheet_manager

# gui
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox

# exceptions
from scraper.exceptions import *
from gspread.exceptions import SpreadsheetNotFound
from gspread.exceptions import NoValidUrlKeyFound

# typing
from typing import Union

class App (QMainWindow):
    """
    Main UI class
    """

    def __init__ (self) -> None:
        super().__init__()
        self.title = 'Ali Express Price Checker Prototype'
        self.left = 400
        self.top = 400
        self.width = 500
        self.height = 500
        self.initUI()

    def setUpCountryList (self) -> None:
        """
        Set up the list of countries.
        """
        for country in const.countries:
            self.countryList.addItem(country)


    def setUpCurrencyList (self) -> None:
        """
        Set up the list of countries.
        """
        for currency in const.currencies:
            self.currencyList.addItem(currency)

    def initUI (self) -> None:
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.titleLabel = QLabel('<h1>Ali Express Price<br>Checker Prototype</h1>', self)
        self.titleLabel.move(60, 0)
        self.titleLabel.resize(400, 120)

        self.urlLabel = QLabel('<h3>Enter Google Sheet URL:</h3>', self)
        self.urlLabel.move(60, 120)
        self.urlLabel.resize(350, 50)
        self.urlBox = QLineEdit(self)
        self.urlBox.move(60, 160)
        self.urlBox.resize(250, 35)

        self.countryLabel = QLabel('<h3>Enter a country:</h3>', self)
        self.countryLabel.move(60, 190)
        self.countryLabel.resize(350, 50)
        self.countryList = QComboBox(self)
        self.setUpCountryList()
        self.countryList.move(60, 240)
        self.countryList.resize(350, 40)

        self.currencyLabel = QLabel('<h3>Enter a currency:</h3>', self)
        self.currencyLabel.move(60, 280)
        self.currencyLabel.resize(350, 50)
        self.currencyList = QComboBox(self)
        self.setUpCurrencyList()
        self.currencyList.move(60, 330)
        self.currencyList.resize(350, 40)

        self.infoLabel = QLabel('<h5></h5>', self)
        self.infoLabel.move(60, 280)

        self.errorLabel = QLabel('<h5></h5>', self)
        self.errorLabel.move(60, 340)

        self.startButton = QPushButton('Start', self)
        self.startButton.move(150, 400)
        self.startButton.resize(100, 30)
        self.startButton.clicked.connect(self.on_click)

    def disableInput (self) -> None:
        """
        Disables the input to all text boxes and comboboxes.
        """

        self.urlBox.setEnabled(False)
        self.countryList.setEnabled(False)
        self.currencyList.setEnabled(False)

    def enableInput (self) -> None:
        """
        Enables the input to all text boxes and comboboxes.
        """

        self.urlBox.setEnabled(True)
        self.countryList.setEnabled(True)
        self.currencyList.setEnabled(True)

    def clearURL (self) -> None:
        """
        Clears the contents of self.urlBox.
        """
        self.urlBox.clear()

    def displayURLErrorMessage (self) -> None:
        """
        Shows an error message about something not being right with the url.
        """
        message = 'Something is wrong with the sheet url.'
        self.displayErrorMessage(message)

    def displayDriverErrorMessage (self) -> None:
        """
        Shows an error message about something not being right with the driver.
        """
        message = 'Something went wrong with the driver. Please try again.'
        self.displayErrorMessage(message)

    def clearError (self) -> None:
        """
        Clears the text in self.errorLabel
        """
        self.displayErrorMessage('')

    def displayErrorMessage (self, message: str) -> None:
        """
        Displays the passed message in self.errorLabel
        """
        self.errorLabel.setText(message)

    def clearInfo (self) -> None:
        """
        Clears the text in self.infoLabel
        """
        self.displayInfo('')

    def displayInfo (self, message: str) -> None:
        """
        Displays passed message in self.infoLabel
        """
        self.infoLabel.setText(message)

    def on_click (self) -> None:
        """
        To be called when the start button is pressed.
        """

        # clear previous errors/info
        # self.clearError()
        # self.clearInfo()

        # get sheet url
        sheet_url = self.urlBox.text()

        if sheet_url:

            # disable input
            self.disableInput()

            # get country and currency
            country = self.countryList.currentText()
            if country == 'None': country = None
            currency = self.currencyList.currentText()
            if currency == 'None': currency = None

            # get worksheet
            try:
                sh = sheet_manager.SheetManager(url=sheet_url)
                # self.displayInfo('Successfully found the worksheet')

            except (SpreadsheetNotFound, NoValidUrlKeyFound):
                self.displayURLErrorMessage()
                self.clearURL()
                self.enableInput()
                return None

            # get urls
            urls = sh.getItemUrls()
            if urls: trackings = sh.getTracking()
            else:
                self.enableInput()
                return None
            # self.displayInfo('Successfully acquired urls.')

            # set up driver
            try:
                # self.displayInfo('Setting up driver...')
                scr = scraper.Scraper(country=country, currency=currency, headless=True)
                # self.displayInfo('Successfully set up driver.')
            except:
                self.displayDriverErrorMessage()
                self.enableInput()
                return None

            # start feeding the urls to the scraper
            scraperExceptions = (InvalidXpathNavigationException, InvalidClassNameNavigationException, ItemPriceNotFoundException, ShippingPriceNotFoundException)
            error_items = []
            for url, tracking, (itemCell, shipCell) in zip(urls, trackings, sh.itemPriceCells()):
                try:
                    # self.displayInfo(f'Scraping item at {url}...')
                    itemPrice, shipPrice = scr.scrapeURL(url=url, tracking=tracking)
                    sh.write(itemCell, itemPrice)
                    sh.write(shipCell, shipPrice)

                except scraperExceptions as e:
                    # no need for the loop to stop in case an item is misbehaving
                    error_items.append({
                        'url': url,
                        'tracking': tracking,
                        'error': e,
                    })
                    continue

                except Exception as e:
                    # we need the loop to stop otherwise
                    raise e

            # once the loop is over clear the url and reenable the input
            self.clearURL()
            self.enableInput()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
