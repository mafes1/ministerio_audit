from shutil import which
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

SECRETS_DIR = PROJECT_ROOT / "secrets"
SECRETS_PATH = SECRETS_DIR / "passwords.yaml"

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CV_DIR = RAW_DIR / "cv"
OFFERS_DIR = RAW_DIR / "offers"
INTERIM_DIR = DATA_DIR / "interim"

RUNS_DIR = PROJECT_ROOT / "runs"

GECKODRIVER_PATH = which("geckodriver")
CHROMEDRIVER_PATH = which("chromedriver")

INFOJOBS_LOGIN = "https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml"
INFOJOBS_MAIN = "https://www.infojobs.net/"
