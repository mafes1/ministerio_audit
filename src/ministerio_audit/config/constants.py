from shutil import which
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

SECRETS_DIR = PROJECT_ROOT / "secrets"
SECRETS_PATH = SECRETS_DIR / "passwords.yaml"

DATA_DIR = PROJECT_ROOT / "data"

INTERIM_DIR = DATA_DIR / "interim"

GECKODRIVER_PATH = which("geckodriver")
CHROMEDRIVER_PATH = which("chromedriver")

INFOJOBS_LOGIN = "https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml"
INFOJOBS_MAIN = "https://www.infojobs.net/"
