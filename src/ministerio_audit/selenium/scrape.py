"""Scrape operations with Selenium."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime
import re
import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
from bs4 import BeautifulSoup
from ministerio_audit.config import INFOJOBS_LOGIN
import logging

logger = logging.getLogger(__name__)


def get_offer_elements(driver, wait):
    return wait.until(
        EC.visibility_of_all_elements_located(
            (By.XPATH, "//li[@class='ij-List-item sui-PrimitiveLinkBox']")
        )
    )


def get_offer_details(driver, wait):
    data = {}
    logger.debug("Waiting for headers of offer")
    header = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//article[@class='ij-Box ij-OfferDetailHeader']")
        )
    )
    title = header.find_element(
        By.XPATH, "//div[contains(@class, 'OfferDetailHeader-title')]"
    ).find_element(By.TAG_NAME, "h1")
    data["title"] = title.text
    logger.debug("Title located %s" % title.text)

    company_name = header.find_element(
        By.XPATH, "//div[contains(@class, 'companyLogo-companyName')]"
    )
    data["company_name"] = company_name.text
    logger.debug("Company located %s" % company_name.text)

    try:
        logger.debug("Trying locating company rating")
        rating_company = header.find_element(
            By.XPATH, "//p[contains(@class, 'sui-MoleculeRating-label')]"
        )
        data["rating_company"] = rating_company.text
        logger.debug("Company rating not located")
    except:
        data["rating_company"] = ""
        logger.debug("No company rating located")
    
    details = driver.find_elements(
        By.XPATH,
        "//div[contains(@class, 'OfferDetailHeader-detailsList')]"
        "//div[contains(@class, 'OfferDetailHeader-detailsList-item')]",
    )
    data["details"] = [d.text for d in details]
    logging.debug("Found %s details" % str(len(details)))

    publicada = header.find_element(
        By.XPATH, "//span[@data-testid='sincedate-tag']"
    )
    data["publicada"] = publicada.text
    logging.debug("Found date %s" % publicada.text)

    soup = BeautifulSoup(driver.page_source, "lxml")

    req = {}
    req_block = soup.find("h3", string="Requisitos").find_next("dl")
    for dt, dd in zip(req_block.find_all("dt"), req_block.find_all("dd")):
        key = dt.get_text(strip=True).lower().replace(" ", "_")
        value = dd.get_text("\n", strip=True)
        req[key] = value
    data["requisitos"] = req
    logging.debug("Found %s requirements" % str(len(req)))

    desc_block = soup.find("h3", string="Descripción")
    desc = ""
    for el in desc_block.next_sibling():
        desc += el.get_text("\n") + "\n"
    desc = re.sub(r"(\n){2,}", r"\1\1", desc).strip()
    data["descripcion"] = desc
    logging.debug("Found description block of %s chars" % str(len(desc)))

    cond = {}
    details_dl = desc_block.find_next("dl")
    for dt, dd in zip(details_dl.find_all("dt"), details_dl.find_all("dd")):
        key = dt.get_text(strip=True).lower().replace(" ", "_")
        if dd.find_all("a"):
            cond[key] = [a.get_text("\n", strip=True) for a in dd.find_all("a")]
        else:
            cond[key] = dd.get_text("\n", strip=True)
    data["condiciones"] = cond
    logging.debug("Found %s conditions" % str(len(cond)))

    footer = soup.find(
        "h3",
        string=lambda s: s
        and ("inscritos" in s.lower() or "vacantes" in s.lower()),
    )
    data["inscritos"] = footer.get_text(strip=True)
    logger.debug("Found applicants")
    logger.info("Ended first page scraping for offer")
    return data


def parse_fieldsets(form_html):
    soup = BeautifulSoup(form_html, "lxml")
    form = soup.find("form") or soup
    fieldsets = []
    for idx, fieldset in enumerate(form.find_all("fieldset"), start=1):
        legend = fieldset.find("legend")
        question = legend.get_text(" ", strip=True) if legend else ""
        inputs = []
        for input_el in fieldset.find_all(["input", "textarea", "select"]):
            tag_name = input_el.name
            input_type = (
                input_el.get("type", "text") if tag_name == "input" else tag_name
            )
            input_id = input_el.get("id", "")
            input_name = input_el.get("name", "")
            label_text = ""
            if input_id:
                label = fieldset.find("label", attrs={"for": input_id})
                if label:
                    label_text = label.get_text(" ", strip=True)
            entry = {
                "type": input_type,
                "id": input_id,
                "name": input_name,
                "label": label_text,
            }
            if tag_name == "select":
                entry["options"] = [
                    {
                        "value": opt.get("value", ""),
                        "label": opt.get_text(" ", strip=True),
                    }
                    for opt in input_el.find_all("option")
                ]
            inputs.append(entry)
        fieldsets.append(
            {
                "index": idx,
                "question": question,
                "inputs": inputs,
            }
        )
    return fieldsets

def _csv_safe_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _flatten_for_csv(item, prefix=""):
    flattened = {}
    for key, value in item.items():
        col = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            flattened.update(_flatten_for_csv(value, col))
        else:
            flattened[col] = _csv_safe_value(value)
    return flattened


def save_offers_data(offers_data, output_dir, prefix="infojobs_offers"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_path / f"{prefix}_{timestamp}.json"
    csv_path = output_path / f"{prefix}_{timestamp}.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(offers_data, f, ensure_ascii=False, indent=2)

    flattened_rows = [_flatten_for_csv(item) for item in offers_data]
    fieldnames = sorted({key for row in flattened_rows for key in row.keys()})
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in flattened_rows:
            row = {key: row.get(key) for key in fieldnames}
            writer.writerow(row)

    return json_path, csv_path


def scrape_application(driver, wait):
    data = {}
    job_title = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//h2[@class='job-list-title']")
        )
    )
    data["job_title"] = job_title.text
    try:
        title_link = job_title.find_element(By.TAG_NAME, "a")
        data["offer_link"] = title_link.get_attribute("href")
    except NoSuchElementException:
        data["offer_link"] = job_title.get_attribute("href") or ""

    try:
        job_subtitle = driver.find_element(
            By.XPATH, "//h3[@class='job-list-subtitle']"
        )
    except NoSuchElementException:
        logger.info("No subtitle info found for %s", data["offer_link"])
        job_subtitle = None

    data["job_subtitle"] = job_subtitle.text if job_subtitle else None

    job_subtitle_href = None
    if job_subtitle:
        try:
            job_subtitle_href = job_subtitle.find_element(
                By.XPATH, ".//a"
            ).get_attribute("href")
        except NoSuchElementException:
            logger.info("No subtitle href info found for %s", data["offer_link"])
    data["job_subtitle_href"] = job_subtitle_href

    details = []
    try:
        details_ul = job_title.find_element(
            By.XPATH, "following-sibling::ul[1]"
        )
        details = [
            item.text.strip()
            for item in details_ul.find_elements(By.TAG_NAME, "li")
            if item.text.strip()
        ]
    except NoSuchElementException:
        logger.info("No subtitle details list found for %s", data["offer_link"])

    data["job_details"] = details

    try:
        next_div = job_title.find_element(
            By.XPATH, "parent::div/following-sibling::div[1]"
        ).get_attribute("innerText")
    except NoSuchElementException:
        logger.info("No next div found for %s", data["offer_link"])
        next_div = ""

    data["next_div"] = next_div

    data["all_job_desc"] = driver.find_element(
        By.XPATH, "//div[contains(@class, 'job-list')]"
    ).get_attribute("innerText")

    events = driver.find_elements(By.XPATH, "//li[starts-with(@id, 'event-')]")
    data["events"] = []
    for event in events:
        text = event.find_element(By.CSS_SELECTOR, "p#event-text").text.strip()
        timestamp = event.find_element(By.TAG_NAME, "time").text.strip()
        data["events"].append({"text": text, "time": timestamp})
    return data
