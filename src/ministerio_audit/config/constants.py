from pathlib import Path
from shutil import which
import os


def _find_project_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return start.parents[3]


PROJECT_ROOT = _find_project_root(Path(__file__).resolve())

def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default

SECRETS_DIR = _env_path("SECRETS_DIR", PROJECT_ROOT / "secrets")
SECRETS_PATH = _env_path("SECRETS_PATH", SECRETS_DIR / "passwords.yaml")

DATA_DIR = _env_path("DATA_DIR", PROJECT_ROOT / "data")
RAW_DIR = DATA_DIR / "raw"
CV_DIR = RAW_DIR / "cv"
OFFERS_DIR = RAW_DIR / "offers"
INTERIM_DIR = DATA_DIR / "interim"

RUNS_DIR = _env_path("RUNS_DIR", PROJECT_ROOT / "runs")

GECKODRIVER_PATH = which("geckodriver")
CHROMEDRIVER_PATH = which("chromedriver")

INFOJOBS_LOGIN = "https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml"
INFOJOBS_MAIN = "https://www.infojobs.net/"
