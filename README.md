# Role 3: Portfolio Data Processing (Fama-French Factor 추출)

## 📌 Role Objective
이 브랜치(`portfolio-data-processing`)는 **Role 3 담당자**를 위한 작업 공간입니다.
주요 목표는 **Role 1(`text-data-processing`)이 최종 확정한 투자자 목록과 시간 범위(Time Period)에 맞추어** 포트폴리오 수익률 데이터를 수집하고, Fama-French 회귀분석을 통해 Factor Fingerprint를 추출하는 것입니다.
이 Factor Fingerprint는 이후 Role 4에서 투자자의 Persona Score와 매핑되는 핵심 타깃 변수가 됩니다.

> ⚠️ **Dependency:** 이 브랜치의 작업은 Role 1이 투자자 리스트와 분석 기간을 확정한 후에 본격적으로 시작됩니다.

---

## 📊 Key Responsibilities (주요 업무)

### 1. Portfolio Data Collection (포트폴리오 데이터 수집)
- **출처:** SEC EDGAR 13F filings, yfinance 등
- **대상 투자자:** Role 1(`text-data-processing`)이 확정한 투자자 리스트를 따름
- **필수 데이터:**
  - 분기별 포트폴리오 보유 종목 및 비중 (13F Holdings)
  - 포트폴리오 수익률 (Portfolio Returns)
- **주기:** Role 1이 확정한 Time Period에 맞춤 (분기별/Quarterly)

### 2. Fama-French Factor Regression (팩터 회귀분석)
각 투자자의 포트폴리오 수익률에 대해 Fama-French 팩터 회귀분석을 수행합니다.
- **Fama-French Factor 데이터 출처:** [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- **사용 팩터:**
  - Market (Mkt-RF): 시장 초과수익률
  - Size (SMB): 소형주 프리미엄
  - Value (HML): 가치주 프리미엄
  - Quality (RMW): 수익성 프리미엄
  - Investment (CMA): 투자 보수성 프리미엄
- **분석 방법:** OLS 회귀분석으로 각 투자자의 팩터 노출도(Factor Exposure/Loading)를 추출

### 3. Data Formatting & Export
- 추출된 Factor Fingerprint는 Role 4 담당자(데이터 스키마 관리)가 정의한 메타데이터 포맷에 맞추어 `CSV` 또는 `JSON` 형태로 Export 되어야 합니다.

---

## 📂 Expected Output (예상 결과물 형태)

정제된 데이터의 예시 형태입니다:

| Year-Quarter | investor_id | Mkt-RF | SMB | HML | RMW | CMA | Alpha |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2008-Q3 | INV_BUFFETT | 0.85 | -0.12 | 0.45 | 0.20 | 0.15 | 0.02 |
| 2020-Q1 | INV_DALIO | 0.60 | 0.05 | 0.10 | 0.40 | 0.30 | -0.01 |

---

## 🚀 How to Work in this Branch
1. 파이썬 스크립트(`portfolio_scraper.py`, `ff_regression.py` 등)를 작성하여 데이터를 수집하고 회귀분석을 수행합니다.
2. 데이터를 저장할 때는 `.gitignore`에 데이터 폴더를 추가하여 무거운 원본 데이터가 GitHub에 올라가지 않도록 주의하세요 (정제된 최종 가벼운 `.csv` 결과물만 업로드).
3. 작업 완료 후 `git add`, `git commit`, `git push`를 통해 본인의 작업을 저장하세요.
