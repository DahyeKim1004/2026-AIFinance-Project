"""
persona_axis_extraction.py
==========================
Phase 1: Contrastive FinBERT Persona Score Extraction

Pipeline:
  1. Define seed sentences for 4 behavioural axes (high / low poles)
  2. Encode seeds with ProsusAI/FinBERT → compute normalised axis direction vectors
  3. Score pre-computed letter embeddings (from CSV) against each axis via sigmoid dot product
  4. Output enriched CSV with 4 persona score columns

Usage:
  python persona_axis_extraction.py \
      --input  finbert_embeddings_baron.csv \
      --output finbert_embeddings_baron_with_persona.csv \
      --save_axes axis_vectors.npy
"""

import argparse
import os
from pathlib import Path
import numpy as np
import pandas as pd

# Transformers can otherwise import optional vision dependencies through
# torchvision. This pipeline is text-only, and some pyenv builds lack _lzma,
# which torchvision imports indirectly.
os.environ.setdefault("TRANSFORMERS_NO_TORCHVISION", "1")

try:
    from scipy.special import expit   # sigmoid
except ImportError:
    def expit(x):
        return 1 / (1 + np.exp(-x))

# ── optional: only imported when re-encoding seeds ──────────────────────────
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


DEFAULT_INPUT_DIR = Path("finbert_embedding/results")
DEFAULT_OUTPUT_DIR = Path("models/GRU/persona_scores")
DEFAULT_AXIS_PATH = Path("models/GRU/axis_vectors_auto_v2.npy")
DEFAULT_COMBINED_OUTPUT = DEFAULT_OUTPUT_DIR / "persona_scores_all_investors.csv"

