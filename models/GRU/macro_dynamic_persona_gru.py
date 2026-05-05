"""
macro_dynamic_persona_gru.py
============================
Build quarterly macro-conditioned persona scores with a small GRU.

Inputs:
  - macro_data_processed/processed_v2.xlsx
  - models/GRU/persona_scores/persona_scores_all_investors.csv

Outputs:
  - quarterly_persona_macro.csv: cleaned quarterly training table
  - gru_predictions.csv: observed persona scores and GRU dynamic scores
  - gru_training_history.csv: train/test loss by epoch
  - gru_model.pt: fitted model weights
  - plots/: loss curve, investor trajectories, macro-state heatmap

The persona input may contain multiple source documents for a year, half-year,
or quarter. Instead of duplicating every annual letter equally, this script
expands documents to covered quarters and uses specificity-weighted averaging:
quarter documents receive the highest weight, half-year documents a medium
weight, and annual documents a lower background weight.
"""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

os.environ.setdefault("MPLCONFIGDIR", str(Path("models/GRU/.mplconfig").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("models/GRU/.cache").resolve()))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


DEFAULT_PERSONA_CSV = Path("models/GRU/persona_scores/persona_scores_all_investors.csv")
DEFAULT_MACRO_XLSX = Path("macro_data_processed/processed_v2.xlsx")
DEFAULT_OUTPUT_DIR = Path("models/GRU/macro_dynamic_outputs")

PERSONA_COLS = [
    "persona_risk_tolerance",
    "persona_time_horizon",
    "persona_loss_aversion",
    "persona_macro_sensitivity",
]

MACRO_COLS = ["inflation", "cycle", "unemployment", "monetary", "stress"]

SPECIFICITY_WEIGHTS = {
    "quarter": 1.00,
    "half": 0.75,
    "year": 0.45,
}


@dataclass
class SequenceBundle:
    x: np.ndarray
    y: np.ndarray
    meta: pd.DataFrame
    feature_cols: list[str]
    target_cols: list[str]
    train_mask: np.ndarray


class MacroPersonaGRU(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        num_layers: int = 1,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        effective_dropout = dropout if num_layers > 1 else 0.0
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=effective_dropout,
        )
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, output_size),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, hidden = self.gru(x)
        return self.head(hidden[-1])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a GRU that maps macro states to dynamic investor persona scores."
    )
    parser.add_argument("--persona_csv", type=Path, default=DEFAULT_PERSONA_CSV)
    parser.add_argument("--macro_xlsx", type=Path, default=DEFAULT_MACRO_XLSX)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sequence_length", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--hidden_size", type=int, default=32)
    parser.add_argument("--num_layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--learning_rate", type=float, default=0.01)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--test_fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def quarter_sort_key(date_value: str) -> tuple[int, int]:
    text = str(date_value).strip()
    if "-Q" in text:
        year_text, quarter_text = text.split("-Q", 1)
        return int(year_text), int(quarter_text)
    if "Q" in text:
        quarter_text, year_text = text.split("Q", 1)
        year = int(year_text)
        if year < 100:
            year += 2000 if year <= 40 else 1900
        return year, int(quarter_text)
    raise ValueError(f"Unsupported quarter date: {date_value!r}")


def to_macro_date(year: int, quarter: int) -> str:
    return f"{quarter}Q{year % 100:02d}"


def covered_quarters(row: pd.Series) -> Iterable[int]:
    period_type = str(row.get("period_type", "")).strip().lower()
    if period_type == "quarter":
        quarter = row.get("quarter")
        if pd.notna(quarter):
            yield int(quarter)
        return

    if period_type == "half":
        half = row.get("half")
        if pd.notna(half) and int(half) == 2:
            yield from (3, 4)
        else:
            yield from (1, 2)
        return

    yield from (1, 2, 3, 4)


