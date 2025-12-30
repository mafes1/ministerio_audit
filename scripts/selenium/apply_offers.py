from __future__ import annotations

from time import sleep
from datetime import datetime
import logging
import argparse

import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import yaml

from ministerio_audit.config import (
    SECRETS_PATH,
    CHROMEDRIVER_PATH,
    INTERIM_DIR,
    CV_DIR,
    RUNS_DIR,
    OFFERS_DIR,
)
from ministerio_audit.selenium import login_infojobs
from ministerio_audit.selenium.actions import (
    TIME_WAIT,
    applybutton_offer_infojobs,
    load_offer_infojobs,
    logout_infojobs,
    populate_fieldsets_infojobs,
    populate_optional_infojobs,
)

SLEEP = 2
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = INTERIM_DIR / f"apply_infojobs_{TIMESTAMP}"
LOG_PATH = RUNS_DIR / "selenium" / f"apply_offers_{TIMESTAMP}.log"

DEFAULT_OFFERS = ["mozo0", "mozo1", "admin0", "admin1"]
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
    "cv17",
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
        "--offers",
        default=",".join(DEFAULT_OFFERS),
        help="Comma-separated offer ids (default: %(default)s)",
    )
    parser.add_argument(
        "--cvs",
        default=",".join(DEFAULT_CVS),
        help="Comma-separated CV ids (default: %(default)s)",
    )
    return parser.parse_args()


def _load_config(cv_ids: list[str], offer_ids: list[str]):
    with open(SECRETS_PATH) as f:
        secrets = yaml.safe_load(f).get("accounts", [])
    with open(CV_DIR / "letters.yaml") as f:
        letters = yaml.safe_load(f)
    userdata = {}
    for secret in secrets:
        if secret["id"] not in cv_ids:
            continue
        userdata[secret["id"]] = secret
        userdata[secret["id"]]["letter"] = letters.get(secret["id"])
    offerdata = {}
    for offer_id in offer_ids:
        with open(OFFERS_DIR / f"{offer_id}.yaml") as f:
            offerdata[offer_id] = yaml.safe_load(f)
    return userdata, offerdata


def _save_run_data(output_dir, cv_id, offer_id, data):
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{cv_id}_{offer_id}.yaml"
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def main():
    args = _parse_args()
    offer_ids = _split_csv_arg(args.offers)
    cv_ids = _split_csv_arg(args.cvs)
    userdata, offerdata = _load_config(cv_ids, offer_ids)
    logger.info(
        "Starting scraping for %s CV at offers %s",
        ", ".join(cv_ids),
        ", ".join(offer_ids),
    )
    logger.debug(
        "Loaded data for %s CV and %s offers",
        len(userdata),
        len(offerdata),
    )
    if not userdata:
        raise RuntimeError("No accounts configured in secrets file.")
    if not offerdata:
        raise RuntimeError("No offers configured in offers directory.")

    service = Service(CHROMEDRIVER_PATH)
    driver = uc.Chrome(service=service, use_subprocess=False)
    wait = WebDriverWait(driver, TIME_WAIT)
    try:
        for cv_id, cv_data in userdata.items():
            email = cv_data["infojobs_email"]
            password = cv_data["infojobs_password"]
            login_infojobs(driver, email, password)
            sleep(SLEEP)

            for offer_id, offer in offerdata.items():
                alias = offer["alias"]
                url = offer["url"]
                logger.info("Applying %s with %s", offer_id, cv_id)

                data = {"cv_id": cv_id, "offer_id": offer_id, "alias": alias, "url": url}
                data["offer_data"] = load_offer_infojobs(driver, url)
                data["form_text"], data["requirements"] = applybutton_offer_infojobs(driver)
                wait.until(EC.visibility_of_element_located((By.ID, "myForm")))

                data["form_trace"] = populate_fieldsets_infojobs(
                    driver,
                    offer["fieldsets"],
                    cv_id,
                    offer_id=offer_id,
                )

                cv_path = CV_DIR / "pdf" / f"{cv_id}.pdf"
                letter = cv_data["letter"]
                data["optional_trace"] = populate_optional_infojobs(
                    driver, cv_path, letter
                )

                submit = driver.find_element(By.ID, "botonEnviar")
                submit.click()
                wait.until(EC.staleness_of(submit))
                _save_run_data(OUTPUT_DIR, cv_id, offer_id, data)
                sleep(SLEEP)

            logout_infojobs(driver)
            sleep(SLEEP)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
