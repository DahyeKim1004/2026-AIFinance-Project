# InvestorDNA

## AI Finance Capstone Project (Sogang University | Spring 2026)

**InvestorDNA** is a behavioral persona-to-factor translation system. The core objective of this project is to mathematically map an investor's text/language-based personality directly to their real-world portfolio returns.

### Core Architecture & Workflow
Our system leverages the following **5-Phase Pipeline**:

#### Phase 1: Preparation & Macro Context
- **Goal:** Define the economic weather (Macro State) and gather raw data.
- **Data:** GDP, Inflation, and VIX data grouped into economic labels (e.g., "Recession", "Expansion"). Create simple embedding vector using quantiles. 
- **Text:** Collect shareholder letters, public speeches, and book excerpts from 6-8 target investors (e.g., Buffett, Soros, Dalio).
- **Financials:** Gather historical portfolio returns to map against.

#### Phase 2: Building the GRU Persona (What they SAY)
- **Goal:** Analyze how their language choices change depending on the economy.
- **Process:** Extract risk-attitude keywords using NLP and LLMs. Feed those sentiment features alongside the Macro State into a GRU sequence model.
- **Output:** The **"True Persona Score"** (a mathematical baseline of their risk personality across varying economic weathers).

#### Phase 3: Factor Fingerprinting (What they HELD)
- **Goal:** Mathematically measure what their actual portfolio was built of.
- **Process:** Run Fama-French regressions on the famous investor's actual portfolio returns during the same time periods.
- **Output:** The **"Factor Fingerprint"** (quantifying exposures to Value, Market Beta, Quality, etc.).

#### Phase 4: Persona-to-Factor Mapping (The Engine)
- **Goal:** Connect the language-based personality directly to the portfolio math.
- **Process:** We mathematically link Phase 2 with Phase 3 to build a translation dictionary.
- **Expected Outcome:** An engine that states: *"When language Persona Vector is [X, Y, Z], the optimal Factor Fingerprint is almost always [Value=A, Quality=B, Risk=C]."*

#### Phase 5: The User App & Gap Advice (Streamlit)
- **Goal:** Provide actionable financial advice to a new user based on behavioral matching.
- **Flow:** 
  1. User takes a behavioral quiz to generate their own Persona Score.
  2. App finds the closest famous investor match.
  3. App analyzes the user's actual stock portfolio to calculate their current Factor Fingerprint.
  4. App calculates the gap between actual holdings and the matched ideal.
- **Output:** ETF Recommendations designed to bridge the gap and align actual investments with the stated personality.

---

### Team Roles & Branches
This repository separates the work into 4 role-based branches:

| Branch | Role | Description |
| :--- | :--- | :--- |
| `main` | — | Stable production branch and finalized documentation |
| `text-data-processing` | Role 1 | Annual letter 수집, 정리, tagging. 투자자 목록 & Time Period 최종 확정 |
| `macro-data-processing` | Role 2 | Macro 변수 정리. 거시 경제 데이터 수집 및 Macro State 라벨링 |
| `portfolio-data-processing` | Role 3 | Fama-French factor 추출. Role 1 확정 기준에 맞춘 포트폴리오 회귀분석 |
| `model-architecture` | Role 4 | Personality 축 정의, GRU/PLS 모델 틀 준비, 데이터 스키마 & 코드북 관리 |
| `app-integration` | — | Phase 5 Streamlit frontend development and user gap-analysis (TBD) |
