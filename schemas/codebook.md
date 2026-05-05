# InvestorDNA Codebook

> **Version:** 1.1  
> **Last Updated:** 2026-05-05  
> **Maintained by:** Role 4 (Model Architecture & Data Schema)  
> **Status:** Current working schema for the raw text corpus, FinBERT embeddings, and unified model inputs.

This codebook defines the column names, data types, allowed values, and formatting rules shared across the project. Role 1 handed off the raw text corpus under `TextData-Processing/data/raw/`; Role 4 owns text cleaning, FinBERT embedding, schema management, and model-ready exports.

---

## 1. Investor Registry

Canonical investor metadata should be exported as `TextData-Processing/data/investors.csv` or `data/processed/investors.csv`.

| Column | Type | Example | Description |
|---|---|---|---|
| `investor_id` | `string` (PK) | `INV_BUFFETT` | Investor identifier: `INV_` + uppercase surname. |
| `name` | `string` | `Warren Buffett` | Investor full name. |
| `firm` | `string` | `Berkshire Hathaway` | Firm or reporting entity associated with the text/13F data. |
| `cik` | `integer` | `1067983` | SEC EDGAR CIK used by Role 2/3 where applicable. |
| `category` | `string` | `Quality Compounder Value` | Investor style category. |
| `style_short` | `string` | `quality_value` | Snake-case style label for code. |
| `thirteen_f_start` | `integer` | `1998` | First usable 13F year. |
| `text_source_primary` | `string` | `annual_letter` | Primary source type; see §8. |
| `text_source_url` | `string` | `https://...` | Primary source URL. |
| `recognition_score` | `integer` | `5` | 1-5 public recognition score. |
| `etf_mapping` | `string` | `MOAT;QUAL;VLUE` | Semicolon-separated ETF mappings. |

### Active Investor Set

The current raw text corpus contains **6 active investors** and **519 files**. `INV_EINHORN` is excluded from the current model-ready corpus because the collected files were not suitable recurring LP letters.

| investor_id | Investor | Firm / Entity | Native Text Cadence | Current Raw Files |
|---|---|---|---|---:|
| `INV_BUFFETT` | Warren Buffett | Berkshire Hathaway | Annual | 48 |
| `INV_HAWKINS` | Mason Hawkins | Southeastern / Longleaf | Semiannual through 2021, quarterly from 2022-Q4 | 125 |
| `INV_GRANTHAM` | Jeremy Grantham | GMO | Quarterly plus signature essays | 77 |
| `INV_DRIEHAUS` | Richard Driehaus | Driehaus Mutual Funds | Semiannual EDGAR reports | 65 |
| `INV_BARON` | Ron Baron | Baron Funds | Semiannual EDGAR reports | 75 |
| `INV_YACKTMAN` | Don Yacktman | Yacktman / AMG Funds | Semiannual EDGAR reports | 129 |

---

## 2. Raw Text Corpus

Raw files are stored under:

```text
TextData-Processing/data/raw/{investor_slug}/{Investor}_{YY}[_Qn|_S1][_NN|_tag].{ext}
```

Supported raw file extensions:

| Extension | Count | Source Pattern | Processing Requirement |
|---|---:|---|---|
| `.pdf` | 161 | Company/site PDFs: Buffett, Grantham, Hawkins | PDF text extraction. |
| `.html` | 21 | Berkshire site letters | HTML visible-text extraction. |
| `.htm` | 244 | EDGAR HTML/iXBRL reports | DOM/iXBRL stripping and section slicing. |
| `.txt` | 93 | EDGAR TXT/SGML reports | `<TEXT>` block extraction and section slicing. |

### Raw Filename Periods

Raw filenames preserve each document's native cadence before quarterly carry-forward.

