from __future__ import annotations

from time import sleep
from datetime import datetime
import logging
import argparse
import os

import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import yaml
import random

from ministerio_audit.config import (
    SECRETS_PATH,
    CHROMEDRIVER_PATH,
    INTERIM_DIR,
    CV_DIR,
    RUNS_DIR,
    OFFERS_DIR,
)
from ministerio_audit.selenium import login_infojobs
from ministerio_audit.selenium.actions import TIME_WAIT, TIME_SLEEP, logout_infojobs
from ministerio_audit.selenium.scrape import scrape_application

DIR_PREFIX = "infojobs_consult"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = (
    INTERIM_DIR / DIR_PREFIX / f"{DIR_PREFIX}_{TIMESTAMP}"
)
LOG_PATH = RUNS_DIR / "selenium" / DIR_PREFIX / f"{DIR_PREFIX}_{TIMESTAMP}.log"

DEFAULT_CVS = [
    "cv01",
    "cv02",
    "cv03",
    "cv04",
    "cv05",
    "cv06",
    "cv07",
    "cv08",
    "cv09",
    "cv10",
    "cv11",
    "cv12",
    "cv13",
    "cv14",
    "cv15",
    "cv16",
]

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def _split_csv_arg(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_args():
    parser = argparse.ArgumentParser(description="Apply InfoJobs offers via Selenium")
    parser.add_argument(
        "--cvs",
        default=",".join(DEFAULT_CVS),
        help="Comma-separated CV ids (default: %(default)s)",
    )
    return parser.parse_args()


def _load_config(cv_ids: list[str]):
    with open(SECRETS_PATH) as f:
        secrets = yaml.safe_load(f).get("accounts", [])
    userdata = {}
    for secret in secrets:
        if secret["id"] not in cv_ids:
            continue
        userdata[secret["id"]] = secret
    return userdata



def _append_cv_results(output_dir, cv_id, rows):
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{cv_id}.yaml"
    existing = []
    if out.exists():
        with out.open(encoding="utf-8") as f:
            existing = yaml.safe_load(f) or []
    existing.extend(rows)
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(existing, f, sort_keys=False, allow_unicode=True)


def main():
    args = _parse_args()
    cv_ids = _split_csv_arg(args.cvs)
    random.shuffle(cv_ids)
    userdata = _load_config(cv_ids)

    logger.info(
        "Starting scraping for consulting offers of %s CV",
        ", ".join(cv_ids),
    )
    logger.debug(
        "Loaded data for %s CV",
        len(userdata)
    )
    if not userdata:
        raise RuntimeError("No accounts configured in secrets file.")

    service = Service(CHROMEDRIVER_PATH)
    driver = uc.Chrome(service=service, use_subprocess=False)
    wait = WebDriverWait(driver, TIME_WAIT)
    try:
        for cv_id, cv_data in userdata.items():
            email = cv_data["infojobs_email"]
            password = cv_data["infojobs_password"]
            login_infojobs(driver, email, password)
            sleep(TIME_SLEEP)
            
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@class, 'trackingMainMenuMyApplication')]")
                )
            ).click()

            _urls = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//li[contains(@id, 'inscription-')]/div/h2/a[@href]")
                )
            )
            urls = [u.get_property("href") for u in _urls]

            logger.info("Found %s applications", len(urls))

            for url in urls:
                driver.get(url)
                data = {
                    "cv_id": cv_id,
                    "url": url,
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                }
                data.update(scrape_application(driver, wait))
                _append_cv_results(OUTPUT_DIR, cv_id, [data])
                sleep(TIME_SLEEP)
            driver.find_element(
                By.ID, "menu_tab_26"
            ).click()  # go to empleos so we have avatar
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//form[@aria-label='Buscar ofertas']")
                )
            )
            sleep(TIME_SLEEP)
            logout_infojobs(driver)
            sleep(TIME_SLEEP)

    except Exception:
        logger.exception("Failed while consulting offers")
        raise

    finally:
       if not os.environ.get("KEEP_BROWSER_OPEN"):
           driver.quit()


if __name__ == "__main__":
    main()