def load_macro(macro_xlsx: Path) -> pd.DataFrame:
    raw = pd.read_excel(macro_xlsx, sheet_name="labeling", header=None)
    macro = raw.iloc[1:, 12:19].copy()
    macro.columns = raw.iloc[1, 12:19].tolist()
    macro = macro.iloc[1:].copy()
    macro = macro.rename(
        columns={
            "Date": "Date",
            "Unemployment": "unemployment",
            "macro state": "macro_state_label",
        }
    )
    macro.columns = [str(col).strip().replace(" ", "_") for col in macro.columns]
    macro = macro.rename(columns={"macro_state": "macro_state_label"})
    macro = macro.dropna(subset=["Date"])
    for col in MACRO_COLS:
        macro[col] = pd.to_numeric(macro[col], errors="coerce")
    macro = macro.dropna(subset=MACRO_COLS)
    sort_parts = macro["Date"].map(quarter_sort_key)
    macro["year"] = [part[0] for part in sort_parts]
    macro["quarter"] = [part[1] for part in sort_parts]
    macro = macro.sort_values(["year", "quarter"]).reset_index(drop=True)
    return macro[["Date", "year", "quarter", *MACRO_COLS, "macro_state_label"]]


def load_persona(persona_csv: Path) -> pd.DataFrame:
    persona = pd.read_csv(persona_csv)
    missing = [col for col in PERSONA_COLS if col not in persona.columns]
    if missing:
        raise ValueError(f"Persona CSV is missing columns: {missing}")

    drop_cols = [col for col in persona.columns if col.startswith("dim_")]
    persona = persona.drop(columns=drop_cols)
    persona["period_type"] = persona["period_type"].fillna("year").str.lower()
    persona["year"] = pd.to_numeric(persona["year"], errors="coerce")
    persona["word_count"] = pd.to_numeric(persona.get("word_count", 0), errors="coerce").fillna(0)
    persona = persona.dropna(subset=["investor_id", "year", *PERSONA_COLS])
    persona["year"] = persona["year"].astype(int)
    return persona


def expand_persona_to_quarters(persona: pd.DataFrame) -> pd.DataFrame:
    expanded_rows = []
    for _, row in persona.iterrows():
        period_type = str(row["period_type"]).lower()
        specificity = SPECIFICITY_WEIGHTS.get(period_type, SPECIFICITY_WEIGHTS["year"])
        base_weight = math.log1p(max(float(row["word_count"]), 0.0))
        weight = max(base_weight * specificity, 1e-6)
        for quarter in covered_quarters(row):
            expanded = {
                "investor_id": row["investor_id"],
                "year": int(row["year"]),
                "quarter": int(quarter),
                "Date": to_macro_date(int(row["year"]), int(quarter)),
                "period_type": period_type,
                "filename": row.get("filename", ""),
                "word_count": float(row["word_count"]),
                "source_weight": weight,
            }
            for col in PERSONA_COLS:
                expanded[col] = float(row[col])
            expanded_rows.append(expanded)
    return pd.DataFrame(expanded_rows)


def weighted_average(group: pd.DataFrame, col: str) -> float:
    return float(np.average(group[col], weights=group["source_weight"]))


def aggregate_quarterly_persona(expanded: pd.DataFrame) -> pd.DataFrame:
    grouped_rows = []
    group_cols = ["investor_id", "Date", "year", "quarter"]
    for keys, group in expanded.groupby(group_cols, sort=False):
        row = dict(zip(group_cols, keys))
        for col in PERSONA_COLS:
            row[col] = weighted_average(group, col)
        row["source_count"] = int(len(group))
        row["quarter_source_count"] = int((group["period_type"] == "quarter").sum())
        row["half_source_count"] = int((group["period_type"] == "half").sum())
        row["year_source_count"] = int((group["period_type"] == "year").sum())
        row["total_word_count"] = int(group["word_count"].sum())
        row["source_files"] = "; ".join(sorted({str(v) for v in group["filename"].dropna() if str(v)}))
        grouped_rows.append(row)
    quarterly = pd.DataFrame(grouped_rows)
    return quarterly.sort_values(["investor_id", "year", "quarter"]).reset_index(drop=True)


def build_modeling_table(persona_csv: Path, macro_xlsx: Path) -> pd.DataFrame:
    macro = load_macro(macro_xlsx)
    persona = load_persona(persona_csv)
    expanded = expand_persona_to_quarters(persona)
    quarterly_persona = aggregate_quarterly_persona(expanded)
    modeling = quarterly_persona.merge(
        macro.drop(columns=["year", "quarter"]),
        on="Date",
        how="inner",
        validate="many_to_one",
    )
    state_dummies = pd.get_dummies(modeling["macro_state_label"], prefix="state", dtype=float)
    investor_dummies = pd.get_dummies(modeling["investor_id"], prefix="investor", dtype=float)
    modeling = pd.concat([modeling, state_dummies, investor_dummies], axis=1)
    return modeling.sort_values(["investor_id", "year", "quarter"]).reset_index(drop=True)


