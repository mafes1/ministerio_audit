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
from selenium.common.exceptions import TimeoutException
from time import sleep
from bs4 import BeautifulSoup
from ministerio_audit.config import INFOJOBS_LOGIN


def get_offer_elements(driver, wait):
    return wait.until(
        EC.visibility_of_all_elements_located(
            (By.XPATH, "//li[@class='ij-List-item sui-PrimitiveLinkBox']")
        )
    )


def get_offer_details(driver, wait):
    data = {}
    header = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//article[@class='ij-Box ij-OfferDetailHeader']")
        )
    )
    title = header.find_element(
        By.XPATH, "//div[contains(@class, 'OfferDetailHeader-title')]"
    ).find_element(By.TAG_NAME, "h1")
    data["title"] = title.text

    company_name = header.find_element(
        By.XPATH, "//div[contains(@class, 'companyLogo-companyName')]"
    )
    data["company_name"] = company_name.text

    try:
        rating_company = header.find_element(
        By.XPATH, "//p[contains(@class, 'sui-MoleculeRating-label')]"
        )
        data["rating_company"] = rating_company.text
    except:
        data["rating_company"] = ""

    details = driver.find_elements(
        By.XPATH,
        "//div[contains(@class, 'OfferDetailHeader-detailsList')]"
        "//div[contains(@class, 'OfferDetailHeader-detailsList-item')]",
    )
    data["details"] = [d.text for d in details]

    publicada = header.find_element(
        By.XPATH, "//span[@data-testid='sincedate-tag']"
    )
    data["publicada"] = publicada.text

    soup = BeautifulSoup(driver.page_source, "lxml")

    req = {}
    req_block = soup.find("h3", string="Requisitos").find_next("dl")
    for dt, dd in zip(req_block.find_all("dt"), req_block.find_all("dd")):
        key = dt.get_text(strip=True).lower().replace(" ", "_")
        value = dd.get_text("\n", strip=True)
        req[key] = value
    data["requisitos"] = req

    desc_block = soup.find("h3", string="Descripción")
    desc = ""
    for el in desc_block.next_sibling():
        desc += el.get_text("\n") + "\n"
    desc = re.sub(r"(\n){2,}", r"\1\1", desc).strip()
    data["descripcion"] = desc

    cond = {}
    details_dl = desc_block.find_next("dl")
    for dt, dd in zip(details_dl.find_all("dt"), details_dl.find_all("dd")):
        key = dt.get_text(strip=True).lower().replace(" ", "_")
        if dd.find_all("a"):
            cond[key] = [a.get_text("\n", strip=True) for a in dd.find_all("a")]
        else:
            cond[key] = dd.get_text("\n", strip=True)
    data["condiciones"] = cond

    footer = soup.find(
        "h3",
        string=lambda s: s
        and ("inscritos" in s.lower() or "vacantes" in s.lower()),
    )
    data["inscritos"] = footer.get_text(strip=True)
    return data



def get_form_text(driver, wait):
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//div[@data-test='apply-button-footer']/button")
        )
    ).click()
    wait.until(
        EC.visibility_of_element_located(
            (By.ID, "myForm")
        )
    )
    soup = BeautifulSoup(driver.page_source, "lxml")
    form = soup.find("form", id="myForm")
    form = re.sub(r"(\n){2,}", r"\1\1", form.get_text("\n").strip())
    driver.back()
    return form


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
