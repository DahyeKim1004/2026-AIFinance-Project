# Role 4: Model Architecture & Data Schema (모델 아키텍처 & 데이터 스키마 관리)

## 📌 Role Objective
이 브랜치(`model-architecture`)는 **Role 4 담당자**를 위한 작업 공간입니다.
주요 목표는 **Personality 축을 정의하고, GRU 모델 및 PLS 모델의 틀을 준비하는 것**입니다.
또한, 프로젝트 전체의 **데이터 스키마(Data Schema), 코드북(Codebook), 메타데이터(Metadata) 형식**을 정의하고 관리합니다.
Role 1, 2, 3의 산출물이 이 브랜치에서 정의한 스키마에 맞추어 통합됩니다.

---

## 📊 Key Responsibilities (주요 업무)

### 1. Personality Axis Definition (성격 축 정의)
- FinBERT 이용해서 추출된 embedding 활용해서 Persona Vector 만들기 위해서 우선 각 Personality Dimension을 LLM 기반으로 정의해두어야 함. 
- Sentences that match each personality dimension define -> Create Personality Vector
- **추출 대상 축(Personality Dimensions):**
  - Risk Tolerance: 위험 감수 성향
  - Time Horizon: 투자 시계
  - Loss Aversion: 손실 회피 성향
  - Marco Senstivity: 거시 경제 민감도
- **주기:** Yearly (Annual Shareholder Letters) 

### 2. Data Schema & Codebook Management (데이터 스키마 & 코드북 관리)
- Role 1, 2, 3의 모든 산출물이 통합되는 **통합 데이터셋(Unified Dataset)** 의 컬럼 및 형식을 정의합니다.
- `/schemas/codebook.md`: 모든 변수명, 데이터 타입, 출처, 설명을 기록
- `/schemas/metadata.json`: 데이터셋 버전, 처리 파라미터, 데이터 출처를 기록

### 3. Model Framework Preparation (모델 틀 준비)
- **GRU Model:** 분기별 Personality 점수 시계열을 입력으로 받아, Macro State에 따른 변화를 학습하는 순환 신경망(RNN) 모델 틀 구성
- **PLS Model (Partial Least Squares):** GRU의 Persona Output과 Fama-French Factor Fingerprint 간의 관계를 매핑하는 회귀 모델 틀 구성

### 4. Data Formatting & Export
- 통합 데이터는 `CSV` 및 `JSON` 형태로 `/data/processed/` 디렉터리에 저장합니다.
- 모든 데이터 처리 스크립트는 `/schemas/metadata.json`에 정의된 파라미터를 따릅니다.

---

## 📂 Expected Output (예상 결과물 형태)

통합 데이터셋의 예시 형태입니다:

| Year | investor_id | macro_state | risk_attitude | time_horizon | loss_aversion | factor_value | factor_quality |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2008 | INV_BUFFETT | [1,1,1,1,1] | 0.72 | 0.90 | 0.30 | 0.45 | 0.20 |
| 2020 | INV_DALIO | [2,3,2,2,1] | 0.50 | 0.65 | 0.55 | 0.10 | 0.40 |

---

## 📁 Directory Structure (이 브랜치의 폴더 구조)

```text
/data/
  /raw/           # Role 1, 2, 3에서 넘어온 원본 데이터
  /processed/     # 통합 정제 데이터 (모델 입력용)
/models/
  /gru/           # GRU 모델 스크립트
  /pls/           # PLS 모델 스크립트
/schemas/
  codebook.md     # 변수 정의 코드북
  metadata.json   # 메타데이터 포맷
```

---

## 🚀 How to Work in this Branch
1. `/schemas/codebook.md`와 `/schemas/metadata.json`을 먼저 업데이트하여, 다른 Role 담당자들이 따를 수 있는 데이터 형식을 확정합니다.
2. GRU, PLS 모델 스크립트는 각각 `/models/gru/`, `/models/pls/` 디렉터리에 작성합니다.
3. 데이터는 `.gitignore`를 통해 원본 대용량 파일이 GitHub에 올라가지 않도록 관리합니다.
4. 작업 완료 후 `git add`, `git commit`, `git push`를 통해 본인의 작업을 저장하세요.
