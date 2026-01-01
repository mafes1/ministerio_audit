import argparse
import mailbox
import re
from pathlib import Path

import pandas as pd
import yaml
from bs4 import BeautifulSoup

from ministerio_audit.config import INTERIM_DIR, DATA_DIR

MAILROOT = DATA_DIR / "raw" / "maildir"
CONSULT_DIR = INTERIM_DIR / "infojobs_consult"
PANEL_DIR = INTERIM_DIR / "panels"


def iter_maildirs(root: Path):
    for p in root.rglob("cur"):
        yield p.parent


def extract_text(msg):
    parts = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                text = payload.decode(errors="ignore")

                if ctype == "text/html":
                    text = BeautifulSoup(text, "lxml").get_text(" ")

                parts.append(text)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            parts.append(payload.decode(errors="ignore"))

    return "\n".join(parts).strip()


def _extract_infojobs_links(text: str) -> list[str]:
    return re.findall(r"https?://(?:www\.)?infojobs\.net/[^\s)\"']+", text)


def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _iter_consult_paths(root: Path):
    for run_dir in sorted(root.glob("infojobs_consult_*")):
        for path in sorted(run_dir.glob("*.yaml")):
            yield run_dir, path


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Build a panel CSV from consult YAMLs and InfoJobs maildir.",
    )
    parser.add_argument(
        "--consult-dir",
        type=Path,
        default=CONSULT_DIR,
        help="Directory with consult runs (default: %(default)s)",
    )
    parser.add_argument(
        "--mail-root",
        type=Path,
        default=MAILROOT,
        help="Maildir root to scan (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PANEL_DIR / "consult_offers.csv",
        help="Output CSV path (default: %(default)s)",
    )
    return parser.parse_args()


def _build_panel(consult_dir: Path, mail_root: Path) -> pd.DataFrame:
    matches = []
    for maildir in iter_maildirs(mail_root):
        md = mailbox.Maildir(maildir, factory=None)
        for _, msg in md.items():
            subj = (msg.get("Subject") or "").lower()
            from_ = (msg.get("From") or "").lower()
            if "te has inscrito a una oferta" in subj and "infojobs" in from_:
                body = extract_text(msg)
                matches.append(
                    {
                        "date": msg.get("Date"),
                        "subject": msg.get("Subject"),
                        "from": msg.get("From"),
                        "body": body,
                    }
                )

    mail_links = {}
    for match in matches:
        for link in _extract_infojobs_links(match["body"]):
            mail_links.setdefault(link, []).append(match)

    rows = []
    for run_dir, path_yaml in _iter_consult_paths(consult_dir):
        offers = _load_yaml(path_yaml) or []
        for offer in offers:
            offer = dict(offer)
            offer["run_id"] = run_dir.name
            offer["cv_id"] = path_yaml.stem
            link = offer.get("offer_link", "")
            mail_hits = mail_links.get(link, [])
            offer["mail_confirmed"] = bool(mail_hits)
            offer["mail_dates"] = " | ".join(
                hit.get("date", "") for hit in mail_hits if hit.get("date")
            )
            rows.append(offer)

    df = pd.DataFrame(rows)
    if not df.empty and "events" in df.columns:
        df_events = (
            df["events"]
            .explode(ignore_index=False)
            .apply(pd.Series)
            .rename(columns={"text": "event", "time": "event_time"})
        )
        df = pd.concat([df.drop(columns="events"), df_events], axis=1)

    return df


def main():
    args = _parse_args()
    df = _build_panel(args.consult_dir, args.mail_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
