from ministerio_audit.config import INTERIM_DIR
from pathlib import Path
import yaml
import pandas as pd


DROP_COLUMNS = [
    "offer_data",
    "form_trace",
    "requirements",
    "optional_trace",
]

traces_dir = INTERIM_DIR / "infojobs_applications"

def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _iter_trace_paths():
    for run_dir in sorted(traces_dir.glob("apply_infojobs_*")):
        for path in sorted(run_dir.glob("*.yaml")):
            yield run_dir.name, path


def _build_traces():
    rows = []
    for run_id, path in _iter_trace_paths():
        trace = _load_yaml(path) or {}
        trace["run_id"] = run_id
        trace["trace_path"] = str(path)
        rows.append(trace)

    df = pd.DataFrame(rows)
    if df.empty:
        return df, pd.DataFrame()

    df["questions_answered"] = df["form_trace"].apply(
        lambda items: len(items) if isinstance(items, list) else 0
    )
    df["has_end_time"] = (
        df["end_time"].notna() if "end_time" in df.columns else False
    )
    df["has_offer_data"] = df["offer_data"].notna()
    df["has_optional_trace"] = df["optional_trace"].notna()

    problems = []
    problems.append(
        df.loc[~df["has_end_time"], ["run_id", "cv_id", "offer_id", "trace_path"]]
        .assign(problem="missing_end_time")
    )
    problems.append(
        df.loc[
            (df["already_inscribed"] == False) & (df["questions_answered"] == 0),
            ["run_id", "cv_id", "offer_id", "trace_path"],
        ].assign(problem="no_questions_answered")
    )
    problems.append(
        df.loc[
            (df["already_inscribed"] == False) & (~df["has_offer_data"]),
            ["run_id", "cv_id", "offer_id", "trace_path"],
        ].assign(problem="missing_offer_data")
    )
    problems.append(
        df.loc[
            (df["already_inscribed"] == False) & (~df["has_optional_trace"]),
            ["run_id", "cv_id", "offer_id", "trace_path"],
        ].assign(problem="missing_optional_trace")
    )
    problems_df = pd.concat(problems, ignore_index=True)

    output_dir = INTERIM_DIR / "panels"
    output_dir.mkdir(parents=True, exist_ok=True)
    df.drop(columns=DROP_COLUMNS, errors="ignore").to_csv(
        output_dir / "traces.csv", index=False
    )
    problems_df.to_csv(output_dir / "traces_problems.csv", index=False)
    return df, problems_df


if __name__ == "__main__":
    apps, problems = _build_traces()
    print(apps.head(5))
    print(problems.head(5))
