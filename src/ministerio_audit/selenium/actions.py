"""Common Selenium actions shared across experiments."""

from __future__ import annotations

import logging
import re
from typing import Tuple
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
from .scrape import get_offer_details

logger = logging.getLogger(__name__)
TIME_WAIT = 10

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


def get_form_text(driver, wait, go_back=True):
    logger.debug("Waiting for apply button to appear")
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//div[@data-test='apply-button-footer']/button")
        )
    ).click()
    logger.debug("Waiting for form loading")
    wait.until(
        EC.visibility_of_element_located(
            (By.ID, "myForm")
        )
    )
    logger.debug("Form parsing")
    soup = BeautifulSoup(driver.page_source, "lxml")
    form = soup.find("form", id="myForm")
    form = re.sub(r"(\n){2,}", r"\1\1", form.get_text("\n").strip())
    logger.debug("Form parsing")
    if go_back:
        logger.info("Going back from form offer")
        driver.back()
    reqs = {}
    reqs_block = soup.find("h3", string="Datos de la oferta")  # TODO: correct offer scraping, now tthis function returns two values!!!
    if reqs_block:
        reqs_dl = reqs_block.find_next("dl")
        for dt, dd in zip(reqs_dl.find_all("dt"), reqs_dl.find_all("dd")):
            key = dt.get_text(strip=True).lower().replace(" ", "_")
            reqs[key] = dd.get_text("\n", strip=True)
    logging.debug("Found %s requirements at offer form page" % str(len(reqs)))
    return form, reqs

def applybutton_offer_infojobs(driver) -> Tuple:
    """Apply to a specific offer URL."""
    wait = WebDriverWait(driver, TIME_WAIT)
    logger.debug("Waiting for apply offer button")
    form_text, reqs = get_form_text(driver, wait, go_back=False)
    #apply_button = wait.until(
    #    EC.visibility_of_element_located(
    #        (By.XPATH, "//div[contains(@class, 'OfferDetailApplyButton')]")
    #    )
    #)
    #apply_button.click()
    #wait.until(EC.staleness_of(apply_button))
    logger.info("Form correctly accessed and parsed")
    return form_text, reqs


def load_offer_infojobs(driver, url):
    """Apply to a specific offer URL."""
    wait = WebDriverWait(driver, TIME_WAIT)
    driver.get(url)
    logger.info("Loading for offer %s" % url)
    wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
    logger.debug("Scraping details")
    data = get_offer_details(driver, wait)
    return data


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


def populate_fieldsets_infojobs(driver, fieldsets, cv_id, offer_id=None):
    trace = []
    for fieldset in fieldsets:
        logger.debug(
            "Filling question %s - %s",
            fieldset.get("index"),
            fieldset.get("question"),
        )
        inputs = fieldset.get("inputs", [])
        if len(inputs) > 1:
            logger.warning("Multiple inputs for the same question!")
        for input_item in inputs:
            input_id = input_item.get("id")
            if not input_id:
                logger.error("Missing input id for fieldset %s", fieldset)
                continue
            element = driver.find_element(By.ID, input_id)
            input_type = input_item.get("type")
            if "cv_values" not in input_item and input_type == "radio":
                element.click()
                trace.append(input_item)
                logger.debug("Clicked radio item")
                continue
            if "cv_values" in input_item and input_type == "textarea":
                value = input_item["cv_values"].get(cv_id)
                if not value:
                    logger.warning(
                        "No cv_value for %s at offer %s",
                        cv_id,
                        offer_id,
                    )
                else:
                    element.send_keys(value)
                    trace.append(value)
                continue
            logger.error("No corresponding form element for %s", fieldset)
    return trace


def populate_optional_infojobs(driver, cv_path, letter):
    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
    file_input.send_keys(str(cv_path))

    driver.find_element(By.ID, "opcionCarta_incluir").click()
    wait = WebDriverWait(driver, TIME_WAIT)
    wait.until(
        EC.visibility_of_element_located(
            (By.ID, "texto_carta_incluir")
        )
    ).send_keys(letter)
    trace = {
        "cv": driver.find_element(By.XPATH, "//span[@class='ij-FilePreview-name']").text,
        "letter": driver.find_element(By.ID, "opcionCarta_incluir").text
    }
    return trace
