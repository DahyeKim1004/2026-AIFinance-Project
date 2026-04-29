# Role 1 — Text Data Processing PLAN

> **목적**: Role 1이 확정한 분석 대상 투자자 8명, 데이터 출처, 폴더 구조, 산출물 형식을 한 문서에 정리. Role 2/3/4 모두가 이 문서를 기준선(single source of truth)으로 사용.

---

## 1. 프로젝트 개요

**InvestorDNA** — 유명 투자자의 언어적 성향(Persona Vector)과 실제 13F 포트폴리오의 Factor Fingerprint를 직접 매핑하고, 일반 사용자를 가장 가까운 투자자에 매칭하여 ETF로 갭을 메우게 해주는 Streamlit 앱.

채택 플랜: **[project_v2.md](../project_v2.md)** (Original Vision)
- Phase 2: [텍스트 + 거시] → GRU → Persona Vector
- Phase 3: [13F 포트폴리오] → Fama-French 회귀 → Factor Fingerprint
- Phase 4: Persona Vector ↔ Factor Fingerprint 직접 매핑

Role 1의 산출물은 **Phase 2의 입력(텍스트 코퍼스)**이며, Role 2의 13F 수집 대상도 이 문서가 정한 8명을 따름.

---

## 2. 분석 대상 — 8명의 투자자

