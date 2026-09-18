import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def create_chrome_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,900")
    if binary := os.getenv("CHROME_BINARY"):
        options.binary_location = binary
    return webdriver.Chrome(options=options)
