# Role 1 — Raw Data Collection Progress

> **Last updated**: 2026-04-30
> **Scope**: PLAN.md §2 의 7명 투자자 텍스트 코퍼스 수집 진행 현황 + 분기 정렬을 위한 추가 작업 정의.
> **Storage policy**: 본 파일을 제외한 `data/raw/` 하위 모든 파일은 `.gitignore` 처리. 무거운 원본은 commit 되지 않음.
> **Naming**: PLAN §7 규칙 — `{Investor}_{YY}` (annual), `{Investor}_{YY}_Q{n}` (quarterly), `{Investor}_{YY}_S{n}` (semi-annual), `{Investor}_{YY}_Q{n}_{tag}` (per-fund/세부 태그).

---

## TL;DR — 7명 진행률

| # | Investor | 상태 | 시계열 커버 | Native cadence | 주요 파일 형식 | 파일 수 | 디스크 |
|---|---|---|---|---|---|---|---|
| 1 | **Buffett** | ✅ 수집 완료 | 1977~2024 (48y) | 연간 | HTML(1977-1997) + PDF(1998-2024) | 54 | 8.9 MB |
| 2 | **Hawkins** | ✅ 수집 완료 | 1995~2026 (32y) | 1995-2021 반기 → 2022~ 분기 | PDF(site) + HTML/TXT(EDGAR) | 125 | 82 MB |
| 3 | **Grantham** | ✅ 수집 완료 | 2007~2026 (20y, gap 2016만) | 분기 letter + 시그니처 essay | PDF(gmo.com + Wayback) | 77 | 30 MB |
| 4 | **Driehaus** | ✅ 수집 완료 | 1996~2025 (30y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 65 | 142 MB |
| 5 | **Einhorn** | ❌ 사실상 부재 | 2020-2021 (2건) | 비정형 (GLRE 8-K best-effort) | HTML(EDGAR) | 2 | 16 KB |
| 6 | **Baron** | ✅ 수집 완료 | 1996~2025 (30y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 76 | 125 MB |
| 7 | **Yacktman** | ✅ 수집 완료 | 1995~2025 (30y) | 1995-2011 + 2012-2025 (운용사 변경) | HTML/TXT(EDGAR) | 127 | 266 MB |

**Aggregate**: 526 파일 / ~671 MB (전체 7명 수집 완료, collision suffix → sequence 정규화 완료)

> **확장 이력**: 1차 379 → 487 → 526 파일
> - Grantham 26 → 38 → 77 (gmo.com brute-force + Wayback Machine archive)
> - Yacktman 31 → 127 (AMG FUNDS CIK 1089951 추가, 2012+ filings 만)
> - 2026-04-30: Baron/Driehaus/Yacktman/Hawkins 의 month/accession/per-fund collision suffix → 시점 bucket + sequence 번호 로 정규화

---

## 명명규칙 (전체 공통, 2026-04-30 정규화 완료)

### 기본 패턴

```
{Investor}_{YY}                       # 단일 연간 letter        (Buffett_77.html)
{Investor}_{YY}_Q{n}                  # 단일 분기 letter        (Hawkins_07_Q1.pdf)
{Investor}_{YY}_S{n}                  # 단일 반기 letter        (Driehaus_22_S1.htm)
{Investor}_{YY}_NN                    # 다중 letter, 동일 bucket (Baron_06_S1_01.txt ... _09.txt)
{Investor}_{YY}_Q{n}_NN               # 다중 펀드 분기 letter   (Hawkins_23_Q1_01.pdf, _02, _03)
```

### 시기 (period) 결정 규칙

같은 `(Investor, YY, period)` bucket 안의 파일이 2개 이상일 때 sequence 번호 (`_01`, `_02`, ...) 부여. 단일이면 canonical (sequence 없음).

**Period 분류**:
- 분기 letter (Q1-Q4): 사이트 PDF (예: Hawkins, Grantham) — 명시적
- 반기 (S1): EDGAR 보고에서 **filing month 1-6월**
- 연간 (no period): EDGAR 보고에서 **filing month 7-12월**

> ⚠️ **주의**: Period 는 "filing 시점" 기반 분류이지 "content 의 fiscal period" 와 1:1 매핑은 아님. 예: N-CSR (annual content) 가 Feb 발간되면 → S1 bucket; N-CSRS (semi-annual content) 가 Aug 발간되면 → annual bucket. 의미적으로는 inversion 처럼 보이지만 — naming 의 목적은 **deterministic 한 시점 분류** 이고, fiscal semantics 는 text_cleaner.py 단계에서 N-CSR vs N-CSRS form 정보를 토대로 별도 추출.

### 연도 = content 연도 (fiscal period)

- N-CSR 2023-02 발간 → FY2022 보고 → year = 22, filed Feb (1-6월) → `Hawkins_22_S1.htm` (S1 bucket of 2022)
- N-CSRS 2023-08 발간 → H1 2023 → year = 23, filed Aug (7-12월) → `Hawkins_23.htm` (annual bucket of 2023)
- N-30D 1996-02 발간 → FY1995 → `Hawkins_95.txt`
- N-30D 1996-07 발간 → H1 1996 → `Hawkins_96_S1.txt`

### 보존되는 의미 태그

- **`_stub`** (Buffett): HTML stub vs PDF 본문 — file kind 구분 (다른 형식)
- **Essay 라벨** (Grantham): `_purgatory`, `_stalin`, `_bargain` 등 본인이 명명한 시그니처 letter — 의미 있는 라벨

### Consolidate 되는 collision 마커 (제거 후 sequence 번호)

원칙: **포트폴리오 본질이 같으면 묶는다**. 운용사·펀드 종류 차이는 같은 투자자의 portfolio 임에는 변함 없으므로 collision 으로 처리.

- 펀드 종류 태그: `_partners`, `_smallcap`, `_global` (Hawkins) — 같은 firm 다른 mandate
- 운용사/Entity 변경: `_amg` (Yacktman: AMG 인수 전후) — 포트폴리오 본질은 같음
- Filing month: `_jan`, `_feb`, `_mar`, ..., `_dec` — 다중 펀드 / amendment
- Accession suffix: `_a000074` 등 — SEC 등록 번호 끝자리

---

## INV_BUFFETT — Warren Buffett

### 수집된 자료
Berkshire Hathaway 주주 서한(annual chairman's letter) 전체 시계열. 회장 직접 서명, 회사 공식 페이지에서 1977년부터 매년 1회 발행.

### 파일 형식 / 출처
- **1977-1997 (21개)**: HTML 직접 본문 — `https://www.berkshirehathaway.com/letters/{YYYY}.html`
- **1998-2003 (6개)**: HTML stub(1KB) → 실제 본문 PDF (`{YYYY}pdf.pdf` 또는 `final{YYYY}pdf.pdf` 변형)
- **2004-2024 (21개)**: PDF — `{YYYY}ltr.pdf`

### Cadence
**연간 (annual only)**. Berkshire 는 분기 letter 를 발행하지 않음. 분기 cadence 는 native 부재.

### 저장 위치
[data/raw/buffett/](buffett/) — 48 letter (Buffett_77~Buffett_24) + 6 stub HTML (Buffett_98_stub~Buffett_03_stub)

### 분기 데이터 확보를 위한 추가 단계
1. **Carry-forward (가장 간단)**: 연간 letter 를 그 해의 4개 분기에 동일하게 적용. Persona 가 1년 단위로 변하는 가정 → Phase 2 GRU 의 분기 시계열엔 동일 입력 4번 반복.
2. **AGM Q&A transcript 보충** (PLAN.md §2 표에서 명시): Berkshire 연차 주주총회(매년 5월) Q&A 녹취록을 추가 수집 — wisdomvalue.com / brkletters.com 등 fan archive
3. **분기 13F 발표 시점 인터뷰 보충**: CNBC/Yahoo finance archive

**권장**: 1번 (carry-forward) + 2번 (AGM transcript) 조합.

---

## INV_HAWKINS — Mason Hawkins (Southeastern / Longleaf Partners)

### 수집된 자료
Longleaf Partners Funds (Partners / Small-Cap / International / Global) 의 shareholder letter 전체 시계열. 사이트와 SEC EDGAR 두 채널 병행 수집.

### 파일 형식 / 출처

**채널 1 — Southeastern 사이트** (57 PDFs, 23 MB)
- **2007~2021 (16 PDFs)**: 일부 분기만 (Q1+Q3 위주) — `https://southeasternasset.com/report/{q}q{yy}-quarterly-fund-report/` → 합본 PDF (4개 펀드)
  - 파일명: `Hawkins_07_Q1.pdf`, `Hawkins_19_Q1.pdf` 등
- **2022-Q4 ~ 2026-Q1 (39 PDFs)**: 분기 cadence, 펀드별 분리 — `https://southeasternasset.com/commentary/{q}q{yy}-{partners|small-cap|global}-fund-commentary/`
  - 파일명: `Hawkins_22_Q4_partners.pdf`, `Hawkins_22_Q4_smallcap.pdf`, `Hawkins_22_Q4_global.pdf`

**채널 2 — SEC EDGAR Longleaf Partners Funds Trust (CIK 0000806636)** (68 docs, 57 MB)
- **1996-02 ~ 2002-07 (18 TXT)**: N-30D / N-30D/A — pre-Sarbanes-Oxley 양식, plain text
  - 파일명: `Hawkins_95.txt` (annual), `Hawkins_96_S1.txt` (semi-annual)
- **2002-07 (1 HTM)**: N-30D, HTML 양식 전환 시작
- **2003-02 ~ 2026-03 (49 HTM)**: N-CSR (annual, 매년 2월) + N-CSRS (semi-annual, 매년 8월). 4개 펀드 합본 + financial statements + holdings 모두 단일 HTML 에 embedded. "To Our Shareholders" 섹션이 letter 본문.
  - 파일명: `Hawkins_22.htm` (FY2022 annual), `Hawkins_22_S1.htm` (H1 2022 semi-annual)
  - Collision: 2007-08 + 2008-02 (FY 변경기) → 두 번째는 `Hawkins_07_feb.htm`

### Cadence

| 기간 | Native cadence | 출처 |
|---|---|---|
| 1995-2002 | 반기 (Feb + Aug N-30D) | EDGAR |
| 2003-2021 | 반기 (Feb N-CSR + Aug N-CSRS) | EDGAR (사이트엔 일부만) |
| 2022 Q4 ~ | 분기 (per-fund 분리) | 사이트 |

**중요**: 2014-2021 사이의 사이트 listing 갭은 EDGAR 채널이 모두 메움. **누락 분기 없음**.

### 저장 위치
[data/raw/hawkins/](hawkins/) — 사이트 PDF + EDGAR HTML/TXT, **flat layout** (이전 `edgar/` subfolder 폐지)

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward** (1995-2021): Feb letter (= 12-31 기준 annual report) 를 직전 Q4 + 다음 Q1 에 적용, Aug letter (= 6-30 기준 semi-annual) 를 그 해 Q2 + Q3 에 적용
2. **펀드 합본 vs 분리 결정** (2022~): Partners/Small-Cap/Global 분기 letter 가 펀드별로 분리되어 있음
3. **N-CSR HTML 에서 letter 섹션만 추출** (text_cleaner.py 작업): "To Our Shareholders" 섹션 시작점부터 다음 헤딩까지 추출. financial statements / holdings table 은 제외

---

## INV_GRANTHAM — Jeremy Grantham (GMO)  ⚠️ 부분 수집

### 수집된 자료
GMO research-library 의 분기 letter PDF. 두 가지 출처 결합:
1. **sitemap.xml 등재 landing page** → landing 에서 PDF 추출 (시그니처 essay 포함)
2. **PDF URL 패턴 brute-force** ([scripts/_grantham_brute.py](../../scripts/_grantham_brute.py)) — `gmo-quarterly-letter_{q}q{yy}.pdf` 패턴으로 직접 시도

### 파일 형식 / 출처
- **GMO 분기 letter** PDF — `https://www.gmo.com/globalassets/articles/quarterly-letter/{YYYY}/{slug}.pdf`
- 두 패턴:
  - 정형: `gmo-quarterly-letter_{q}q{yy}` → `Grantham_17_Q1.pdf` 등
  - 자유 slug (시그니처 essay): `up-at-night`, `tariffs-...`, `race-of-our-lives` 등 → `Grantham_24_Q2_bargain.pdf` 같이 라벨 보존

### Cadence + 커버리지
**분기 native, 단 sitemap 등재 분량 + brute-force 가능 분량 만**:

| 연도 | 수집 분기 | 비고 |
|---|---|---|
| 2008 | _globalbubble | 시그니처 essay |
| 2009 | _purgatory | 시그니처 essay |
| 2010 | Q2 | Q1, Q3, Q4 누락 |
| 2011-2016 | 없음 | URL 패턴이 다른 시기 — Wayback Machine 조사 필요 |
| 2017 | Q1, Q2, Q3, Q4 + _stalin | full + 시그니처 |
| 2018 | Q1, Q2, Q4 | Q3 누락 |
| 2019 | Q1, Q2, Q3 | Q4 누락 |
| 2020 | Q1, Q2, Q3 | Q4 누락 |
| 2021 | Q1-Q4 | full |
| 2022 | Q1-Q4 | full |
| 2023 | Q1, Q3, Q4 | Q2 누락 |
| 2024 | Q1, Q2 (+_bargain), Q4 (+_trade Q3 시그니처) | |
| 2025 | Q1 (+_tariffs 별도), Q2 (+_unexcept 별도), Q3, Q4 | |
| 2026 | Q1 + _bubble | |

### 저장 위치
[data/raw/grantham/](grantham/) — 38 PDF, 17 MB

### 분기 데이터 확보를 위한 추가 단계 (gap 보완)
1. **Wayback Machine archive**: 2011-2016 letter 들이 archive.org 에 보존되어 있을 가능성 → `wayback_machine_downloader` 또는 직접 API 호출
2. **GMO white paper / Insights 추가**: research-library 의 다른 문서들 (`{slug}_insights/` 등) 도 Grantham 본인 저술 가능 — sitemap 추가 검색 필요
3. **Playwright 동적 렌더링**: 자유 slug 페이지의 `<meta article:published_time>` 가 JS로 주입되는 케이스 → `mcp__playwright__browser_navigate` 로 렌더 후 추출
4. **PDF metadata 에서 날짜 추출**: 다운로드한 PDF 자체의 `/CreationDate` 에서 발간 시점 식별 후 분기 매핑 (text_cleaner.py 단계)

---

## INV_DRIEHAUS — Richard Driehaus (Driehaus Capital Mgmt) ✅

### 수집된 자료
Driehaus Mutual Funds (CIK 0001016073) 의 N-CSR / N-CSRS / N-30D 시계열. 1996-08 ~ 2025-09 의 모든 shareholder report.

### 파일 형식 / 출처
- **EDGAR Driehaus Mutual Funds (CIK 0001016073)** — N-CSR/N-CSRS/N-30D HTML 또는 TXT
  - 파일명: `Driehaus_25.htm` (FY2025 annual), `Driehaus_25_S1.htm` (H1 2025 semi-annual)
  - 일부 collision: `Driehaus_21_may.htm`, `Driehaus_09_mar.htm` (다른 fiscal-year-end 펀드)

### Cadence
**반기** (annual N-CSR + semi-annual N-CSRS)
- 1996-2025: 매년 2건 (Feb annual + Aug/Sep semi-annual)
- Pre-2003: N-30D plain text

### 저장 위치
[data/raw/driehaus/](driehaus/) — 65 HTML/TXT, 142 MB

### Note: Richard Driehaus 본인 vs 펀드 매니저
Richard Driehaus 본인은 **2021년 사망**. 사후 letter 는 Jeff James 등 후임 펀드 매니저 명의. 2021-2025 letter 는 Driehaus Capital "house style" 은 유지하지만 본인 시그널은 아님 → text_cleaner.py / Role 4 단계에서 cutoff 정책 결정 필요 (예: 2021 이전만 사용).

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward** (Hawkins 와 동일)
2. **N-CSR 본문에서 manager letter 섹션 추출** — Driehaus 의 N-CSR 도 다중 펀드 합본
3. **Gap 보완**: 1995년 이전 (Driehaus Capital Mgmt 1982 설립) 은 EDGAR 미보존, 사이트 (Cloudflare 차단) 또는 archive.org 시도

---

## INV_EINHORN — David Einhorn (Greenlight Capital)  ❌ 사실상 부재

### 수집된 자료
Greenlight Capital Re Ltd (GLRE, CIK 0001385613) 의 8-K 첨부 EX-99 중 letter-style 문서 best-effort. 167건의 8-K 중 의미있는 letter 발견은 2건뿐.

### 파일 형식 / 출처
- **EDGAR GLRE 8-K EX-99 첨부**:
  - `Einhorn_20_exhibit991glrexpress.htm` (10 KB)
  - `Einhorn_21_bdoletteroct42021.htm` (2 KB)

### 한계 — 왜 letter 가 없나
Greenlight Capital LP (헷지펀드) 의 LP letter 는 **공개 출처가 없음**:
- 자체 사이트 letter 페이지 부재
- 3rd-party archive (hedgefundalpha.com, valuewalk.com) 는 Cloudflare 차단 → Playwright 필수
- Greenlight Capital Re (GLRE 상장 reinsurer) 는 별도 비즈니스, Einhorn 본인 letter 가 부속되는 경우 드뭄

### 저장 위치
[data/raw/einhorn/](einhorn/) — 2 HTML, 16 KB

### 분기 데이터 확보를 위한 추가 단계 (블로킹)
1. **Playwright 로 hedgefundalpha 우회** — Cloudflare challenge 해결 후 D. Einhorn category page 의 letter PDF 링크 일괄 다운로드. 약 10년 분기 letter 확보 예상
2. **valuewalk archive scrape** — 동일 메커니즘
3. **Twitter/X scrape** — Einhorn (@davidein) 트윗 archive (분기 letter 발표 후 발췌가 자주 등장)
4. **GLRE 10-K Item 7 (MD&A)** — 분기 trading commentary 가 첨부되는 경우 추출 (보유: 167 8-K 중 미발견)

**현재 Einhorn 은 PLAN §2 의 "분기 letter (third-party archive 통한)" 가 사실상 부재 상태로 운영 → 모델 학습량 매우 부족**. Long/Short Fundamental 카테고리 유지 여부 재논의 필요.

---

## INV_BARON — Ron Baron (Baron Capital / BAMCO) ✅

### 수집된 자료
Baron Investment Funds Trust (CIK 0000810902, formerly Baron Asset Fund) + Baron Capital Funds Trust (CIK 0001050084) 양 trust 의 N-CSR / N-CSRS / N-30D 시계열.

### 파일 형식 / 출처
- **EDGAR Baron Investment Funds Trust** (CIK 0000810902) + **Baron Capital Funds Trust** (CIK 0001050084) — N-CSR/N-CSRS/N-30D
- 1996-2025 연도별 반기 (Feb annual + Aug semi-annual)
- 일부 collision: `Baron_05_mar.txt`, `Baron_03_mar.txt`, `Baron_06_maya000094.txt` (FY 변경기 / 시리즈 분리)

### Cadence
**반기** (annual + semi-annual)

### 저장 위치
[data/raw/baron/](baron/) — 76 HTML/TXT, 125 MB

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward** (Hawkins 와 동일)
2. **Baron Investment Conference keynote transcript** — 매년 10월/11월 (Ron Baron 본인 발표) → 별도 추가 수집 (YouTube + Baron 사이트). PLAN §2 의 보충 텍스트
3. **펀드별 letter 분리** — Baron Growth / Baron Partners / Baron Small-Cap 등 11개 펀드의 N-CSR 합본에서 펀드별 letter 추출 필요

---

## INV_YACKTMAN — Don Yacktman ✅ 1995-2025 (full coverage)

### 수집된 자료
두 entity 결합:
1. **Yacktman Fund Inc (CIK 0000885980)** — 1995년 ~ 2011년 (17년 standalone)
2. **AMG FUNDS (CIK 0001089951)** — 2012년 ~ 2025년 (AMG 인수 후, 다른 fund 와 합본 N-CSR)

### 파일 형식 / 출처
- **EDGAR Yacktman Fund Inc (1995-2011)**:
  - 파일명: `Yacktman_95.txt`, `Yacktman_95_S1.txt` (annual + semi-annual)
- **EDGAR AMG FUNDS (2012-2025)**:
  - 파일명: `Yacktman_22_amg.htm`, `Yacktman_22_S1_amg.htm` 등 — `_amg` 태그 로 출처 구분
  - **N-CSR 본문은 AMG fund family 합본**이라 Yacktman 섹션을 별도로 추출 필요 (text_cleaner.py 단계)

### Filter 정책
스크래퍼는 `min_filing_year=2012` 로 AMG entity 의 pre-2012 N-CSR 제외 (Yacktman 인수 전 무관 fund 만 포함). **AMG 인수 시점 검증**: 2012년 3월 이전 AMG N-CSR 에 "yacktman" 문자열 0건 → cutoff 합당.

### Cadence
**반기** (annual + semi-annual)

### 저장 위치
[data/raw/yacktman/](yacktman/) — 127 HTML/TXT, 266 MB
- 31 standalone (1995-2011, 2 docs/year)
- 96 AMG-era (2012-2025, 다중 N-CSR — 각 series 별로)

### Note: Don Yacktman 본인 vs AMG era
PLAN.md §2 의 "Don Yacktman 은 2016년 은퇴" — AMG 시기 중 2012-2016 은 Don Yacktman 직접 운용, 2016 이후는 Stephen Yacktman / Jason Subotky 공동 운용. Persona 분석 시 **2016 cutoff** 권장.

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward** (Hawkins 와 동일)
2. **AMG N-CSR 에서 Yacktman-specific 섹션만 추출** — text_cleaner.py 가 "Yacktman Focused Fund" 또는 "Yacktman Fund" 헤더 기반으로 Slice
3. **2016 cutoff 적용 결정**: Role 4 합의 후 본인-only 모드와 후임 포함 모드 분리

---

## Aggregate Stats

```
Buffett                  54 files (48 letters + 6 stubs)         8.9  MB  1977-2024
Hawkins                 125 files (57 site PDF + 68 EDGAR)      82    MB  1995-2026
Grantham                 38 files (PDF — 26 sitemap + 12 brute)  17    MB  2008-2026
Driehaus                 65 files (HTML/TXT EDGAR)             142    MB  1996-2025
Einhorn                   2 files (GLRE 8-K best-effort)         0.02 MB  2020-2021
Baron                    76 files (HTML/TXT EDGAR)             125    MB  1996-2025
Yacktman                127 files (31 own + 96 AMG-era)        266    MB  1995-2025
                         ──────────────────────────────────────────────────
                        487 files                              641    MB
```

`.gitignore` 처리되어 commit 안됨. 본 `raw-progress.md` 만 화이트리스트 (`data/raw/raw-progress.md`) 로 commit.

---

## Next Steps (priority order)

1. **Role 4 와 메타데이터 스키마 합의** (PLAN §9 step 3, 블로킹) — 특히 cadence 가 mixed (annual / semiannual / quarterly / 비정형) 인 점 반영해 `source_type` 어휘 + `chunk_id` 의미 + 펀드별 분리 정책 확정
2. **text_cleaner.py 파일럿** — N-CSR HTML 에서 "To Our Shareholders" / manager letter 섹션 추출. PDF→텍스트, 헤더/푸터 제거 → `data/interim/{investor}_{quarter}.xlsx`
3. **Grantham gap 보완** (MEDIUM) — 2011-2016 letter 들 Wayback Machine 또는 Playwright 로 추가. 현재 38 letter 로도 2017-2026 + 2008-2010 부분 커버
4. **Einhorn 우회 수집** (BLOCKING) — Playwright + Cloudflare 우회로 hedgefundalpha 또는 valuewalk archive 접근 시도. 실패 시 PLAN.md 카테고리 재논의
5. **AMG N-CSR 에서 Yacktman 섹션 추출** — 2012-2025 의 96 AMG 합본 N-CSR 에서 Yacktman-specific 부분만 slice (text_cleaner.py 단계)
6. **분기 cadence alignment 정책 확정** — 반기 → 분기 mapping 규칙을 text_tagger.py 단계에서 일괄 적용

---

## Reproducibility

수집은 다음 스크립트 조합으로 idempotent:
- [scripts/text_scraper.py](../../scripts/text_scraper.py) — 7명 통합 스크래퍼
- [scripts/_naming.py](../../scripts/_naming.py) — 명명 helper
- [scripts/_rename_existing.py](../../scripts/_rename_existing.py) — 마이그레이션 (1회용)
- [scripts/_grantham_brute.py](../../scripts/_grantham_brute.py) — Grantham PDF URL brute-force 보강
- [scripts/_renormalize_edgar.py](../../scripts/_renormalize_edgar.py) — collision suffix → sequence 번호 정규화

```bash
cd 2026-AIFinance-Project/TextData-Processing

# 신규 수집 (인자 없으면 7명 모두)
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py buffett hawkins
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py grantham         # GMO sitemap-driven
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py driehaus baron yacktman  # EDGAR
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py einhorn          # GLRE 8-K best-effort

# Grantham brute-force 추가 수집 (PDF URL 직접 패턴 매칭)
PYTHONIOENCODING=utf-8 python scripts/_grantham_brute.py

# 명명규칙 마이그레이션 (1회 실행 후 끝)
python scripts/_rename_existing.py --dry-run  # 미리보기
python scripts/_rename_existing.py            # 실제 rename

# Collision suffix → sequence 번호 정규화 (Baron/Driehaus/Yacktman/Hawkins)
python scripts/_renormalize_edgar.py --dry-run
python scripts/_renormalize_edgar.py
```

이미 다운로드된 파일은 자동 skip. SEC EDGAR 호출은 정책 준수 UA + 0.3s rate-limit 적용 (10 req/s 제한 안에서 운용).

Windows 환경에서는 `PYTHONIOENCODING=utf-8` 필요 (cp949 콘솔 인코딩 회피).
