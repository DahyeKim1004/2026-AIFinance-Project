# InvestorDNA Codebook (데이터 코드북)

> **Version:** 1.0  
> **Last Updated:** 2026-04-29  
> **Maintained by:** Role 4 (Model Architecture & Data Schema)  
> **Status:** ✅ Confirmed — All Roles should follow this schema.

이 코드북은 프로젝트 전체에서 사용되는 모든 변수명, 데이터 타입, 출처, 설명을 정의합니다.  
Role 1, 2, 3의 산출물이 이 코드북에 맞추어 정제·통합되어야 합니다.

---

## 1. Investor Registry (`data/processed/investors.csv`)

투자자 마스터 테이블. Role 1이 확정한 8명의 메타데이터를 관리합니다.

| Column | Type | Example | Description |
|---|---|---|---|
| `investor_id` | `string` (PK) | `INV_BUFFETT` | 투자자 고유 식별자. `INV_` 접두어 + 대문자 성(姓). 전체 데이터셋의 Primary Key로 사용 |
| `name` | `string` | `Warren Buffett` | 투자자 실명 |
| `firm` | `string` | `Berkshire Hathaway` | 운용사 / 기관명 |
| `cik` | `integer` | `1067983` | SEC EDGAR CIK 번호 (13F 조회용) |
| `category` | `string` | `Quality Compounder Value` | 투자 스타일 카테고리 (8개 직교 카테고리) |
| `style_short` | `string` | `quality_value` | `category`의 snake_case 축약형 (코드 내 사용) |
| `thirteen_f_start` | `integer` | `1998` | 13F 보고 시작 연도 (SEC EDGAR 기준) |
| `text_source_primary` | `string` | `annual_letter` | 주요 텍스트 출처 유형. 허용 값은 §5 `source_type` 어휘 참조 |
| `text_source_url` | `string` | `https://...` | 텍스트 1차 출처 URL |
| `recognition_score` | `integer` (1-5) | `5` | 일반 대중 인지도 점수 |
| `etf_mapping` | `string` | `MOAT;QUAL;VLUE` | 스타일 매핑 가능 ETF 목록 (세미콜론 구분) |

### 확정된 투자자 8명

| # | investor_id | Category | Native Cadence |
|---|---|---|---|
| 1 | `INV_BUFFETT` | Quality Compounder Value | Annual letter (4Q carry-forward) |
| 2 | `INV_HAWKINS` | Deep Value Contrarian | Semi-annual → Quarterly (2022~) |
| 3 | `INV_DALIO` | Macro Systematic | Irregular (LinkedIn, books) |
| 4 | `INV_DRUCKENMILLER` | Macro Discretionary | Irregular (interviews) |
| 5 | `INV_DRIEHAUS` | Momentum / Trend | Quarterly commentary |
| 6 | `INV_EINHORN` | Long/Short Fundamental | Quarterly letter |
| 7 | `INV_BARON` | Disruptive Growth | Quarterly letter |
| 8 | `INV_YACKTMAN` | Dividend Growth | Semi-annual letter |

---

## 2. Text Corpus (`data/processed/investor_text.csv`) — Role 1 산출물

투자자별 텍스트 데이터. FinBERT embedding 및 Personality Vector 추출의 입력 데이터.

| Column | Type | Example | Description |
|---|---|---|---|
| `investor_id` | `string` (FK) | `INV_BUFFETT` | 투자자 식별자. `investors.csv`의 PK 참조 |
| `year_quarter` | `string` | `2008-Q4` | 텍스트가 귀속되는 분기. 형식: `YYYY-QN` |
| `source_type` | `string` (enum) | `annual_letter` | 텍스트 출처 유형. 허용 값은 §5 참조 |
| `chunk_id` | `integer` | `1` | 동일 분기 내 텍스트 분할 시 순번 (1부터) |
| `text_content` | `string` | `"The financial..."` | 정제된 텍스트 본문 (UTF-8, 헤더/푸터 제거) |
| `word_count` | `integer` | `3542` | `text_content`의 단어 수 |
| `source_url` | `string` | `https://...` | 원본 텍스트 출처 URL (추적용) |

### Cadence Alignment Policy (분기 정렬 정책)

텍스트의 native cadence가 분기가 아닌 경우:
- **Annual letter** (Buffett): 동일 텍스트를 해당 연도 4개 분기에 carry-forward
- **Semi-annual letter** (Hawkins, Yacktman): 동일 텍스트를 2개 분기에 carry-forward
- **Irregular** (Dalio, Druckenmiller): 발행 시점 기준 분기 시간창으로 그룹핑

---

## 3. Macro State (`data/processed/macro_state.csv`) — Role 2 산출물

