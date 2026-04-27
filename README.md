# Role 2: Macro Data Processing (거시 경제 변수 정리)

## 📌 Role Objective
이 브랜치(`macro-data-processing`)는 **Role 2 담당자**를 위한 작업 공간입니다. 
주요 목표는 **거시 경제(Macro) 데이터를 수집하고, 경제 상황을 정의(Macro State)하는 것**입니다. 

---

## 📊 Key Responsibilities (주요 업무)

### 1. Data Collection (데이터 수집)
- **출처:** FRED (Federal Reserve Economic Data), yfinance 등
- **필수 변수:**
  - Cycle: Real GDP Growth (GDPC1) 
  - Inflation: CPI YoY (CPIAUCSL) 
  - Monetary: Fed Funds Rate (FEDFUNDS) 
  - Stress: VIX (VIXCLS) 
  - Unemployment: Unemployment (UNRATE, inverted) 
- **주기:** 분기별(Quarterly) 데이터

### 2. Macro State Definition (경제 상태 라벨링)
수집한 연속형(Continuous) 데이터를 바탕으로, 각 시점을 직관적인 **경제 상태 카테고리**로 분류합니다.
- Final output: one 5-dimensional quantile vector per quarter, labelled [cycle, inflation, monetary,
stress, sentiment].
- **분류 방법:** 과거 데이터의 분위수(Quantiles) 또는 특정 Threshold(예: 물가상승률 4% 이상 등)를 설정하여 룰 베이스(Rule-based)로 라벨링.

### 3. Data Formatting & Export
- 처리된 데이터는 최종적으로 Role 4 담당자(데이터 스키마 관리)가 정의한 메타데이터 포맷에 맞추어 `CSV` 또는 `JSON` 형태로 Export 되어야 합니다.

---

## 📂 Expected Output (예상 결과물 형태)

정제된 데이터의 예시 형태입니다:

| Year-Quarter | cycle | inflation | monetary | stress | sentiment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2008-Q3 | 1 | 1 | 1 | 1 | 1 |
| 2020-Q4 | 2 | 3 | 2 | 2 | 1 |

---
## 🚀 How to Work in this Branch
1. 파이썬 스크립트(`macro_scraper.py`, `macro_labeling.py` 등)를 작성하여 데이터를 수집하고 라벨링합니다.
2. 데이터를 저장할 때는 `.gitignore`에 데이터 폴더를 추가하여 무거운 원본 데이터가 GitHub에 올라가지 않도록 주의하세요 (정제된 최종 가벼운 `.csv` 결과물만 업로드).
3. 작업 완료 후 `git add`, `git commit`, `git push`를 통해 본인의 작업을 저장하세요.
