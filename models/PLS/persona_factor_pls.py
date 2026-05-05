"""
persona_factor_pls.py
=====================
Map macro-dynamic persona scores to Fama-French factor exposures with PLS.

Inputs:
  - models/GRU/macro_dynamic_outputs/gru_predictions.csv
  - models/GRU/macro_dynamic_outputs/quarterly_persona_macro.csv
  - famafrench_factor_regression/data/Fama-French Factor Regression (2).xlsx

Outputs:
  - pls_mapping_dataset.csv
  - pls_factor_predictions.csv
  - pls_coefficients.csv
  - ideal_factor_exposures_by_profile.csv
  - plots/

The model is trained on one pooled investor-quarter dataset. It does not use
raw FinBERT embedding dimensions or investor identity as features, so the fitted
mapping can be applied to new user persona profiles.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("models/PLS/.mplconfig").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("models/PLS/.cache").resolve()))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


DEFAULT_GRU_PREDICTIONS = Path("models/GRU/macro_dynamic_outputs/gru_predictions.csv")
DEFAULT_QUARTERLY_MACRO = Path("models/GRU/macro_dynamic_outputs/quarterly_persona_macro.csv")
DEFAULT_FAMA_XLSX = Path("famafrench_factor_regression/data/Fama-French Factor Regression (2).xlsx")
DEFAULT_OUTPUT_DIR = Path("models/PLS/factor_mapping_outputs")

MACRO_COLS = ["inflation", "cycle", "unemployment", "monetary", "stress"]
PERSONA_BASE_COLS = [
    "persona_risk_tolerance",
    "persona_time_horizon",
    "persona_loss_aversion",
    "persona_macro_sensitivity",
]
FACTOR_COLS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Alpha"]

INVESTOR_SHEET_MAP = {
    "INV_BUFFETT": "Warren Buffet",
    "INV_HAWKINS": "Mason Hawkins",
    "INV_GRANTHAM": "Jeremey Grantham",
    "INV_DRIEHAUS": "Richard Driehaus",
    "INV_BARON": "Ron Baron",
    "INV_YACKTMAN": "Don Yacktman",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit PLS mapping from macro-dynamic persona scores to Fama-French factor exposure."
    )
    parser.add_argument("--gru_predictions", type=Path, default=DEFAULT_GRU_PREDICTIONS)
    parser.add_argument("--quarterly_macro", type=Path, default=DEFAULT_QUARTERLY_MACRO)
    parser.add_argument("--fama_xlsx", type=Path, default=DEFAULT_FAMA_XLSX)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--persona_mode", choices=["dynamic", "observed"], default="dynamic")
    parser.add_argument("--n_components", type=int, default=3)
    return parser.parse_args()


def to_year_qtr(date_value: str) -> str:
    text = str(date_value).strip()
    if "-Q" in text:
        return text
    quarter_text, year_text = text.split("Q", 1)
    year = int(year_text)
    if year < 100:
        year += 2000 if year <= 40 else 1900
    return f"{year}-Q{int(quarter_text)}"


def load_fama_french(fama_xlsx: Path) -> pd.DataFrame:
    frames = []
    for investor_id, sheet_name in INVESTOR_SHEET_MAP.items():
        df = pd.read_excel(fama_xlsx, sheet_name=sheet_name)
        df = df.rename(columns={"Year-Qtr": "Year_Qtr"})
        df["investor_id"] = investor_id
        df["Year_Qtr"] = df["Year_Qtr"].astype(str).str.strip()
        for col in FACTOR_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        frames.append(df[["investor_id", "Year_Qtr", *FACTOR_COLS]])
    fama = pd.concat(frames, ignore_index=True)
    return fama.dropna(subset=FACTOR_COLS)


def load_persona_macro(
    gru_predictions: Path,
    quarterly_macro: Path,
    persona_mode: str,
) -> pd.DataFrame:
    predictions = pd.read_csv(gru_predictions)
    quarterly = pd.read_csv(quarterly_macro)
    macro_cols = ["investor_id", "Date", *MACRO_COLS]
    macro = quarterly[macro_cols].drop_duplicates(["investor_id", "Date"])

    prefix = "macro_dynamic_" if persona_mode == "dynamic" else "observed_"
    persona_cols = [f"{prefix}{col}" for col in PERSONA_BASE_COLS]
    keep_cols = [
        "investor_id",
        "Date",
        "year",
        "quarter",
        "macro_state_label",
        "split",
        *persona_cols,
    ]
    persona = predictions[keep_cols].merge(macro, on=["investor_id", "Date"], how="left")
    rename_map = {f"{prefix}{col}": col for col in PERSONA_BASE_COLS}
    persona = persona.rename(columns=rename_map)
    persona["Year_Qtr"] = persona["Date"].map(to_year_qtr)
    return persona


def build_mapping_dataset(args: argparse.Namespace) -> pd.DataFrame:
    persona = load_persona_macro(args.gru_predictions, args.quarterly_macro, args.persona_mode)
    fama = load_fama_french(args.fama_xlsx)
    dataset = persona.merge(
        fama,
        on=["investor_id", "Year_Qtr"],
        how="inner",
        validate="one_to_one",
    )
    state_dummies = pd.get_dummies(dataset["macro_state_label"], prefix="state", dtype=float)
    dataset = pd.concat([dataset, state_dummies], axis=1)
    return dataset.sort_values(["investor_id", "year", "quarter"]).reset_index(drop=True)


def feature_columns(dataset: pd.DataFrame) -> list[str]:
    state_cols = sorted([col for col in dataset.columns if col.startswith("state_")])
    return [*PERSONA_BASE_COLS, *MACRO_COLS, *state_cols]


def fit_pls(dataset: pd.DataFrame, n_components: int) -> tuple[Pipeline, list[str]]:
    features = feature_columns(dataset)
    max_components = min(n_components, len(features), len(FACTOR_COLS), len(dataset) - 1)
    if max_components < 1:
        raise ValueError("Not enough rows/features to fit PLS.")
    model = Pipeline(
        steps=[
            ("x_scaler", StandardScaler()),
            ("pls", PLSRegression(n_components=max_components, scale=True)),
        ]
    )
    train_mask = dataset["split"].eq("train")
    model.fit(dataset.loc[train_mask, features], dataset.loc[train_mask, FACTOR_COLS])
    return model, features


def predict_dataset(model: Pipeline, dataset: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    predicted = model.predict(dataset[features])
    output = dataset[
        [
            "investor_id",
            "Date",
            "Year_Qtr",
            "macro_state_label",
            "split",
            *PERSONA_BASE_COLS,
            *MACRO_COLS,
        ]
    ].copy()
    for idx, col in enumerate(FACTOR_COLS):
        output[f"observed_{col}"] = dataset[col].to_numpy()
        output[f"predicted_{col}"] = predicted[:, idx]
        output[f"residual_{col}"] = dataset[col].to_numpy() - predicted[:, idx]
    return output


def model_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, group in predictions.groupby("split"):
        for factor in FACTOR_COLS:
            observed = group[f"observed_{factor}"]
            predicted = group[f"predicted_{factor}"]
            rows.append(
                {
                    "split": split,
                    "factor": factor,
                    "rmse": mean_squared_error(observed, predicted) ** 0.5,
                    "mae": mean_absolute_error(observed, predicted),
                    "r2": r2_score(observed, predicted),
                }
            )
    return pd.DataFrame(rows)


def coefficient_table(model: Pipeline, features: list[str]) -> pd.DataFrame:
    pls = model.named_steps["pls"]
    coefs = np.asarray(pls.coef_)
    if coefs.shape[0] == len(FACTOR_COLS):
        coefs = coefs.T
    return pd.DataFrame(coefs, index=features, columns=FACTOR_COLS).reset_index(names="feature")


def profile_grid(dataset: pd.DataFrame, model: Pipeline, features: list[str]) -> pd.DataFrame:
    q25 = dataset[PERSONA_BASE_COLS].quantile(0.25)
    q50 = dataset[PERSONA_BASE_COLS].quantile(0.50)
    q75 = dataset[PERSONA_BASE_COLS].quantile(0.75)

    profiles = {
        "Conservative": {
            "persona_risk_tolerance": q25["persona_risk_tolerance"],
            "persona_time_horizon": q50["persona_time_horizon"],
            "persona_loss_aversion": q75["persona_loss_aversion"],
            "persona_macro_sensitivity": q50["persona_macro_sensitivity"],
        },
        "Balanced": q50.to_dict(),
        "Aggressive": {
            "persona_risk_tolerance": q75["persona_risk_tolerance"],
            "persona_time_horizon": q50["persona_time_horizon"],
            "persona_loss_aversion": q25["persona_loss_aversion"],
            "persona_macro_sensitivity": q50["persona_macro_sensitivity"],
        },
        "Macro-Sensitive": {
            "persona_risk_tolerance": q50["persona_risk_tolerance"],
            "persona_time_horizon": q50["persona_time_horizon"],
            "persona_loss_aversion": q50["persona_loss_aversion"],
            "persona_macro_sensitivity": q75["persona_macro_sensitivity"],
        },
    }

    state_cols = sorted([col for col in dataset.columns if col.startswith("state_")])
    rows = []
    for macro_state, state_group in dataset.groupby("macro_state_label"):
        macro_mean = state_group[MACRO_COLS].mean().to_dict()
        for profile_name, persona_values in profiles.items():
            row = {"profile": profile_name, "macro_state_label": macro_state, **persona_values, **macro_mean}
            for col in state_cols:
                row[col] = 1.0 if col == f"state_{macro_state}" else 0.0
            rows.append(row)

    grid = pd.DataFrame(rows)
    for col in features:
        if col not in grid.columns:
            grid[col] = 0.0
    predicted = model.predict(grid[features])
    for idx, factor in enumerate(FACTOR_COLS):
        grid[f"ideal_{factor}"] = predicted[:, idx]
    keep = ["profile", "macro_state_label", *PERSONA_BASE_COLS, *MACRO_COLS, *[f"ideal_{factor}" for factor in FACTOR_COLS]]
    return grid[keep].sort_values(["macro_state_label", "profile"]).reset_index(drop=True)


def plot_predicted_vs_observed(predictions: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    axes = axes.ravel()
    for ax, factor in zip(axes, FACTOR_COLS):
        ax.scatter(
            predictions[f"observed_{factor}"],
            predictions[f"predicted_{factor}"],
            c=np.where(predictions["split"].eq("train"), "#4C78A8", "#F58518"),
            alpha=0.75,
            s=24,
        )
        low = min(predictions[f"observed_{factor}"].min(), predictions[f"predicted_{factor}"].min())
        high = max(predictions[f"observed_{factor}"].max(), predictions[f"predicted_{factor}"].max())
        ax.plot([low, high], [low, high], color="black", linewidth=1, alpha=0.5)
        ax.set_title(factor)
        ax.set_xlabel("Observed")
        ax.set_ylabel("Predicted")
        ax.grid(alpha=0.2)
    fig.suptitle("PLS Factor Mapping: Predicted vs Observed")
    fig.tight_layout()
    fig.savefig(output_dir / "pls_predicted_vs_observed.png", dpi=180)
    plt.close(fig)


def plot_profile_heatmap(profile_predictions: pd.DataFrame, output_dir: Path) -> None:
    for state, group in profile_predictions.groupby("macro_state_label"):
        heat = group.set_index("profile")[[f"ideal_{factor}" for factor in FACTOR_COLS]]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        image = ax.imshow(heat.to_numpy(), aspect="auto", cmap="coolwarm")
        ax.set_xticks(np.arange(len(FACTOR_COLS)))
        ax.set_xticklabels(FACTOR_COLS)
        ax.set_yticks(np.arange(len(heat.index)))
        ax.set_yticklabels(heat.index)
        ax.set_title(f"Ideal Factor Exposure by Profile: {state}")
        fig.colorbar(image, ax=ax, label="Predicted exposure")
        fig.tight_layout()
        safe_state = str(state).lower().replace(" ", "_").replace("/", "_")
        fig.savefig(output_dir / f"profile_factor_heatmap_{safe_state}.png", dpi=180)
        plt.close(fig)


def write_outputs(
    dataset: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    coefficients: pd.DataFrame,
    profile_predictions: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_dir / "pls_mapping_dataset.csv", index=False)
    predictions.to_csv(output_dir / "pls_factor_predictions.csv", index=False)
    metrics.to_csv(output_dir / "pls_metrics.csv", index=False)
    coefficients.to_csv(output_dir / "pls_coefficients.csv", index=False)
    profile_predictions.to_csv(output_dir / "ideal_factor_exposures_by_profile.csv", index=False)
    plot_predicted_vs_observed(predictions, plot_dir)
    plot_profile_heatmap(profile_predictions, plot_dir)


def main() -> None:
    args = parse_args()
    dataset = build_mapping_dataset(args)
    model, features = fit_pls(dataset, args.n_components)
    predictions = predict_dataset(model, dataset, features)
    metrics = model_metrics(predictions)
    coefficients = coefficient_table(model, features)
    profile_predictions = profile_grid(dataset, model, features)
    write_outputs(dataset, predictions, metrics, coefficients, profile_predictions, args.output_dir)

    print(f"PLS mapping rows: {len(dataset)}")
    print(f"Features used: {features}")
    print(f"Targets: {FACTOR_COLS}")
    print(f"Outputs written to: {args.output_dir}")
    print(metrics.pivot(index='factor', columns='split', values='rmse').round(4).to_string())


if __name__ == "__main__":
    main()