def build_sequences(modeling: pd.DataFrame, sequence_length: int, test_fraction: float) -> SequenceBundle:
    state_cols = sorted([col for col in modeling.columns if col.startswith("state_")])
    investor_cols = sorted([col for col in modeling.columns if col.startswith("investor_INV_")])
    feature_cols = [*MACRO_COLS, *state_cols, *investor_cols]
    x_values = modeling[feature_cols].to_numpy(dtype=np.float32)
    y_values = modeling[PERSONA_COLS].to_numpy(dtype=np.float32)

    x_rows = []
    y_rows = []
    meta_rows = []
    train_mask = []

    for investor_id, group in modeling.groupby("investor_id", sort=False):
        group_indices = group.index.to_list()
        if len(group_indices) < sequence_length:
            continue
        split_position = max(sequence_length, int(math.ceil(len(group_indices) * (1 - test_fraction))))
        for local_pos in range(sequence_length - 1, len(group_indices)):
            current_index = group_indices[local_pos]
            window_indices = group_indices[local_pos - sequence_length + 1 : local_pos + 1]
            x_rows.append(x_values[window_indices])
            y_rows.append(y_values[current_index])
            meta = modeling.loc[
                current_index,
                [
                    "investor_id",
                    "Date",
                    "year",
                    "quarter",
                    "macro_state_label",
                    "source_count",
                    "quarter_source_count",
                    "half_source_count",
                    "year_source_count",
                    "total_word_count",
                ],
            ].to_dict()
            meta_rows.append(meta)
            train_mask.append(local_pos < split_position)

    if not x_rows:
        raise ValueError("No GRU sequences could be built. Try a shorter --sequence_length.")

    return SequenceBundle(
        x=np.stack(x_rows),
        y=np.stack(y_rows),
        meta=pd.DataFrame(meta_rows),
        feature_cols=feature_cols,
        target_cols=PERSONA_COLS,
        train_mask=np.array(train_mask, dtype=bool),
    )