거시 경제 상태 벡터. GRU 모델의 contextual input으로 사용됩니다.

| Column | Type | Example | Description |
|---|---|---|---|
| `year_quarter` | `string` (PK) | `2008-Q3` | 분기 식별자. 형식: `YYYY-QN` |
| `cycle` | `float` (0.0-1.0) | `0.166` | Real GDP Growth (GDPC1) 기반 quantile (0~1) |
| `inflation` | `float` (0.0-1.0) | `0.708` | CPI YoY (CPIAUCSL) 기반 quantile (0~1) |
| `monetary` | `float` (0.0-1.0) | `0.805` | Fed Funds Rate (FEDFUNDS) 기반 quantile (0~1) |
| `stress` | `float` (0.0-1.0) | `0.875` | VIX (VIXCLS) 기반 quantile (0~1) |
| `sentiment` | `float` (0.0-1.0) | `0.513` | Unemployment Rate (UNRATE, inverted) 기반 quantile (0~1) |
| `label` | `string` (enum) | `Recession` | 경제 상태 라벨 (Recession, Expansion, Neutral, Stagflation Risk, Inflationary Tightening) |

### Quantile & Labeling 정의

각 변수는 과거 데이터에 대해 0~1 사이의 상대적 위치(Quantile)로 변환됩니다:
- `0.0` = 과거 최저치
- `1.0` = 과거 최고치

**Macro State Labels:**
- `Recession`: 경기 후퇴 (Low Cycle, High Stress/Unemployment)
- `Expansion`: 경기 확장 (High Cycle, Low Stress)
- `Neutral`: 중립 상태
- `Stagflation Risk`: 스태그플레이션 위험 (High Inflation, Low Cycle)
- `Inflationary Tightening`: 인플레 억제 및 긴축 (High Inflation, High Monetary)

### FRED Series Mapping

| Dimension | FRED Series ID | Frequency | Transform |
|---|---|---|---|
| `cycle` | `GDPC1` | Quarterly | YoY % change |
| `inflation` | `CPIAUCSL` | Monthly → Quarterly avg | YoY % change |
| `monetary` | `FEDFUNDS` | Monthly → Quarter-end | Level |
| `stress` | `VIXCLS` | Daily → Quarterly avg | Level |
| `sentiment` | `UNRATE` | Monthly → Quarterly avg | Inverted level |

---

## 4. Factor Fingerprint (`data/processed/factor_fingerprint.csv`) — Role 3 산출물

Fama-French 5-Factor 회귀분석 결과. PLS 모델의 타깃 변수로 사용됩니다.

| Column | Type | Example | Description |
|---|---|---|---|
| `year_quarter` | `string` (PK) | `2008-Q3` | 분기 식별자. 형식: `YYYY-QN` |
| `investor_id` | `string` (PK) | `INV_BUFFETT` | 투자자 식별자 (복합 PK) |
| `mkt_rf` | `float` | `0.85` | Market 팩터 노출도 (시장 초과수익률 베타) |
| `smb` | `float` | `-0.12` | Size 팩터 노출도 (소형주 프리미엄) |
| `hml` | `float` | `0.45` | Value 팩터 노출도 (가치주 프리미엄) |
| `rmw` | `float` | `0.20` | Quality/Profitability 팩터 노출도 (수익성) |
| `cma` | `float` | `0.15` | Investment 팩터 노출도 (투자 보수성) |
| `alpha` | `float` | `0.02` | Jensen's Alpha (잔차 초과수익률) |

### Factor Data Source