| # | 카테고리 | 투자자 | Entity (CIK) | 13F 시계열 | 텍스트 1차 출처 | 인지도 | ETF 매핑 |
|---|---|---|---|---|---|---|---|
| 1 | Quality Compounder Value | Warren Buffett | Berkshire Hathaway (1067983) | 1998~ (28y) | [berkshirehathaway.com letter](https://www.berkshirehathaway.com/letters/letters.html) (1977~) + AGM Q&A | ⭐⭐⭐⭐⭐ | MOAT, QUAL, VLUE |
| 2 | Deep Value Contrarian | Mason Hawkins | Southeastern Asset Mgmt (807985) | 1996~ (30y) | 반기 letter (SEC EDGAR Longleaf Partners Funds Trust [CIK 806636](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000806636&type=N-CSR), 1996~2021) → 분기 per-fund letter ([site](https://southeasternasset.com/mutual-fund-commentaries/), 2022~) | ⭐⭐⭐⭐ | RPV, IUSV |
| 3 | Macro Systematic | Ray Dalio | Bridgewater Associates (1350694) | 2006~ (20y) | [LinkedIn 포스트](https://www.linkedin.com/in/raydalio) + 저서(Principles, Big Debt Crises 등) + 인터뷰 transcript | ⭐⭐⭐⭐⭐ | RPAR, AOA |
| 4 | Macro Discretionary | Stanley Druckenmiller | Duquesne Family Office (1536411) | 2012~ (14y) | CNBC/Sohn/Bloomberg 인터뷰 transcript (YouTube + 언론 archive) | ⭐⭐⭐⭐⭐ | DBMF, KMLM |
| 5 | Momentum / Trend | Richard Driehaus | Driehaus Capital Mgmt (938206) | 1999~ (27y) | [driehaus.com 분기 commentary](https://www.driehaus.com/insights) | ⭐⭐⭐ | MTUM, PDP |
| 6 | Long/Short Fundamental | David Einhorn | Greenlight Capital (1079114) | 2000~ (24y) | [hedgefundalpha.com](https://hedgefundalpha.com) 등 third-party archive (분기 letter) | ⭐⭐⭐⭐ | BTAL, QLS |
| 7 | Disruptive Growth | Ron Baron | Baron Capital/BAMCO (1017918) | 2000~ (25y) | [baronfunds.com 분기 letter](https://www.baronfunds.com/insights/quarterly-reports) + Baron Investment Conference | ⭐⭐⭐⭐⭐ | ARKK, QQQ |
| 8 | Dividend Growth | Don Yacktman | Yacktman Asset Mgmt (874118) | 1992~ (30y) | [yacktman.com 반기 letter](https://www.yacktman.com) + Yacktman Focused Fund commentary | ⭐⭐⭐ | SCHD, VIG, NOBL |

---

## 3. 카테고리 선정 방법론 — 왜 이 8개인가

### 원칙 1 — Fama-French / Factor 모델과의 매핑 가능성
v2 plan의 Phase 5.5(ETF 추천)가 작동하려면 각 카테고리가 일반 사용자가 **ETF로 reproduce 가능**한 factor exposure에 대응해야 함.
- ❌ **Activist 카테고리 제외** (Ackman/Icahn): "거버넌스 알파"는 자본력 기반 권력형 투자라 individual factor exposure로 환원되지 않음. 사용자에게 "당신은 Ackman" → 추천할 ETF가 없음.

### 원칙 2 — 카테고리 직교성 (8개 결이 겹치지 않게)
- **Value 두 결**: Quality Compounder(Buffett) ↔ Deep Value Contrarian(Hawkins)
- **Macro 두 결**: Systematic Risk-Parity(Dalio) ↔ Discretionary Trading(Druckenmiller)
- **Equity Style 네 결**: Momentum(Driehaus) / Long-Short(Einhorn) / Disruptive Growth(Baron) / Dividend Growth(Yacktman)

### 원칙 3 — Equity-pure 13F (포트폴리오 ↔ 텍스트 정합성)
13F-HR은 미국 상장 주식·ETF만 보고. 채권·distressed debt·private credit은 13F 미반영. 따라서 운용 자산의 **다수가 미국 상장 주식**이어야 13F 기반 Factor Fingerprint가 그 사람의 진짜 스타일을 반영.
- ❌ **Howard Marks (Oaktree)** — distressed debt + high-yield 위주, 13F 미반영
- ❌ **Seth Klarman (Baupost)** — 2024 restructuring 후 credit 중심, 13F는 AUM의 19%만
- ❌ **Bill Gross (PIMCO)** — 채권 위주

---

## 4. 투자자 선정 방법론 — 왜 이 8명인가

### 조건 1 — 13F-HR 시계열 ≥ 15년
GRU 학습량 확보. SEC EDGAR로 모든 후보 직접 검증. 위 §2 표 "13F 시계열" 컬럼 참조.

### 조건 2 — 텍스트 코퍼스 분기 cadence 가용
v2 GRU의 분기 입력과 정렬 가능해야 함. 분기 letter 부재 시 인터뷰/소셜 포스트로 보충 (Dalio·Druckenmiller가 이 케이스).
- ❌ **Peter Lynch** — Magellan 1977-90 시기 SEC 분기 보고 의무 자체가 없었음(N-Q rule은 2004 도입). 반기 N-30D만 → 분기 시계열 재구성 불가
- ❌ **Joel Greenblatt** — Gothamfunds.com에 commentary 페이지 없음(404). 책 4권만 정적
- ❌ **William O'Neil** — IBD 발행사. 운용사 아니라 13F 자체 미보고

### 조건 3 — 인지도
사용자 매칭 시 "이 사람이 누군지 모릅니다"가 안 나와야 함.
- 일반 대중 5/5: Buffett, Dalio, Druckenmiller, Baron
- 가치투자 커뮤니티 4/5: Hawkins, Einhorn
- 학계/실무 3/5: Driehaus, Yacktman
- ❌ 제외: Glenn Greenberg, Donald Smith, Tom Slater, Rajiv Jain (인지도 ≤ 2/5)

### 조건 4 — ETF 매핑 가능성
Phase 5.5 Gap Advice가 작동하려면 매칭된 투자자 스타일을 retail이 살 수 있는 ETF로 환산 가능해야 함. 모든 8명이 충족 (위 §2 표 마지막 컬럼).
- Yacktman의 SCHD 매핑은 retail 인기도 측면에서 특히 valuable (2025-26 retail 최대 매수 ETF).

---

## 5. 검토했으나 제외한 후보 (간략)

| 후보 | 제외 사유 |
|---|---|
| Peter Lynch | 분기 holdings 데이터 부재 (조건 2) |
| Joel Greenblatt | 분기 텍스트 cadence 없음 (조건 2) |
| William O'Neil | 13F 미보고 (조건 1) |
| Howard Marks (Oaktree) | 13F가 distressed debt 미반영 (원칙 3) |
| Seth Klarman (Baupost) | 13F가 AUM의 19%만 (원칙 3) |
| Cathie Wood (ARK) | 13F 9년·텍스트 11년만, 시계열 부족 (조건 1) |
| Tiger Global / Lone Pine / Coatue | letter 비공개 (조건 2) |
| Bill Ackman / Carl Icahn | Activist (원칙 1) |
| Michael Burry | 13F 비연속(2008-2015 결손) + put option으로 시가 왜곡 |
| Bill Miller | Growth-tilt가 Ron Baron과 일부 침범, 본인 letter 2021 Q3 종료 |
| Cliff Asness (AQR) | multi-factor라 단일 페르소나 매핑 모호 |
| Bill Nygren (Oakmark) | Buffett(Quality Value)와 결 일부 겹침 |

---

## 6. Time Period

**모든 투자자 공통의 교집합을 강제하지 않음.** 각 투자자의 실제 활동 시기에 13F + 텍스트가 공존하는 분기를 사용.

근거: 사용자(Role 1)의 결정 — "버핏이 30년 활동, 린치가 13년 활동이면 각각의 활동 기간을 그대로 사용. 모델이 거시-개인 매핑을 학습하는 것이 목표지, 동일 기간에서 행태 비교가 목표가 아님."

거시 라벨(GDP/Inflation/VIX)은 Role 2가 모든 분기에 대해 산출하여 동일 라벨 셋을 모든 투자자에 적용.

### Cadence 노트 — 분기 정렬 시 주의

§2 표의 "텍스트 1차 출처" 가 implicit 하게 분기 letter 처럼 보이지만 실제 cadence 는 투자자/기간별로 다음과 같이 상이:

| 투자자 | Native cadence | 비고 |
|---|---|---|
| Buffett | **연간** (annual letter only) | 분기 정렬 시 같은 letter 를 4개 분기 carry-forward 또는 AGM Q&A 보충 필요 |
| Hawkins | **1996-2021 반기** (N-30D + N-CSR/N-CSRS) → **2022~ 분기 per-fund** | 반기 letter 는 2개 분기로 carry-forward |
| Dalio | 비정형 (LinkedIn 포스트 cadence 가변) | 분기 시간창으로 그룹핑 |
| Druckenmiller | 비정형 (인터뷰 발생 시점) | 분기 시간창으로 그룹핑 |
| Driehaus, Einhorn, Baron | **분기 letter** (native) | carry-forward 불필요 |
| Yacktman | **반기 letter** | 2개 분기 carry-forward |

분기 단위로 align 할 때의 정책은 Role 2/3 스키마 합의 단계에서 확정. Role 1 산출(`investor_text.csv`) 의 `source_type` + `chunk_id` 메타데이터로 cadence 정보 보존.

---

## 7. Role 1 산출물 형식 (Role 4 스키마 합의 전 잠정안)

[README.md:46-49](../README.md) 표 + 다음 컬럼 추가 권장:
- `chunk_id` (분기 내 텍스트가 분할될 때)
- `word_count`
- `source_url` (원본 출처 추적)
- `source_type` 확장 어휘:
  - `annual_letter`, `quarterly_letter`, `interim_letter`
  - `memo`, `market_commentary`
  - `agm_transcript`, `interview`, `speech`
  - `social_post` (Dalio LinkedIn 등)
  - `book_excerpt`

`data/investors.csv` 컬럼 스키마 (잠정):
```
investor_id, name, firm, cik, category, style_short,
thirteen_f_start, text_source_primary, text_source_url,
recognition_score, etf_mapping
```

> **Role 4와 합의 후 위 스키마 확정** — 합의되면 본 §7의 "잠정안" 표시 제거.

---

## 8. 폴더 구조

다른 Role 브랜치(`macro-data-processing`, `portfolio-data-processing`, `model-architecture`, `app-integration`)와 main 머지 시 충돌하지 않도록 모든 Role 1 산출물을 **`TextData-Processing/` 네임스페이스**에 격리. 다른 팀도 본인 브랜치에서 동일 패턴(`MacroData-Processing/` 등)을 쓰면 자연스럽게 정리됨.

```
2026-AIFinance-Project/
├── README.md, project.md, project_v2.md       (existing)
├── .gitignore                                  (UPDATE: TextData-Processing 항목 추가)
│
└── TextData-Processing/                        ← Role 1 네임스페이스
    ├── PLAN.md                                 ← 본 문서
    │
    ├── data/
    │   ├── investors.csv                       (committed) 8명 메타데이터 단일 진실 소스
    │   │
    │   ├── raw/                                (gitignored) 원본 PDF/HTML/TXT
    │   │   ├── buffett/                        (예: 2008ltr.pdf)
    │   │   ├── hawkins/
    │   │   ├── dalio/
    │   │   ├── druckenmiller/
    │   │   ├── driehaus/
    │   │   ├── einhorn/
    │   │   ├── baron/
    │   │   └── yacktman/
    │   │
    │   ├── interim/                            (gitignored) 클리닝 중간 산출 (xlsx)
    │   │   └── {investor_id}_{quarter}.xlsx    엑셀에서 직접 열어 청크 단위 검수
    │   │
    │   └── processed/                          (committed) 최종 정제 데이터
    │       └── investor_text.csv               Role 2/3/4 import용 primary export
    │
    ├── scripts/
    │   ├── text_scraper.py                     수집 (Phase 1 파일럿: Buffett + Hawkins)
    │   ├── text_cleaner.py                     클리닝 (헤더/푸터/인코딩)
    │   └── text_tagger.py                      메타데이터 태깅 + CSV export
    │
    └── notebooks/                              (gitignored) exploratory analysis (.ipynb)
```

### 폴더별 형식 결정

| 폴더 | 형식 | 이유 |
|---|---|---|
| `raw/` | PDF / HTML / TXT (원본 그대로) | 다운로드한 형식 보존, 재처리 가능 |
| `interim/` | **xlsx** | 디버깅 시 엑셀에서 직접 열어 청크 단위 확인 편리 (.gitignore라 binary 형식이 git diff에 무관) |
| `processed/` | **CSV** | Role 2/3/4의 Python pandas import에 가장 가벼움, 텍스트 diff 가능 |

### `.gitignore` 추가 항목

```
# Role 1 (TextData-Processing) — 무거운 원본/중간 산출물 제외
TextData-Processing/data/raw/
TextData-Processing/data/interim/
TextData-Processing/notebooks/
*.ipynb
```

---

## 9. 작업 순서 (Phase 1 로드맵)

1. ✅ **PLAN.md 작성** (본 문서)
2. ✅ **폴더 구조 생성** + `.gitignore` 갱신 + `investors.csv` 초안
3. ⏳ **Role 4와 메타데이터 스키마 합의** (블로킹: 다른 Role 시작 전 필수)
4. ⏳ **`scripts/text_scraper.py` 파일럿** — Buffett (정적 HTML/PDF) + Hawkins (longleafpartners.com 분기 archive) 두 패턴 검증
5. ⏳ **나머지 6명에 패턴 확장**
6. ⏳ **`data/processed/investor_text.csv` 첫 commit** — Role 2/3/4 다음 단계 unblock

---

## 10. 참고 — Role 간 의존 관계

```
Role 1 (Text)         ──┐
                        ├─→ Role 4 (Schema) → investor_text.csv 확정
Role 2 (Macro/13F)    ──┘                           │
                                                    ├─→ Role 3 (Model) → GRU 학습
                                                    └─→ Role 5 (App) → Streamlit
```

Role 1의 8명 리스트 + Time Period 결정이 **모든 다음 단계를 unblock**. 이 PLAN.md를 Role 2/3/4에 공유하는 즉시 병렬 진행 가능.