def train_model(bundle: SequenceBundle, args: argparse.Namespace) -> tuple[MacroPersonaGRU, pd.DataFrame]:
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    model = MacroPersonaGRU(
        input_size=bundle.x.shape[-1],
        hidden_size=args.hidden_size,
        output_size=bundle.y.shape[-1],
        num_layers=args.num_layers,
        dropout=args.dropout,
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    criterion = nn.MSELoss()

    x_train = torch.tensor(bundle.x[bundle.train_mask], dtype=torch.float32)
    y_train = torch.tensor(bundle.y[bundle.train_mask], dtype=torch.float32)
    x_test = torch.tensor(bundle.x[~bundle.train_mask], dtype=torch.float32)
    y_test = torch.tensor(bundle.y[~bundle.train_mask], dtype=torch.float32)
    loader = DataLoader(
        TensorDataset(x_train, y_train),
        batch_size=args.batch_size,
        shuffle=True,
    )

    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += float(loss.item()) * len(batch_x)

        model.eval()
        with torch.no_grad():
            train_loss = criterion(model(x_train), y_train).item()
            test_loss = criterion(model(x_test), y_test).item() if len(x_test) else np.nan
        history.append(
            {
                "epoch": epoch,
                "batch_train_loss": total_loss / max(len(x_train), 1),
                "train_loss": train_loss,
                "test_loss": test_loss,
            }
        )

    return model, pd.DataFrame(history)


def make_predictions(model: MacroPersonaGRU, bundle: SequenceBundle) -> pd.DataFrame:
    model.eval()
    with torch.no_grad():
        pred = model(torch.tensor(bundle.x, dtype=torch.float32)).numpy()

    result = bundle.meta.copy()
    result["split"] = np.where(bundle.train_mask, "train", "test")
    for idx, col in enumerate(PERSONA_COLS):
        result[f"observed_{col}"] = bundle.y[:, idx]
        result[f"macro_dynamic_{col}"] = pred[:, idx]
        result[f"residual_{col}"] = bundle.y[:, idx] - pred[:, idx]
    return result


def plot_loss(history: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(8, 4.5))
    plt.plot(history["epoch"], history["train_loss"], label="train")
    if history["test_loss"].notna().any():
        plt.plot(history["epoch"], history["test_loss"], label="test")
    plt.xlabel("Epoch")
    plt.ylabel("MSE")
    plt.title("GRU Training Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "gru_loss_curve.png", dpi=180)
    plt.close()


def plot_investor_trajectories(predictions: pd.DataFrame, output_dir: Path) -> None:
    for investor_id, group in predictions.groupby("investor_id", sort=True):
        group = group.sort_values(["year", "quarter"])
        x = np.arange(len(group))
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
        axes = axes.ravel()
        labels = group["Date"].tolist()
        tick_step = max(1, len(labels) // 8)
        for ax, col in zip(axes, PERSONA_COLS):
            ax.plot(x, group[f"observed_{col}"], label="observed", linewidth=1.8)
            ax.plot(x, group[f"macro_dynamic_{col}"], label="GRU dynamic", linewidth=1.8)
            ax.set_title(col.replace("persona_", "").replace("_", " ").title())
            ax.set_ylim(0, 1)
            ax.grid(alpha=0.25)
        for ax in axes[-2:]:
            ax.set_xticks(x[::tick_step])
            ax.set_xticklabels(labels[::tick_step], rotation=45, ha="right")
        axes[0].legend(loc="best")
        fig.suptitle(f"{investor_id}: Observed vs Macro-Dynamic Persona")
        fig.tight_layout()
        fig.savefig(output_dir / f"persona_observed_vs_dynamic_{investor_id.lower()}.png", dpi=180)
        plt.close(fig)


def plot_macro_state_heatmap(modeling: pd.DataFrame, output_dir: Path) -> None:
    heat = modeling.groupby("macro_state_label")[PERSONA_COLS].mean().sort_index()
    fig, ax = plt.subplots(figsize=(9, max(3.5, 0.45 * len(heat))))
    image = ax.imshow(heat.to_numpy(), aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(PERSONA_COLS)))
    ax.set_xticklabels([col.replace("persona_", "").replace("_", " ").title() for col in PERSONA_COLS], rotation=25, ha="right")
    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels(heat.index)
    ax.set_title("Average Persona Score by Macro State")
    fig.colorbar(image, ax=ax, label="Persona score")
    fig.tight_layout()
    fig.savefig(output_dir / "macro_state_persona_heatmap.png", dpi=180)
    plt.close(fig)


def write_outputs(
    model: MacroPersonaGRU,
    modeling: pd.DataFrame,
    bundle: SequenceBundle,
    predictions: pd.DataFrame,
    history: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    modeling.to_csv(output_dir / "quarterly_persona_macro.csv", index=False)
    predictions.to_csv(output_dir / "gru_predictions.csv", index=False)
    history.to_csv(output_dir / "gru_training_history.csv", index=False)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "feature_cols": bundle.feature_cols,
            "target_cols": bundle.target_cols,
        },
        output_dir / "gru_model.pt",
    )

    plot_loss(history, plot_dir)
    plot_investor_trajectories(predictions, plot_dir)
    plot_macro_state_heatmap(modeling, plot_dir)


def main() -> None:
    args = parse_args()
    modeling = build_modeling_table(args.persona_csv, args.macro_xlsx)
    bundle = build_sequences(modeling, args.sequence_length, args.test_fraction)
    model, history = train_model(bundle, args)
    predictions = make_predictions(model, bundle)
    write_outputs(model, modeling, bundle, predictions, history, args.output_dir)

    print(f"Quarterly modeling rows: {len(modeling)}")
    print(f"GRU sequences: {len(bundle.x)}")
    print(f"Train sequences: {int(bundle.train_mask.sum())}")
    print(f"Test sequences: {int((~bundle.train_mask).sum())}")
    print(f"Features used: {len(bundle.feature_cols)}")
    print(f"Outputs written to: {args.output_dir}")


if __name__ == "__main__":
    main()
