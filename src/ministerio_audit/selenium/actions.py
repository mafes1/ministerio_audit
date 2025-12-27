"""Common Selenium actions shared across experiments."""

from __future__ import annotations

import re
import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
from bs4 import BeautifulSoup
from ministerio_audit.config import INFOJOBS_LOGIN, INFOJOBS_MAIN



def accept_cookies(driver, wait):
    try:
        wait.until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        ).click()
        return True
    except TimeoutException:
        return False


def login_infojobs(driver, email, password, SLEEP=1):
    wait = WebDriverWait(driver, 10)
    driver.get(INFOJOBS_MAIN)
    # driver.get(INFOJOBS_LOGIN)
    accept_cookies(driver, wait)

    wait.until(
        EC.visibility_of_element_located(
            (By.ID, "candidate_login")
        )
    ).click()

    input_email = wait.until(
        EC.visibility_of_element_located((By.NAME, "email"))
    )
    input_email.send_keys(Keys.CONTROL, "a")
    input_email.send_keys(Keys.DELETE)
    input_email.send_keys(email)
    sleep(SLEEP)
    wait.until(
        EC.visibility_of_element_located((By.NAME, "password"))
    ).send_keys(password)
    sleep(SLEEP)
    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//button[@type='submit' and .//span[normalize-space()='Iniciar sesión']]")
        )
    ).click()
    


def logout_infojobs(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "div[class='ij-HeaderDesktop-navbar-avatar']"))
    ).click()
    logout = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a[data-e2e='mainMenuSignOut']")
        )
    )
    logout.click()



def apply_to_offer(driver, offer_url: str) -> None:
    """Apply to a specific offer URL."""
    raise NotImplementedError



def submit_query_infojobs(driver, key, loc):
    """Search for offers using a query string."""
    wait = WebDriverWait(driver, 10)
    
    input_key = wait.until(
        EC.visibility_of_element_located((By.ID, "keyword-autocomplete"))
    )
    input_key.send_keys(Keys.CONTROL, "a")
    input_key.send_keys(Keys.DELETE)
    input_key.send_keys(key)
    
    input_loc = wait.until(
        EC.visibility_of_element_located((By.ID, "location-autocomplete"))
    )
    input_loc.send_keys(Keys.CONTROL, "a")
    input_loc.send_keys(Keys.DELETE)
    input_loc.send_keys(loc)

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//li[contains(@aria-label, 'ciudad')]")
        )
    ).click()
    
    radius = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//div[@class='ij-Box ij-RadiusSelector--desktop']")
    ))
    if radius:
        radius_string = radius.text
    else:
        radius_string = ""
    
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//button[contains(@class, 'SubmitSearchButton')]")
        )
    ).click()
    
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//nav[@class='ij-SidebarFilter']")
        )
    )


