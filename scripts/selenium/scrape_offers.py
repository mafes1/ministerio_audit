from time import sleep
import csv
from datetime import datetime
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup
import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ministerio_audit.selenium import login_infojobs, submit_query_infojobs
from ministerio_audit.selenium import get_form_text, get_offer_details
from ministerio_audit.selenium import get_offer_elements, save_offers_data


import yaml

from ministerio_audit.config import SECRETS_PATH, CHROMEDRIVER_PATH, INTERIM_DIR

with open(SECRETS_PATH) as f:
    secrets = yaml.load(f, Loader=yaml.SafeLoader).get("accounts")

output_dir = INTERIM_DIR

service = Service(CHROMEDRIVER_PATH)
opts = uc.ChromeOptions()
# PROXY = "11.456.448.110:8080"
proxy = "8.212.177.126:8080"
opts.add_argument('--proxy-server=%s' % proxy)
driver = uc.Chrome(service=service, use_subprocess=False)

import time

secret = secrets[-1]
email = secret["infojobs_email"]
password = secret["infojobs_password"]

login_infojobs(driver, email, password)


key = "Mozo/a de almacén"
loc = "Barcelona"


submit_query_infojobs(driver, key, loc)
wait = WebDriverWait(driver, 10)

offers_data = []
seen_links = set()


def collect_offer_links(driver, page_offers):
    links = []
    for offer in page_offers:
        href = offer.find_element(
            By.XPATH, ".//h2[contains(@id, 'job-title')]/a"
        ).get_property("href")
        # if not href:
        #     try:
        #         href = offer.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
        #     except Exception:
        #         href = None
        # if href:
        links.append(href)
    return links

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(5)
    page_offers = get_offer_elements(driver, wait)
    page_links = collect_offer_links(driver, page_offers)

    for link in page_links:
        if link in seen_links:
            continue
        seen_links.add(link)
        driver.get(link)
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
        data = get_offer_details(driver, wait)
        sleep(1)
        try:
            sleep(2)
            data["form_text"] = get_form_text(driver, wait)
        except:
            sleep(10)
            data["form_text"] = get_form_text(driver, wait)
        offers_data.append(data)
        sleep(2)
        driver.back()
        wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//nav[@class='ij-SidebarFilter']")
            )
        )
        sleep(2)

    try:
        next_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//li[contains(@class, 'sui-MoleculePagination-item')]/button"
                    "[.//span[normalize-space()='Siguiente']]",
                )
            )
        )
    except TimeoutException:
        break

    next_button.click()
    sleep(2)
    #wait.until(EC.staleness_of(first_offer))

json_path, csv_path = save_offers_data(offers_data, output_dir)
