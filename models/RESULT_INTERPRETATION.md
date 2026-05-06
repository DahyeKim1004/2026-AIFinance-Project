# Persona-GRU-PLS Result Interpretation

## 1. Why the persona axis construction was changed

The earlier persona axis setup used investor prototypes as a fallback:

```text
assumed high/low investor labels
-> investor mean embeddings
-> persona axis vectors
-> persona scores for the same investors
```

This was methodologically problematic because it made the measurement partly circular. For example, if Baron and Driehaus were assigned as high risk-tolerance prototypes, and Buffett and Hawkins were assigned as low risk-tolerance prototypes, then the risk-tolerance axis was already defined using the investors whose personalities we were trying to infer.

That means the resulting persona score was not purely inferred from text. It partially reflected the prior rule used to label investors.

The corrected setup is:

```text
seed sentences
-> FinBERT embeddings of high/low semantic poles
-> persona axis vectors
-> investor text scored against those axes
```

This is more defensible because the axis is defined from external semantic descriptions rather than from investor identity assumptions.

The current file `models/GRU/persona_axis_extraction.py` now uses only seed-sentence axes. The old investor-prototype fallback and `axis_method` switch were removed so the script cannot silently return to the circular method. The new axis cache is:

```text
models/GRU/axis_vectors_seed.npy
```

The old prototype-derived cache was:

```text
models/GRU/axis_vectors_auto_v2.npy
```

and should not be used.

## 2. What the observed persona scores mean

After the correction, the observed persona scores should be interpreted as text-derived revealed persona scores:

```text
observed persona = FinBERT text embedding projected onto seed-defined behavioral axes
```

They are not direct psychological ground truth. They are semantic scores extracted from investor letters or reports. Still, they are no longer mechanically defined by investor labels, which makes them suitable as a text-based measurement layer.

The four observed persona dimensions are:

```text
persona_risk_tolerance
persona_time_horizon
persona_loss_aversion
persona_macro_sensitivity
```

These scores are saved in:

```text
models/GRU/persona_scores/persona_scores_all_investors.csv
```

## 3. What the GRU actually learns

The GRU should not be interpreted as learning true latent dynamic risk attitude.

The original hope was:

```text
macro history -> true dynamic investor personality
```

But the actual training target is the observed text-derived persona score. Therefore the GRU learns something closer to:

```text
E[observed persona | recent macro sequence, investor identity]
```

or, in words:

```text
the macro-conditioned expected component of observed textual persona
```

This is important. The GRU output is a smoothed macro-conditioned estimate, not a direct estimate of the investor's true latent risk attitude.

The output columns in `gru_predictions.csv` should be interpreted as:

```text
observed_persona_*
    The seed-based text persona score after quarterly aggregation.

macro_dynamic_persona_*
    The GRU-smoothed persona component predicted from recent macro state and investor identity.

residual_persona_*
    The text persona component not explained by the macro-conditioned GRU estimate.
```

So the model is better described as decomposing observed persona into:

```text
observed persona = macro-conditioned component + residual text-specific component
```

## 4. Why the GRU plots now align more closely

After rebuilding persona scores from seed-defined axes and retraining the GRU, the observed and macro-dynamic trajectories align much more closely.

The approximate observed vs dynamic correlations were:

```text
risk_tolerance      0.82
time_horizon        0.96
loss_aversion       0.74
macro_sensitivity   0.82
```

This is visually clear in the investor trajectory plots: the observed and GRU dynamic lines sit close together.

This is partly good: the GRU is fitting the observed target better under the corrected measurement setup.

But it also needs a cautious interpretation. Because the seed-based persona scores occupy a relatively narrow range, the GRU can produce a smooth conditional trajectory that tracks the observed score closely without necessarily discovering a deep latent attitude process.

In short:

```text
better alignment = better conditional smoothing of observed persona
not necessarily proof of true latent personality discovery
```

## 5. Why the macro-state heatmap looked almost uniform

The original heatmap appeared almost the same color across macro states because the plotting scale was fixed from 0 to 1:

```text
vmin = 0
vmax = 1
```

But the actual macro-state differences in average persona scores were very small, usually around:

```text
0.001 to 0.003
```

So on a 0-to-1 color scale, the heatmap naturally looked flat.

This does not necessarily mean the code was wrong. It means the average persona differences by macro state are weak.

The heatmap code was adjusted to show:

