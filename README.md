# Ministerio Audit

Experiment to audit potential discrimination in job-platform selection (Infojobs, Jobfie).
We maintain multiple controlled CV profiles, automate applications with Selenium, and analyze outcomes via synced maildir.

## Project layout

- `config/` example configs (copy into `secrets/`)
- `docs/` protocol, data dictionary, ops notes
- `data/raw/` immutable source data
- `data/interim/` cleaned or normalized datasets
- `data/processed/` final analysis tables
- `runs/` logs, screenshots, and sync artifacts per run
- `scripts/` CLI entrypoints
- `src/ministerio_audit/` reusable code (Selenium helpers, parsing, analysis)
- `experiments/` one-off experiments and scratch work

## Data sources

- `data/raw/cv/odt/` manual CVs (ODT)
- `data/raw/cv/pdf/` manual CVs exported to PDF
- `data/raw/cv/infojobs_export/` CVs exported from Infojobs (distinct source)
- `data/raw/cv/pics/` profile images
- `data/raw/maildir/` synced mailboxes (generated)
- `data/raw/external/` invoices or third-party docs

## Mail sync

1) Copy `config/mbsync.example.conf` to `secrets/mbsyncrc` and fill real values.
2) Run:

```bash
scripts/mail/sync_mail.sh
```

## Editable package

```bash
pip install -e .
```

This enables imports like `from ministerio_audit.selenium import actions` in scripts and notebooks.
