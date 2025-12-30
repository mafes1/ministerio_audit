from __future__ import annotations

from time import sleep
import logging

import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import yaml

from ministerio_audit.config import (
    SECRETS_PATH,
    CHROMEDRIVER_PATH,
    INTERIM_DIR,
    PROJECT_ROOT,
)
from ministerio_audit.selenium import login_infojobs, parse_fieldsets
from ministerio_audit.selenium.actions import applybutton_offer_infojobs, load_offer_infojobs

SLEEP = 2
OUTPUT_DIR = INTERIM_DIR / "infojobs_fieldsets"

logger = logging.getLogger(__name__)


def _load_config():
    with open(SECRETS_PATH) as f:
        secrets = yaml.safe_load(f).get("accounts", [])
    with open(PROJECT_ROOT / "config" / "urls.yaml") as f:
        offers = yaml.safe_load(f).get("offers", {})
    return secrets, offers


def _scrape_offer_fieldsets(driver, offer_id, alias, url):
    out = OUTPUT_DIR / f"{offer_id}.yaml"
    logger.info("Scraping fieldsets for %s (%s)", alias, offer_id)
    try:
        load_offer_infojobs(driver, url)
        applybutton_offer_infojobs(driver)
        form = driver.find_element(By.ID, "myForm")
        form_html = form.get_attribute("outerHTML")
        fieldset_data = parse_fieldsets(form_html)
        with out.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    "offer_id": offer_id,
                    "alias": alias,
                    "url": url,
                    "fieldsets": fieldset_data
                },
                f,
                sort_keys=False,
                allow_unicode=True,
            )
    except Exception:
        logger.exception("Failed to scrape fieldsets for %s (%s)", alias, offer_id)


def main():
    secrets, offers = _load_config()
    if not secrets:
        raise RuntimeError("No accounts configured in secrets file.")
    if not offers:
        raise RuntimeError("No offers configured in config/urls.yaml.")

    secret = secrets[-1]
    email = secret["infojobs_email"]
    password = secret["infojobs_password"]

    service = Service(CHROMEDRIVER_PATH)
    driver = uc.Chrome(service=service, use_subprocess=False)
    try:
        login_infojobs(driver, email, password)
        sleep(SLEEP)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for offer_id, v in offers.items():
            alias, url = v["alias"], v["url"]
            _scrape_offer_fieldsets(driver, offer_id, alias, url)
        sleep(SLEEP)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