```text
macro_state_persona_heatmap.png
    Absolute macro-state persona means with a local color scale.

macro_state_persona_delta_heatmap.png
    Macro-state deviations from the overall mean.
```

The delta heatmap is more informative for interpretation. The current pattern is small but roughly:

```text
Expansion:
    slightly higher macro_sensitivity
    slightly lower time_horizon

Recession:
    slightly higher time_horizon
    slightly lower macro_sensitivity

Neutral:
    slightly higher loss_aversion
```

However, these are very small effects. The main conclusion is:

```text
macro state explains only a weak average shift in persona scores
```

## 6. PLS dynamic vs observed results

The PLS mapping can be run in two modes:

```text
--persona_mode dynamic
    Uses macro_dynamic_persona_* from gru_predictions.csv.

--persona_mode observed
    Uses observed_persona_* from gru_predictions.csv.
```

Both modes still read from:

```text
models/GRU/macro_dynamic_outputs/gru_predictions.csv
```

The difference is only which persona columns are selected.

Observed mode uses the text-derived persona scores:

```text
observed_persona_risk_tolerance
observed_persona_time_horizon
observed_persona_loss_aversion
observed_persona_macro_sensitivity
```

Dynamic mode uses the GRU-smoothed macro-conditioned scores:

```text
macro_dynamic_persona_risk_tolerance
macro_dynamic_persona_time_horizon
macro_dynamic_persona_loss_aversion
macro_dynamic_persona_macro_sensitivity
```

The output folders should be kept separate:

```text
models/PLS/factor_mapping_outputs_dynamic
models/PLS/factor_mapping_outputs_observed
```

Otherwise one mode can overwrite the other.

## 7. Which PLS mode performed better

Comparing the metrics files:

```text
models/PLS/factor_mapping_outputs_dynamic/pls_metrics.csv
models/PLS/factor_mapping_outputs_observed/pls_metrics.csv
```

the observed mode performed slightly better on the test split.

Average test metrics:

```text
dynamic:
    RMSE 0.1620
    MAE  0.1388
    R2   0.1597

observed:
    RMSE 0.1587
    MAE  0.1325
    R2   0.1803
```

Factor-level test comparison:

```text
Observed better:
    Alpha
    CMA
    HML
    RMW

Dynamic better:
    Mkt-RF
    SMB
```

The largest visible improvement for observed mode was in HML:

```text
HML dynamic:
    RMSE 0.3490
    R2   0.4140

HML observed:
    RMSE 0.3293
    R2   0.4783
```

## 8. Interpretation of the PLS comparison

The observed mode performing better suggests that factor exposures are explained more by the revealed text persona signal than by the GRU-smoothed macro-conditioned component.

This makes intuitive sense. The GRU smooths persona scores according to macro history and investor identity. That can reduce noise, but it can also remove idiosyncratic text-specific information that matters for factor exposures.

So the result should not be framed as:

```text
GRU discovered true dynamic personality and PLS maps that to factors.
```

A better framing is:

```text
Observed text persona contains factor-relevant information.
The GRU extracts the macro-conditioned smooth component of persona.
The smoothed macro-dynamic component is useful, but less predictive than the raw observed text persona in the current PLS mapping.
```

This is not a failure. It is a substantive result:

```text
macro-conditioned persona explains part of investor behavior,
but factor exposures retain information from document-specific or investor-specific textual signals beyond macro state.
```

## 9. Recommended wording for the project

Use this wording:

```text
We construct seed-defined text persona scores using FinBERT embeddings.
The GRU estimates the macro-conditioned component of these observed persona scores.
The residual captures text-persona variation not explained by macro conditions.
PLS results show that observed textual persona has slightly stronger factor-exposure mapping performance than the macro-smoothed dynamic persona.
```

Avoid this wording:

```text
The GRU learns the true dynamic risk attitude of investors.
```

That claim is too strong for the current model design.

## 10. Current best interpretation

The clean interpretation of the pipeline is:

```text
Seed sentences define behavioral axes.
Investor text is scored against those axes to produce observed persona.
The GRU smooths observed persona into a macro-conditioned persona component.
PLS maps persona and macro features to Fama-French factor exposures.
Observed persona currently provides slightly better predictive mapping than GRU-smoothed persona.
```

The most defensible conclusion is:

```text
Investor letters contain factor-relevant persona signals.
Macro conditions explain some smooth movement in those persona signals,
but they do not fully determine the factor-relevant variation.
```