INVESTOR_PROTOTYPE_POLES = {
    "risk_tolerance": {
        "high": ["INV_BARON", "INV_DRIEHAUS"],
        "low": ["INV_BUFFETT", "INV_HAWKINS"],
    },
    "time_horizon": {
        "high": ["INV_BUFFETT", "INV_YACKTMAN"],
        "low": ["INV_DRIEHAUS", "INV_GRANTHAM"],
    },
    "loss_aversion": {
        "high": ["INV_HAWKINS", "INV_YACKTMAN"],
        "low": ["INV_BARON", "INV_DRIEHAUS"],
    },
    "macro_sensitivity": {
        "high": ["INV_GRANTHAM"],
        "low": ["INV_BUFFETT", "INV_YACKTMAN"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SEED SENTENCES
# ═══════════════════════════════════════════════════════════════════════════════

AXIS_SEEDS = {

    # ── RISK TOLERANCE ─────────────────────────────────────────────────────────
    # High = aggressive, opportunistic deployment of capital in downturns
    # Low  = defensive posture, capital preservation, moving to cash
    "risk_tolerance": {
        "high": [
            # Opportunistic deployment
            "We aggressively increased our position during the market drawdown.",
            "We view periods of fear and uncertainty as exceptional buying opportunities.",
            "Our largest purchases came in the months when sentiment was most negative.",
            "We deployed capital at an accelerated pace as prices fell sharply.",
            "Volatility creates the very conditions under which great investments are made.",
            "We doubled our stake when the stock declined forty percent.",
            "The portfolio's largest new position was initiated at the depths of the selloff.",
            "When others are fearful, we lean in harder than at any other time.",
            "We added to every core holding during the correction, without exception.",
            "Market dislocations are precisely the moments we have been waiting for.",
            # Concentrated bets, high conviction
            "We concentrate the portfolio in our highest-conviction ideas regardless of index weight.",
            "Position sizing is driven by the magnitude of the opportunity, not by benchmark constraints.",
            "We are comfortable running a highly concentrated book when the opportunity set is compelling.",
            "Our ten largest positions represent the overwhelming majority of the fund's assets.",
            "We do not diversify away from our best ideas for the sake of managing short-term volatility.",
            # Leverage and bold action
            "We used the correction to deploy the last of our dry powder into equities.",
            "This year we acted decisively and at scale when the market gave us the chance.",
            "We entered the position at a size that reflected our full conviction.",
            "We have never been reluctant to make large bets when the odds are clearly in our favour.",
            "We increased gross exposure to its highest level since the fund's inception.",
        ],
        "low": [
            # Defensive and cautious
            "We moved to preserve capital and reduce equity exposure significantly this year.",
            "Protecting our investors' principal is our foremost obligation in this environment.",
            "We raised cash levels to their highest point in the fund's history.",
            "Given the elevated uncertainty, we chose to wait on the sidelines rather than act.",
            "Our priority this year was capital preservation over return maximisation.",
            "We trimmed our most cyclical positions and increased our fixed income allocation.",
            "The portfolio ended the year more defensively positioned than it began.",
            "We reduced gross exposure materially in response to deteriorating risk-reward.",
            "Caution was the defining characteristic of our positioning throughout this period.",
            "We elected to forgo potential upside in order to protect against downside scenarios.",
            # Moving to cash / safe assets
            "We allowed cash to accumulate rather than forcing capital into unattractive opportunities.",
            "A significant portion of the portfolio was held in short-duration treasuries by year end.",
            "We are content to hold cash and wait for a more attractive entry point.",
            "Deploying capital recklessly into a deteriorating environment is not consistent with our mandate.",
            "We reduced our net equity exposure to its lowest level in over a decade.",
            # Risk management language
            "Tail-risk hedges were the most meaningful contributor to protecting the portfolio this year.",
            "We purchased downside protection on our largest positions as a precaution.",
            "Scenario analysis around adverse outcomes drove our decision to de-risk the book.",
            "We sized positions conservatively to limit the impact of any single adverse event.",
            "Our risk management framework led us to reduce exposure well before the drawdown accelerated.",
        ],
    },

    # ── TIME HORIZON ───────────────────────────────────────────────────────────
    # High = multi-year / permanent ownership mindset
    # Low  = event-driven, near-term catalyst, short holding periods
    "time_horizon": {
        "high": [
            # Permanent / forever holding
            "Our favourite holding period is forever.",
            "We think in decades, not quarters.",
            "We have no intention of selling a business that has durable competitive advantages.",
            "Short-term price fluctuations are entirely irrelevant to our long-term investment thesis.",
            "We measure our success over rolling ten-year periods, not annual returns.",
            "We are patient owners; we do not manage to the quarter.",
            "The passage of time is an ally to a business with compounding economics.",
            "We are indifferent to what happens to the stock price over the next twelve months.",
            "Our ideal investment is one we never have to sell.",
            "We would rather own a wonderful business at a fair price for thirty years than trade it.",
            # Long-term compounding language
            "The compounding of intrinsic value over long periods is the core engine of our returns.",
            "We are willing to accept years of apparent underperformance in service of a multi-decade thesis.",
            "Patience is the most underrated competitive advantage available to long-term investors.",
            "We have owned several of our largest positions for more than a decade and expect to do so indefinitely.",
            "Time arbitrage — willingness to hold through near-term pain — is central to our edge.",
            # Ignoring short-term noise
            "We do not react to quarterly earnings misses in businesses with intact long-term prospects.",
            "Analyst price targets and twelve-month consensus views play no role in our decision-making.",
            "We are structurally indifferent to short-term mark-to-market fluctuations.",
            "The market's obsession with the next ninety days is precisely what creates our opportunity.",
            "We have never sold a position simply because it underperformed in a given year.",
        ],
        "low": [
            # Event-driven / near-term catalyst
            "We repositioned the portfolio to reflect near-term catalysts and expected re-ratings.",
            "Our thesis is event-driven with an expected resolution within the next twelve months.",
            "We exited the position after the catalyst we anticipated did not materialise on schedule.",
            "We rotated into positions with clearer near-term earnings visibility.",
            "The fund's average holding period was less than one year over this cycle.",
            "We trimmed positions ahead of the upcoming macro event and earnings announcement.",
            "Our investment horizon for this position was twelve to eighteen months from entry.",
            "We entered the trade expecting a re-rating once the corporate action completed.",
            "We closed the position after capturing the majority of the expected return.",
            "The position was sized for a short-term dislocation rather than a long-term hold.",
            # Active trading / tactical rotation
            "We turned over a significant portion of the portfolio in response to changing conditions.",
            "Tactical asset allocation adjustments were a meaningful driver of performance this year.",
            "We rotated between sectors multiple times as the macro backdrop evolved.",
            "The portfolio's positioning changed substantially from the beginning to the end of the year.",
            "We actively traded around core positions to improve our cost basis.",
            # Short-duration thinking
            "Our investment committee reviews position theses on a quarterly basis.",
            "We evaluate each holding against its expected return over the next six to twelve months.",
            "Positions that do not show progress toward our catalyst within one year are reviewed for exit.",
            "We set price targets with defined time horizons and exit when those targets are reached.",
            "Opportunity cost discipline requires us to recycle capital into fresher ideas regularly.",
        ],
    },

    # ── LOSS AVERSION ──────────────────────────────────────────────────────────
    # High = strong preference to avoid losses; asymmetric fear of downside
    # Low  = comfortable with volatility and drawdowns; symmetric view of outcomes
    "loss_aversion": {
        "high": [
            # Explicit loss-avoidance language
            "We will not risk what we have and need for what we do not have and do not need.",
            "Avoiding permanent loss of capital is the absolute cornerstone of our philosophy.",
            "Our first rule is never to lose money; our second rule is not to forget the first.",
            "Drawdown protection is more important to us than maximising upside participation.",
            "We are far more afraid of a permanent impairment than a temporary price decline.",
            "We would rather earn a lower return with certainty than reach for yield with additional risk.",
            "The asymmetry of losses — harder to recover than to lose — governs every sizing decision.",
            "We subject every investment to a thorough stress test before committing capital.",
            "Preservation of purchasing power over the long run takes precedence over short-term gains.",
            "We will not stretch on valuation when the margin of safety is inadequate.",
            # Margin of safety / downside first
            "We always ask what we can lose before asking what we can gain.",
            "Every position is underwritten by a margin of safety that protects against our being wrong.",
            "We spend more time analysing the downside scenario than the base or upside case.",
            "Asymmetric risk-reward means we need to be able to lose very little while making a great deal.",
            "The worst investment outcome is not underperformance; it is permanent capital destruction.",
            # Hedging and insurance
            "We maintain a meaningful allocation to instruments designed to protect against severe drawdowns.",
            "Insurance against catastrophic loss is not optional in our framework — it is foundational.",
            "We purchased puts on our most volatile positions to cap our downside exposure.",
            "Our risk budget is defined first by the maximum drawdown we are willing to accept.",
            "We sleep well at night because we have thought carefully about what can go wrong.",
        ],
        "low": [
            # Embrace of volatility
            "Volatility is our friend; we embrace it rather than fear it.",
            "A temporary decline in market value is not a loss — it is an opportunity.",
            "We are fully comfortable with short-term mark-to-market losses when our thesis remains intact.",
            "We do not hedge our core positions; we accept the full distribution of outcomes.",
            "Paper losses do not concern us; only permanent impairment of intrinsic value does.",
            "We are willing to sit through drawdowns of thirty to forty percent in our highest-conviction names.",
            "Short-term pain is the price of admission for the long-term returns we seek.",
            "Volatility and risk are fundamentally different concepts that the market conflates.",
            "We view a fifty percent decline in a position as an opportunity to double down, not exit.",
            "Our investors understand and accept that the path to exceptional returns is rarely smooth.",
            # No hedging, full exposure
            "We carry no explicit portfolio hedges; our protection comes from the quality of our businesses.",
            "We do not attempt to smooth the return stream; we are optimising for terminal wealth.",
            "Drawdowns are an inevitable and acceptable feature of our investment approach.",
            "We have never purchased portfolio insurance; we find it expensive and philosophically inconsistent.",
            "Accepting full upside and full downside is essential to earning equity-like returns.",
            # Confidence in recovery
            "Every drawdown in our portfolio's history has been followed by a recovery to new highs.",
            "We are indifferent to short-term losses because our conviction in the long-term thesis is total.",
            "The worst thing an investor can do is sell a great business because of a temporary price decline.",
            "We find it psychologically easy to hold through deep drawdowns when the fundamentals are intact.",
            "Short-term losses create no anxiety for us; permanent impairment is the only scenario we fear.",
        ],
    },

    # ── MACRO SENSITIVITY ─────────────────────────────────────────────────────
    # High = portfolio thesis explicitly driven by macro conditions / regime
    # Low  = purely bottom-up; ignores macro forecasts entirely
    "macro_sensitivity": {
        "high": [
            # Macro as primary organising framework
            "Our positioning this year was shaped primarily by the Federal Reserve's rate trajectory.",
            "We constructed the portfolio with the macroeconomic cycle as the primary organising framework.",
            "The inflationary environment fundamentally changed our sector allocations and factor tilts.",
            "We shifted our thesis materially in response to the deteriorating global growth outlook.",
            "Our factor tilts explicitly reflect our view on where we are in the credit cycle.",
            "Macro regime changes drove the most significant repositioning decisions of the year.",
            "We entered the year positioned for a soft landing and rotated as that thesis came into question.",
            "The path of interest rates was the single most important variable in our portfolio construction.",
            "Our sector weights are a direct expression of our view on the business cycle.",
            "We reduced duration aggressively when the inflation data made clear that rates would stay higher for longer.",
            # Explicit macro forecasting
            "Our macro team's outlook for global growth informed every major allocation decision.",
            "We modelled three macro scenarios — expansion, stagflation, and recession — and sized accordingly.",
            "The portfolio is explicitly positioned for the late-cycle environment we believe we are entering.",
            "We tilted toward defensive sectors and quality factors given our recessionary base case.",
            "Our commodity exposure was increased materially as our inflation outlook became more hawkish.",
            # Regime-aware positioning
            "We think about portfolio construction in terms of macro regimes rather than individual securities.",
            "When the yield curve inverted, we immediately began reducing cyclical exposure.",
            "Our allocation to financials is a function of our view on the net interest margin environment.",
            "We track the leading economic indicators weekly and adjust sector weights accordingly.",
            "The current monetary tightening cycle has been the dominant driver of our asset allocation.",
        ],
        "low": [
            # Pure bottom-up, ignoring macro
            "We do not attempt to predict macroeconomic conditions or time the business cycle.",
            "Our investment process is entirely bottom-up; macro factors do not drive our decisions.",
            "We ignore short-term macro noise and focus entirely on the fundamentals of the businesses we own.",
            "Whether GDP grows or contracts next year, our thesis is driven by company-specific dynamics.",
            "We pay no attention to macro forecasts; we focus solely on competitive advantage and valuation.",
            "Economic conditions are an input we acknowledge but do not attempt to trade around.",
            "We have never altered a position because of a change in the macro outlook.",
            "Our returns have nothing to do with getting the economy right and everything to do with getting businesses right.",
            "We find macro forecasting to be an unreliable basis for investment decisions.",
            "Interest rates, inflation, and GDP growth are variables we note but do not act upon.",
            # Dismissal of macro as a signal
            "Macro predictions are notoriously unreliable; we prefer to focus on what we can actually know.",
            "We have no view on where rates will be in twelve months and do not pretend otherwise.",
            "Our portfolio looks essentially the same regardless of the macro environment because we own great businesses.",
            "We do not rotate between sectors based on the economic cycle; we own quality wherever we find it.",
            "The businesses we own will compound intrinsic value regardless of short-term economic conditions.",
            # Stock-picker identity
            "We are stock pickers, full stop; the economy is someone else's problem.",
            "Our edge comes from understanding businesses deeply, not from macro timing.",
            "Sector weights in our portfolio are a residual of bottom-up stock selection, nothing more.",
            "We would rather own one extraordinary business in a difficult macro environment than ten mediocre ones.",
            "The macro backdrop has never been a primary input to our investment process and never will be.",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENCODE SEEDS AND BUILD AXIS VECTORS
# ═══════════════════════════════════════════════════════════════════════════════

def load_finbert():
    """Load ProsusAI/FinBERT tokenizer and model."""
    if not TORCH_AVAILABLE:
        raise ImportError("torch and transformers are required to encode seeds. "
                          "Install with: pip install torch transformers")
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModel.from_pretrained("ProsusAI/finbert")
    model.eval()
    return tokenizer, model


def encode_sentences(sentences, tokenizer, model):
    """Return CLS embeddings for a list of sentences, shape (n, 768)."""
    embeddings = []
    with torch.no_grad():
        for sent in sentences:
            inputs = tokenizer(
                sent, return_tensors="pt",
                truncation=True, max_length=512, padding=True
            )
            outputs = model(**inputs)
            cls_emb = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            embeddings.append(cls_emb)
    return np.array(embeddings)   # (n, 768)


def build_axis_vectors(axis_seeds, tokenizer, model):
    """
    For each axis, compute the normalised direction vector:
        direction = mean(high_embeddings) - mean(low_embeddings),  L2-normalised
    Returns dict {axis_name: np.array(768,)}
    """
    axis_vectors = {}
    for axis, poles in axis_seeds.items():
        print(f"  Encoding axis: {axis} ...")
        high_embs = encode_sentences(poles["high"], tokenizer, model)
        low_embs  = encode_sentences(poles["low"],  tokenizer, model)
        direction = high_embs.mean(axis=0) - low_embs.mean(axis=0)
        direction = direction / np.linalg.norm(direction)
        axis_vectors[axis] = direction
        print(f"    high seeds: {len(poles['high'])}  |  low seeds: {len(poles['low'])}")
    return axis_vectors


def build_axis_vectors_from_investor_prototypes(df, prototype_poles=None):
    """
    Build axis vectors directly from the six investor embedding files.

    This is a practical fallback when the environment cannot re-encode seed
    sentences with FinBERT. It contrasts mean document embeddings for investors
    chosen as high/low prototypes for each axis.
    """
    prototype_poles = prototype_poles or INVESTOR_PROTOTYPE_POLES
    if "investor_id" not in df.columns:
        raise ValueError("investor_id column is required for investor_prototype axes.")

    dim_cols = embedding_columns(df)
    work = df[["investor_id"] + dim_cols].dropna(subset=["investor_id"]).copy()
    investor_means = work.groupby("investor_id")[dim_cols].mean()

    axis_vectors = {}
    available = set(investor_means.index)
    for axis, poles in prototype_poles.items():
        high = [inv for inv in poles["high"] if inv in available]
        low = [inv for inv in poles["low"] if inv in available]
        if not high or not low:
            raise ValueError(
                f"Cannot build {axis}: high={high}, low={low}, "
                f"available={sorted(available)}"
            )
        high_vec = investor_means.loc[high].mean(axis=0).to_numpy(dtype=np.float32)
        low_vec = investor_means.loc[low].mean(axis=0).to_numpy(dtype=np.float32)
        direction = high_vec - low_vec
        direction = direction / max(np.linalg.norm(direction), 1e-12)
        axis_vectors[axis] = direction
        print(f"  Prototype axis {axis}: high={high} | low={low}")

    return axis_vectors


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SCORE LETTER EMBEDDINGS
# ═══════════════════════════════════════════════════════════════════════════════

def embedding_columns(df, dim_prefix="dim_"):
    """Return embedding columns sorted by numeric dimension index."""
    dim_cols = [c for c in df.columns if c.startswith(dim_prefix)]
    if not dim_cols:
        raise ValueError(f"No columns starting with '{dim_prefix}' found in dataframe.")

    def dim_index(col):
        suffix = col[len(dim_prefix):]
        return int(suffix) if suffix.isdigit() else 10**9

    return sorted(dim_cols, key=dim_index)


def score_embeddings(df, axis_vectors, dim_prefix="dim_"):
    """
    Add one persona_<axis> column per axis to df.
    Persona score = sigmoid(embedding · axis_direction)
    """
    dim_cols = embedding_columns(df, dim_prefix=dim_prefix)

    embeddings = df[dim_cols].values.astype(np.float32)   # (n_rows, 768)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.maximum(norms, 1e-12)

    for axis, vec in axis_vectors.items():
        vec = vec.astype(np.float32)
        vec = vec / max(np.linalg.norm(vec), 1e-12)
        dot_products = embeddings @ vec                    # (n_rows,)
        df[f"persona_{axis}"] = expit(dot_products)

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SANITY CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def sanity_check(df):
    """
    Print per-year persona scores for a quick gut-check.
    Expectation: crisis years (2008, 2020) → lower risk_tolerance, higher loss_aversion
    compared to bull years (2013, 2017, 2019).
    """
    persona_cols = [c for c in df.columns if c.startswith("persona_")]
    if not persona_cols:
        print("No persona columns found — run score_embeddings() first.")
        return

    if "period_type" not in df.columns or "year" not in df.columns:
        print("Skipping sanity check: expected period_type/year columns are missing.")
        return

    # Use only annual rows to avoid double-counting when available.
    subset = df[df["period_type"] == "year"].copy()
    if subset.empty:
        subset = df.copy()
    print("\n── Persona Scores by Year (annual rows only) ──────────────────────")
    display_cols = [c for c in ["investor_id", "year", "period_type"] if c in subset.columns]
    print(subset[display_cols + persona_cols].sort_values(display_cols).to_string(index=False))

    # Highlight crisis vs bull years if available
    crisis_years = [y for y in [2008, 2020] if y in subset["year"].values]
    bull_years   = [y for y in [2013, 2017, 2019] if y in subset["year"].values]

    if crisis_years and bull_years:
        print("\n── Crisis years (expected: lower risk_tolerance, higher loss_aversion) ──")
        print(subset[subset["year"].isin(crisis_years)][["year"] + persona_cols].to_string(index=False))
        print("\n── Bull years ──────────────────────────────────────────────────────────")
        print(subset[subset["year"].isin(bull_years)][["year"] + persona_cols].to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def read_embedding_files(input_files):
    frames = []
    for path in input_files:
        frame = pd.read_csv(path)
        frame["embedding_source_file"] = Path(path).name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def load_or_build_axis_vectors(
    axes_npy=None,
    reload_axes=False,
    axis_method="auto",
    reference_df=None,
):
    """Load cached axis vectors or encode seed sentences and cache them."""
    axes_path = Path(axes_npy) if axes_npy else None
    axis_vectors = None

    if axes_path and axes_path.exists() and not reload_axes:
        print(f"Loading pre-built axis vectors from: {axes_path}")
        axis_vectors = np.load(axes_path, allow_pickle=True).item()
        print(f"  Axes loaded: {list(axis_vectors.keys())}")

    if axis_vectors is None:
        if axis_method in ("seed", "seeds", "auto"):
            try:
                print("Encoding seed sentences with FinBERT ...")
                tokenizer, model = load_finbert()
                axis_vectors = build_axis_vectors(AXIS_SEEDS, tokenizer, model)
            except Exception as exc:
                if axis_method in ("seed", "seeds"):
                    raise
                print("\nSeed-sentence axis build failed; falling back to investor prototypes.")
                print(f"  Reason: {type(exc).__name__}: {exc}")

        if axis_vectors is None:
            if reference_df is None:
                raise ValueError(
                    "reference_df is required for investor_prototype axis method."
                )
            print("Building axis vectors from investor prototype embeddings ...")
            axis_vectors = build_axis_vectors_from_investor_prototypes(reference_df)

        if axes_path:
            axes_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(axes_path, axis_vectors)
            print(f"  Axis vectors saved to: {axes_path}")

    return axis_vectors


def score_file(input_csv, output_csv, axis_vectors):
    """Score one embedding CSV and save it."""
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)

    # ── Load embedding CSV ───────────────────────────────────────────────────
    print(f"Loading embeddings from: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"  Shape: {df.shape}")

    # ── Score embeddings ─────────────────────────────────────────────────────
    print("Scoring letter embeddings ...")
    df = score_embeddings(df, axis_vectors)
    persona_cols = [c for c in df.columns if c.startswith("persona_")]
    print(f"  Persona columns added: {persona_cols}")
    preview_cols = [c for c in ["investor_id", "timestamp", "year", "period_type"] if c in df.columns]
    print(df[preview_cols + persona_cols].head(10).to_string(index=False))

    # ── Sanity check ─────────────────────────────────────────────────────────
    sanity_check(df)

    # ── Save output ──────────────────────────────────────────────────────────
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"\nSaved enriched CSV to: {output_csv}")
    return df


def discover_input_files(input_dir, pattern="finbert_embeddings_*.csv"):
    input_dir = Path(input_dir)
    files = sorted(input_dir.glob(pattern))
    files = [p for p in files if not p.name.endswith("_with_persona.csv")]
    if not files:
        raise FileNotFoundError(f"No input files found in {input_dir} matching {pattern}")
    return files


def output_path_for(input_csv, output_dir):
    stem = Path(input_csv).stem
    return Path(output_dir) / f"{stem}_with_persona.csv"


def main(
    input_csv=None,
    output_csv=None,
    input_dir=DEFAULT_INPUT_DIR,
    output_dir=DEFAULT_OUTPUT_DIR,
    combined_output=DEFAULT_COMBINED_OUTPUT,
    axes_npy=DEFAULT_AXIS_PATH,
    reload_axes=False,
    pattern="finbert_embeddings_*.csv",
    axis_method="auto",
):
    if input_csv:
        reference_df = pd.read_csv(input_csv)
        axis_vectors = load_or_build_axis_vectors(
            axes_npy=axes_npy,
            reload_axes=reload_axes,
            axis_method=axis_method,
            reference_df=reference_df,
        )
        out = output_csv or output_path_for(input_csv, output_dir)
        df = score_file(input_csv, out, axis_vectors)
        if combined_output:
            combined_output = Path(combined_output)
            combined_output.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(combined_output, index=False)
            print(f"Saved combined CSV to: {combined_output}")
        return

    input_files = discover_input_files(input_dir, pattern=pattern)
    print(f"\nDiscovered {len(input_files)} embedding files:")
    for path in input_files:
        print(f"  - {path}")

    reference_df = read_embedding_files(input_files)
    axis_vectors = load_or_build_axis_vectors(
        axes_npy=axes_npy,
        reload_axes=reload_axes,
        axis_method=axis_method,
        reference_df=reference_df,
    )

    scored = []
    for path in input_files:
        out = output_path_for(path, output_dir)
        scored.append(score_file(path, out, axis_vectors))

    combined = pd.concat(scored, ignore_index=True)
    if combined_output:
        combined_output = Path(combined_output)
        combined_output.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(combined_output, index=False)
        print(f"\nSaved combined persona score CSV to: {combined_output}")

    persona_cols = [c for c in combined.columns if c.startswith("persona_")]
    print("\n── Combined Summary by Investor ─────────────────────────────────")
    summary = combined.groupby("investor_id")[persona_cols].mean().round(4)
    print(summary.to_string())


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinBERT Persona Axis Extraction")
    parser.add_argument(
        "--input",
        default=None,
        help="Optional single input CSV. If omitted, all files in --input_dir are processed.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output CSV for --input mode.",
    )
    parser.add_argument(
        "--input_dir",
        default=str(DEFAULT_INPUT_DIR),
        help="Directory containing finbert_embeddings_*.csv files.",
    )
    parser.add_argument(
        "--output_dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for per-investor persona score CSVs.",
    )
    parser.add_argument(
        "--combined_output",
        default=str(DEFAULT_COMBINED_OUTPUT),
        help="Path for combined all-investor persona score CSV.",
    )
    parser.add_argument(
        "--pattern",
        default="finbert_embeddings_*.csv",
        help="Glob pattern for batch input mode.",
    )
    parser.add_argument(
        "--save_axes",
        default=str(DEFAULT_AXIS_PATH),
        help="Path to save or load axis direction vectors (.npy).",
    )
    parser.add_argument(
        "--axis_method",
        choices=["auto", "seed", "seeds", "investor_prototype"],
        default="auto",
        help=(
            "Axis construction method. auto tries FinBERT seed sentences, then "
            "falls back to investor prototype embeddings if the local environment "
            "cannot load FinBERT."
        ),
    )
    parser.add_argument(
        "--reload_axes",
        action="store_true",
        help="Force re-encoding of seed sentences even if .npy exists.",
    )
    args = parser.parse_args()

    main(
        input_csv=args.input,
        output_csv=args.output,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        combined_output=args.combined_output,
        axes_npy=args.save_axes,
        reload_axes=args.reload_axes,
        pattern=args.pattern,
        axis_method=args.axis_method,
    )
