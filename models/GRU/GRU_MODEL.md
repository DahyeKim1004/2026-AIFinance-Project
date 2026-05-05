# GRU Macro-Dynamic Persona Model

## Purpose

The GRU model creates a macro-conditioned investor persona score. It is not meant to replace the FinBERT text persona score. Instead, it learns how each investor's persona tends to move under different macroeconomic states.

The resulting score is used as the input to the next stage:

```text
FinBERT persona score
-> GRU macro-dynamic persona score
-> PLS mapping to Fama-French factor exposure
-> ideal factor / investment recommendation
```

## Inputs

The GRU pipeline is implemented in:

```text
models/GRU/macro_dynamic_persona_gru.py
```

It reads:

```text
models/GRU/persona_scores/persona_scores_all_investors.csv
macro_data_processed/processed_v2.xlsx
```

The persona CSV contains document-level persona scores:

```text
persona_risk_tolerance
persona_time_horizon
persona_loss_aversion
persona_macro_sensitivity
```

The raw FinBERT embedding columns, `dim_0` through `dim_767`, are dropped before GRU training. They are used only to derive persona scores, not as model features.

The macro file contributes quarterly macro state variables:

```text
inflation
cycle
unemployment
monetary
stress
macro_state_label
```

## Handling Multiple Documents Per Time Period

The raw text data does not have exactly one document per investor-quarter. Some sources are annual, some half-year, and some quarterly. The GRU pipeline converts all documents into an investor-quarter panel.

Each document is expanded into the quarters it covers:

```text
quarter document -> that quarter only
half-year document -> Q1/Q2 or Q3/Q4
annual document -> Q1/Q2/Q3/Q4
```

When multiple documents map to the same investor-quarter, persona scores are averaged with source weights:

```text
quarter source weight = 1.00
half-year source weight = 0.75
annual source weight = 0.45
```

The final weight is also scaled by `log1p(word_count)`, so longer documents matter more without letting very long letters dominate the panel.

This is better than duplicating annual letters equally because quarter-specific documents should carry more information about that quarter than broad annual letters.

## Training Dataset

The GRU is trained on one pooled dataset across all investors.

Each training example is:

```text
previous 8 quarters of macro features + investor identity
-> persona score at the current quarter
```

The input sequence includes:

```text
inflation
cycle
unemployment
monetary
stress
macro state dummy variables
investor dummy variables
```

The target is the four-dimensional persona vector:

```text
persona_risk_tolerance
persona_time_horizon
persona_loss_aversion
persona_macro_sensitivity
```

The model trains across all investors together, but investor dummy variables allow it to learn different baseline personalities for Buffett, Grantham, Baron, Hawkins, Driehaus, and Yacktman.

## Model Architecture

The model is a small GRU:

```text
GRU(input features, hidden_size=32)
-> LayerNorm
-> Linear layer
-> Sigmoid
```

The sigmoid keeps all output persona scores on a 0-1 scale.

Default training settings:

```text
sequence_length = 8 quarters
epochs = 250
batch_size = 32
learning_rate = 0.01
loss = mean squared error
```

The split is chronological within each investor. The last 20 percent of each investor's sequences are used as test data.

## Outputs

The GRU writes outputs to:

```text
models/GRU/macro_dynamic_outputs/
```

Important files:

```text
quarterly_persona_macro.csv
gru_predictions.csv
gru_training_history.csv
gru_model.pt
```

`quarterly_persona_macro.csv` is the clean investor-quarter table after document aggregation and macro-state joining.

`gru_predictions.csv` contains:

```text
observed_persona_*
macro_dynamic_persona_*
residual_persona_*
```

Interpretation:

```text
observed_persona_* = FinBERT-derived text persona
macro_dynamic_persona_* = persona expected under the recent macro sequence
residual_persona_* = investor-specific text signal not explained by macro conditions
```

## Link to Fama-French Mapping

The next pipeline is:

```text
models/PLS/persona_factor_pls.py
```

That script maps:

```text
macro_dynamic_persona scores + macro state
-> Fama-French factor exposures
```

The PLS stage uses the GRU output because the project question is conditional on macro regime: the same risk attitude can imply different factor exposures in different macro states.

For robustness, the PLS script can also be run with observed text persona scores:

```bash
python models/PLS/persona_factor_pls.py --persona_mode observed
```

The main project result should use:

```bash
python models/PLS/persona_factor_pls.py --persona_mode dynamic
```