- **Source:** [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- **Model:** Fama-French 5-Factor (Mkt-RF, SMB, HML, RMW, CMA)
- **Method:** Rolling OLS regression per investor per quarter (window: 12 quarters)
- **Returns:** Portfolio returns calculated from 13F holdings (SEC EDGAR)

---

## 5. Enumerated Values (열거형 값 정의)

### `source_type` 허용 어휘

텍스트 출처 유형을 분류하는 통제 어휘(controlled vocabulary)입니다.

| Value | Description | 해당 투자자 |
|---|---|---|
| `annual_letter` | 연간 주주 서한 | Buffett |
| `quarterly_letter` | 분기별 투자 서한 | Einhorn, Baron |
| `interim_letter` | 반기 투자 서한 | Hawkins, Yacktman |
| `memo` | 투자 메모 | (해당 시 사용) |
| `market_commentary` | 시장 코멘터리 | Driehaus |
| `agm_transcript` | 주주총회 Q&A 전문 | Buffett (보충) |
| `interview` | 인터뷰 전문(transcript) | Druckenmiller |
| `speech` | 공개 연설/컨퍼런스 | Baron (Conference) |
| `social_post` | 소셜 미디어 포스트 | Dalio (LinkedIn) |
| `book_excerpt` | 서적 발췌문 | Dalio (Principles 등) |

### `investor_id` 형식 규칙

- 접두어: `INV_`
- 본문: 투자자 성(姓)의 대문자 표기
- 예시: `INV_BUFFETT`, `INV_DALIO`, `INV_DRUCKENMILLER`

### `year_quarter` 형식 규칙

- 형식: `YYYY-QN` (N = 1, 2, 3, 4)
- 예시: `2008-Q3`, `2020-Q1`
- Q1 = Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep, Q4 = Oct-Dec

---

## 6. Unified Dataset (`data/processed/unified_dataset.csv`) — Role 4 통합

GRU 및 PLS 모델 학습을 위한 최종 통합 데이터셋입니다.

| Column | Type | Source | Description |
|---|---|---|---|
| `year_quarter` | `string` (PK) | All Roles | 분기 식별자 |
| `investor_id` | `string` (PK) | Role 1 | 투자자 식별자 (복합 PK) |
| `macro_state` | `string` | Role 2 | 5차원 quantile 벡터 (JSON array, 예: `[0.16, 0.71, 0.81, 0.88, 0.51]`) — `[cycle, inflation, monetary, stress, sentiment]` |
| `macro_label` | `string` | Role 2 | 경제 상태 라벨 (예: `Recession`) |
| `risk_attitude` | `float` | Role 4 (GRU) | Personality Dimension: 위험 감수 성향 점수 |
| `time_horizon` | `float` | Role 4 (GRU) | Personality Dimension: 투자 시계 점수 |
| `loss_aversion` | `float` | Role 4 (GRU) | Personality Dimension: 손실 회피 성향 점수 |
| `macro_sensitivity` | `float` | Role 4 (GRU) | Personality Dimension: 거시 경제 민감도 점수 |
| `mkt_rf` | `float` | Role 3 | Market 팩터 노출도 |
| `smb` | `float` | Role 3 | Size 팩터 노출도 |
| `hml` | `float` | Role 3 | Value 팩터 노출도 |
| `rmw` | `float` | Role 3 | Quality 팩터 노출도 |
| `cma` | `float` | Role 3 | Investment 팩터 노출도 |
| `alpha` | `float` | Role 3 | Jensen's Alpha |

### Personality Dimensions (성격 축)

GRU 모델 출력으로 생성되는 4개 Personality 점수:

| Dimension | Column | Range | High = | Low = |
|---|---|---|---|---|
| Risk Tolerance | `risk_attitude` | 0.0 – 1.0 | 위험 추구형 | 위험 회피형 |
| Time Horizon | `time_horizon` | 0.0 – 1.0 | 장기 투자 | 단기 투자 |
| Loss Aversion | `loss_aversion` | 0.0 – 1.0 | 손실에 둔감 | 손실에 민감 |
| Macro Sensitivity | `macro_sensitivity` | 0.0 – 1.0 | 거시 민감 | 거시 둔감 |

---

## 7. Time Period Policy (시간 범위 정책)

- **공통 교집합을 강제하지 않음.** 각 투자자의 실제 활동 시기에 13F + 텍스트가 공존하는 분기를 사용합니다.
- 거시 라벨(macro_state)은 Role 2가 **모든 분기**에 대해 산출하여 동일 라벨 셋을 모든 투자자에 적용합니다.
- 가장 이른 시작: `1992-Q1` (Yacktman 13F 시작)
- 가장 최근: 데이터 수집 시점의 직전 완료 분기

---

## 8. File Naming Conventions (파일 명명 규칙)

| File | Location | Format | Description |
|---|---|---|---|
| `investors.csv` | `data/processed/` | CSV (UTF-8) | 투자자 마스터 레지스트리 |
| `investor_text.csv` | `data/processed/` | CSV (UTF-8) | 정제된 텍스트 코퍼스 |
| `macro_state.csv` | `data/processed/` | CSV (UTF-8) | 거시 경제 상태 벡터 |
| `factor_fingerprint.csv` | `data/processed/` | CSV (UTF-8) | FF5 팩터 노출도 |
| `unified_dataset.csv` | `data/processed/` | CSV (UTF-8) | 최종 통합 데이터셋 |
| `metadata.json` | `schemas/` | JSON | 데이터셋 메타데이터 |

### CSV Encoding Rules

- **Encoding:** UTF-8 (BOM 없음)
- **Delimiter:** Comma (`,`)
- **Quote Character:** Double quote (`"`) — 텍스트 내 쉼표 포함 시 사용
- **Line Ending:** LF (`\n`)
- **Header:** 첫 행은 반드시 컬럼명
- **Missing Values:** 빈 문자열 (`""`)
