# Role 1: Text Data Processing (Annual Letter 수집, 정리, Tagging)

## 📌 Role Objective
이 브랜치(`text-data-processing`)는 **Role 1 담당자**를 위한 작업 공간입니다.
주요 목표는 **분석 대상 투자자(Investor) 목록을 최종 확정하고, 해당 투자자들의 Annual Letter 및 텍스트 데이터를 수집·정리·태깅하는 것**입니다.
이 브랜치에서 확정한 **투자자 리스트와 Time Period**가 프로젝트 전체의 기준이 되며, Role 2, 3, 4 모두 이를 따릅니다.

> ⚠️ **이 브랜치의 산출물이 다른 모든 Role의 출발점입니다.** 투자자 리스트와 분석 기간을 빠르게 확정하는 것이 전체 프로젝트 일정에 매우 중요합니다.

---

## 📊 Key Responsibilities (주요 업무)

### 1. Investor Selection & Finalization (투자자 목록 확정)
- 분석 대상 유명 투자자 6-8명을 선정하고 최종 확정합니다.
- **선정 기준:**
  - 충분한 양의 공개 텍스트(서한, 연설, 서적 등)가 존재하는 투자자
  - SEC 13F 등 포트폴리오 데이터가 확보 가능한 투자자
  - 서로 다른 투자 스타일을 대표하는 투자자 (예: Value, Macro, Growth 등)
- **예시 후보:** Warren Buffett, Ray Dalio, George Soros, Howard Marks, Seth Klarman 등

### 2. Text Data Collection (텍스트 데이터 수집)
- **데이터 유형:**
  - Annual Shareholder Letters (연간 주주 서한)
  - 공개 연설 및 인터뷰 전문(Transcript)
  - 서적 발췌문 (필요시)
- **출처:** SEC EDGAR, 기업 공식 홈페이지, 공개 아카이브 등
- **수집 범위:** 확정된 Time Period에 해당하는 모든 분기/연도

### 3. Text Preprocessing & Tagging (텍스트 전처리 및 태깅)
- 수집된 텍스트에 대해 다음 메타데이터를 태깅합니다:
  - `investor_id`: 투자자 고유 식별자 (예: `INV_BUFFETT`)
  - `timestamp`: 텍스트가 작성된 연도/분기 (예: `2008-Q3`)
  - `source_type`: 텍스트 출처 유형 (예: `annual_letter`, `speech`, `book`)
- 텍스트 클리닝: 불필요한 서식, 헤더/푸터 제거, 인코딩 통일

### 4. Data Formatting & Export
- 정제된 텍스트 데이터는 Role 4 담당자(데이터 스키마 관리)가 정의한 메타데이터 포맷에 맞추어 `CSV` 또는 `JSON` 형태로 Export 되어야 합니다.

---

## 📂 Expected Output (예상 결과물 형태)

정제된 데이터의 예시 형태입니다:

| investor_id | timestamp | source_type | text_content |
| :--- | :--- | :--- | :--- |
| INV_BUFFETT | 2008-Q4 | annual_letter | "The financial world is a mess, both in the United States and abroad..." |
| INV_DALIO | 2020-Q1 | speech | "The world has gone mad and the system is broken..." |

---

## 🚀 How to Work in this Branch
1. 투자자 리스트를 확정하면 `/data/` 또는 별도 문서에 기록하여 다른 Role 담당자들이 참고할 수 있도록 합니다.
2. 파이썬 스크립트(`text_scraper.py`, `text_cleaner.py` 등)를 작성하여 데이터를 수집하고 태깅합니다.
3. 데이터를 저장할 때는 `.gitignore`에 데이터 폴더를 추가하여 무거운 원본 데이터가 GitHub에 올라가지 않도록 주의하세요 (정제된 최종 가벼운 `.csv` 결과물만 업로드).
4. 작업 완료 후 `git add`, `git commit`, `git push`를 통해 본인의 작업을 저장하세요.