| Pattern | Example | Native Period Output | Meaning |
|---|---|---|---|
| `{Investor}_{YY}` | `Buffett_15.pdf` | `2015` | Annual document. |
| `{Investor}_{YY}_S1` | `Hawkins_22_S1.htm` | `2022-H1` | Semiannual / first-half document. |
| `{Investor}_{YY}_Qn` | `Grantham_19_Q1.pdf` | `2019-Q1` | Quarterly document. |
| `{Investor}_{YY}_Qn_NN` | `Hawkins_24_Q2_01.pdf` | `2024-Q2` | Multiple files in one quarterly bucket. |
| `{Investor}_{YY}_S1_NN` | `Baron_03_S1_02.txt` | `2003-H1` | Multiple files in one semiannual bucket. |
| `{Investor}_{YY}_{tag}` | `Grantham_20_lastdance.pdf` | `2020` plus tag | Signature essay or nonstandard label; mapper may assign quarter. |

---

## 3. Cleaned Text Corpus (`investor_text.csv`)

Role 4 produces this cleaned text corpus from the Role 1 raw-data handoff. This file is the preferred input to embedding extraction once it exists; direct raw-file embedding is a fallback for diagnostics or early iteration.

| Column | Type | Example | Description |
|---|---|---|---|
| `investor_id` | `string` (FK) | `INV_GRANTHAM` | Investor identifier. |
| `timestamp` | `string` | `2019-Q1` | Native document period: `YYYY`, `YYYY-H1`, `YYYY-H2`, or `YYYY-Qn`. |
| `Date` | `string` | `1Q19` | Quarterly model key after cadence alignment. |
| `year` | `integer` | `2019` | Four-digit year. |
| `quarter` | `integer` / empty | `1` | Quarter number when native period is quarterly or after alignment. |
| `half` | `integer` / empty | `1` | Half-year number when native period is semiannual. |
| `period_type` | `string` | `quarter` | One of `year`, `half`, `quarter`, `unknown`. |
| `source_type` | `string` | `signature_essay` | Controlled vocabulary; see §8. |
| `chunk_id` | `integer` | `1` | Sequence within the same `investor_id` + `Date`. |
| `text_content` | `string` | `"Most investors believe..."` | Cleaned narrative text. |
| `word_count` | `integer` | `3542` | Word count for `text_content`. |
| `filename` | `string` | `Grantham_19_Q1.pdf` | Raw source filename. |
| `source_ext` | `string` | `pdf` | Raw source extension without dot. |
| `source_url` | `string` / empty | `https://...` | Original URL when available. |
| `processing_status` | `string` | `ok` | `ok`, `skipped_empty`, `skipped_noise`, `error`. |

### Cadence Alignment Policy

`timestamp` preserves native document cadence. `Date` is the quarterly model key.

| Native Period | Alignment |
|---|---|
| Annual (`YYYY`) | Carry forward to that year's four quarters when building quarterly model inputs. |
| Semiannual (`YYYY-H1`) | Carry forward to `Q1` and `Q2` or the project-approved fiscal mapping. |
| Quarterly (`YYYY-Qn`) | Use the same quarter. |
| Irregular essays | Assign to publication quarter when known; otherwise preserve native timestamp and document mapping notes. |

---

## 4. FinBERT Embeddings

Current embedding outputs are CSV files under `finbert_embedding/results/`.

| Column | Type | Example | Description |
|---|---|---|---|
| `investor_id` | `string` | `INV_BUFFETT` | Investor identifier. |
| `timestamp` | `string` | `2019-Q1` | Native period parsed from filename or cleaned text row. |
| `Date` | `string` | `2019-Q1` or `1Q19` | Backward-compatible date column. Downstream quarterly integration should standardize this to `NQYY`. |
| `year` | `integer` | `2019` | Four-digit year. |
| `quarter` | `integer` / empty | `1` | Quarter if available. |
| `half` | `integer` / empty | `1` | Half-year if available. |
| `period_type` | `string` | `quarter` | `year`, `half`, `quarter`, or `unknown`. |
| `filename` | `string` | `Hawkins_24_Q2_01.pdf` | Source filename. |
| `source_ext` | `string` | `pdf` | Source extension. |
| `word_count` | `integer` | `2840` | Extracted text word count. |
| `dim_0` ... `dim_767` | `float` | `0.031` | FinBERT embedding dimensions for `ProsusAI/finbert`-style BERT models. |

Embedding extraction should accept raw `.pdf`, `.txt`, `.htm`, and `.html` files, but the recommended Role 4 production flow is:

```text
raw files -> text cleaning / section slicing -> investor_text.csv -> FinBERT embeddings
```

---

## 5. Macro State (`macro_state.csv`)

| Column | Type | Example | Description |
|---|---|---|---|
| `Date` | `string` (PK) | `1Q26` | Quarterly key, format `NQYY`. |
| `inflation` | `float` | `0.73` | CPI YoY quantile. |
| `cycle` | `float` | `0.14` | Real GDP growth quantile. |
| `unemployment` | `float` | `0.28` | Unemployment quantile, inverted if used as strength. |
| `monetary` | `float` | `0.76` | Fed Funds Rate quantile. |
| `stress` | `float` | `0.63` | VIX quantile. |
| `macro_state_label` | `string` | `Inflationary Tightening` | Macro regime label. |

---

## 6. Factor Fingerprint (`factor_fingerprint.csv`)

| Column | Type | Example | Description |
|---|---|---|---|
| `Date` | `string` (PK) | `3Q08` | Quarterly key. |
| `investor_id` | `string` (PK) | `INV_BUFFETT` | Investor identifier. |
| `mkt_rf` | `float` | `0.85` | Market factor beta. |
| `smb` | `float` | `-0.12` | Size factor exposure. |
| `hml` | `float` | `0.45` | Value factor exposure. |
| `rmw` | `float` | `0.20` | Profitability / quality exposure. |
| `cma` | `float` | `0.15` | Investment factor exposure. |
| `alpha` | `float` | `0.02` | Regression intercept. |

---

## 7. Unified Dataset

The final model dataset should use `Date` + `investor_id` as its composite key.

| Column | Type | Source | Description |
|---|---|---|---|
| `Date` | `string` | All roles | Quarterly key, `NQYY`. |
| `investor_id` | `string` | Role 1 raw handoff / Role 4 cleaned text | Investor identifier. |
| `macro_state` | `string` | Role 2 | JSON array `[inflation, cycle, unemployment, monetary, stress]`. |
| `macro_state_label` | `string` | Role 2 | Macro regime label. |
| `risk_attitude` | `float` | Role 4 | 0-1 persona score. |
| `time_horizon` | `float` | Role 4 | 0-1 persona score. |
| `loss_aversion` | `float` | Role 4 | 0-1 persona score. |
| `macro_sensitivity` | `float` | Role 4 | 0-1 persona score. |
| `mkt_rf` | `float` | Role 3 | FF market exposure. |
| `smb` | `float` | Role 3 | FF size exposure. |
| `hml` | `float` | Role 3 | FF value exposure. |
| `rmw` | `float` | Role 3 | FF profitability exposure. |
| `cma` | `float` | Role 3 | FF investment exposure. |
| `alpha` | `float` | Role 3 | FF regression intercept. |

---

## 8. Enumerated Values

### `source_type`

| Value | Description | Current Use |
|---|---|---|
| `annual_letter` | Annual shareholder letter | Buffett |
| `quarterly_letter` | Quarterly investor letter/commentary | Grantham, Hawkins 2022+ |
| `interim_letter` | Semiannual shareholder letter/report | Hawkins, Driehaus, Baron, Yacktman |
| `market_commentary` | Market commentary or PM discussion | Driehaus, Baron |
| `signature_essay` | Named essay, white paper, or viewpoint | Grantham |
| `agm_transcript` | Annual meeting Q&A transcript | Optional Buffett supplement |
| `interview` | Interview transcript | Optional supplement |
| `speech` | Public speech or conference transcript | Optional supplement |
| `memo` | Investment memo | Optional supplement |
| `book_excerpt` | Book excerpt | Optional supplement |

### Period Formats

| Field | Format | Example |
|---|---|---|
| `timestamp` annual | `YYYY` | `2015` |
| `timestamp` half | `YYYY-Hn` | `2022-H1` |
| `timestamp` quarter | `YYYY-Qn` | `2019-Q1` |
| `Date` model key | `NQYY` | `1Q19` |

### CSV Rules

- Encoding: UTF-8 without BOM
- Delimiter: comma
- Quote character: double quote
- Line ending: LF
- Missing values: empty string
