# PLS Persona-to-Factor Mapping Model

## Purpose

The PLS model maps investor persona scores into Fama-French factor exposures. It is the final modeling bridge in the project:

```text
FinBERT text embeddings
-> persona scores
-> GRU macro-dynamic persona scores
-> PLS factor mapping
-> ideal factor exposures / investment recommendation
```

The model answers:

```text
Given a risk/persona profile and a macro state,
what Fama-French factor exposure does that profile imply?
```

## Script

The pipeline is implemented in:

```text
models/PLS/persona_factor_pls.py
```

Run:

```bash
python models/PLS/persona_factor_pls.py
```

By default, it uses GRU macro-dynamic persona scores. For a robustness comparison using raw observed text persona scores:

```bash
python models/PLS/persona_factor_pls.py --persona_mode observed
```

## Inputs

The script reads:

```text
models/GRU/macro_dynamic_outputs/gru_predictions.csv
models/GRU/macro_dynamic_outputs/quarterly_persona_macro.csv
famafrench_factor_regression/data/Fama-French Factor Regression (2).xlsx
```

The input features are:

```text
persona_risk_tolerance
persona_time_horizon
persona_loss_aversion
persona_macro_sensitivity
inflation
cycle
unemployment
monetary
stress
macro state dummy variables
```

The target variables are:

```text
Mkt-RF
SMB
HML
RMW
CMA
Alpha
```

Investor identity is not used as a feature. This is intentional: the final recommendation model should be able to accept a new user's persona profile, not only memorize famous investors.

## Why PLS?

PLS, or Partial Least Squares regression, is useful here because:

```text
1. The dataset is not very large.
2. Persona and macro variables can be correlated.
3. The output has multiple related targets.
4. The coefficients are more interpretable than a neural network.
```

In plain English, PLS looks for a small number of hidden directions in the persona/macro data that best explain differences in factor exposures.

The current default uses:

```text
n_components = 3
```

## Outputs

The script writes:

```text
models/PLS/factor_mapping_outputs/
```

Important files:

```text
pls_mapping_dataset.csv
pls_factor_predictions.csv
pls_metrics.csv
pls_coefficients.csv
ideal_factor_exposures_by_profile.csv
```

`pls_mapping_dataset.csv` is the joined modeling dataset.

`pls_factor_predictions.csv` contains observed and predicted factor exposures.

`pls_metrics.csv` contains RMSE, MAE, and R2 for train and test samples.

`pls_coefficients.csv` shows how persona and macro variables map to each factor.

`ideal_factor_exposures_by_profile.csv` gives example factor recommendations for profile types:

```text
Conservative
Balanced
Aggressive
Macro-Sensitive
```

across each macro state.

## Current Result Interpretation

The current test R2 scores are:

```text
HML     0.362
CMA     0.283
Alpha   0.093
SMB     0.072
Mkt-RF  0.051
RMW    -0.173
```

This means the model is learning some signal for value/conservative-style exposures, especially:

```text
HML = value factor
CMA = conservative investment factor
```

But it is weak for:

```text
Mkt-RF = broad market exposure
SMB = size exposure
RMW = profitability exposure
```

A negative R2 for RMW means the test prediction is worse than simply predicting the average RMW exposure.

## How to Evaluate This

The current result is acceptable as a prototype, but not strong enough to claim high predictive accuracy.

The best interpretation is:

```text
The model shows that text-derived persona and macro states contain some information about portfolio factor style,
especially value/conservative exposure, but the current data is too small/noisy for a strong predictive recommender.
```

This is still useful for the project because the goal is to demonstrate the pipeline and mapping logic:

```text
language -> persona -> macro-conditioned persona -> factor exposure
```

For a final presentation, the strongest evidence is:

```text
1. Directional coefficient interpretation
2. Macro-state profile heatmaps
3. Predicted ideal factor exposures by risk profile
4. Honest model metrics showing this is a prototype
```

## Coefficient Interpretation

Current persona coefficients suggest:

```text
higher risk tolerance
-> higher Mkt-RF and SMB
-> lower HML and CMA
```

In plain English:

```text
More aggressive investors are mapped toward higher market and smaller-company exposure,
and away from value/conservative factor exposure.
```

Higher loss aversion and longer time horizon both lean more toward:

```text
HML
CMA
```

In plain English:

```text
More defensive or patient investors are mapped toward value and conservative investment styles.
```

That interpretation is financially reasonable, even though the predictive R2 is modest.

## Recommendation for Final Use

Use the PLS output as a recommendation prototype, not as a production trading model.

For the final project, present:

```text
main model: macro_dynamic_persona_* -> Fama-French factors
robustness check: observed_persona_* -> Fama-French factors
```

Then explain that the current model is strongest for identifying broad factor style, not exact quarterly factor loadings.
