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
| 3 | **Grantham** | ⚠️ 부분 수집 | 2008~2026 (sparse) | 분기 letter (sitemap 한정) | PDF(gmo.com) | 26 | 8.6 MB |
| 4 | **Driehaus** | ✅ 수집 완료 | 1996~2025 (30y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 65 | 142 MB |
| 5 | **Einhorn** | ❌ 사실상 부재 | 2020-2021 (2건) | 비정형 (GLRE 8-K best-effort) | HTML(EDGAR) | 2 | 16 KB |
| 6 | **Baron** | ✅ 수집 완료 | 1996~2025 (30y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 76 | 125 MB |
| 7 | **Yacktman** | ⚠️ 2011 cutoff | 1995~2011 (17y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 31 | 17 MB |

**Aggregate**: 379 파일 / ~381 MB (전체 7명 1차 수집 완료)

---

## 명명규칙 (전체 공통)

```
{Investor}_{YY}                       # 연간                 (Buffett_77.html)
{Investor}_{YY}_Q{n}                  # 분기                 (Hawkins_22_Q1.pdf)
{Investor}_{YY}_S{n}                  # 반기                 (Hawkins_96_S1.txt)
{Investor}_{YY}_Q{n}_{tag1}_{tag2}    # 분기 + 펀드/세부태그  (Hawkins_22_Q4_partners.pdf)
{Investor}_{YY}_{tag}                 # 연간 + 라벨           (Grantham_08_globalbubble.pdf)
{Investor}_{YY}_{month}               # collision 회피용      (Hawkins_07_feb.htm)
{Investor}_{YY}_a{accession}          # 동일 date 다중 필링   (Hawkins_95_a000298.txt)
```

연도는 **컨텐츠 연도** (보고 대상 fiscal period).
- N-CSR 2023-02 발간 → FY2022 보고 → `Hawkins_22.htm`
- N-CSRS 2023-08 발간 → H1 2023 → `Hawkins_23_S1.htm`
- N-30D 1996-02 발간 → FY1995 → `Hawkins_95.txt`
- N-30D 1996-07 발간 → H1 1996 → `Hawkins_96_S1.txt`

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
GMO research-library 의 분기 letter PDF. **gmo.com sitemap.xml 에 등재된 letter 만 자동 수집 가능**.

### 파일 형식 / 출처
- **GMO 분기 letter** (`https://www.gmo.com/americas/research-library/{slug}_gmoquarterlyletter/`) — landing page 에서 PDF 링크 추출 후 다운로드
- 2개 패턴:
  - 정형: `{q}q-{yyyy}-gmo-quarterly-letter` (e.g. 1q-2010, 1q-2023)
  - 자유 slug (시그니처 essay): `race-of-our-lives`, `up-at-night`, `tariffs-...` 등 — 본 스크래퍼는 slug 에서 year/quarter 추출 못 하면 SKIP

### Cadence + 커버리지
**분기 native, 단 sitemap 등재 분량만**:

| 연도 | 수집 분기 | 비고 |
|---|---|---|
| 2008 | (named: globalbubble) | 이름 기반 |
| 2009 | (named: purgatory) | 이름 기반 |
| 2010 | Q2 only | 정형 slug 다수 누락 |
| 2011-2016 | 없음 | sitemap 미등재 |
| 2017 | (named: stalin) | 이름 기반 |
| 2018 | Q1, Q2 | Q3, Q4 누락 |
| 2019 | Q1, Q2, Q3 | Q4 누락 |
| 2020 | Q1, Q2, Q3 | Q4 누락 |
| 2021 | Q1-Q4 | full |
| 2022 | Q1-Q4 | full |
| 2023 | Q1 only | 나머지 누락 |
| 2024 | Q2 (bargain), Q3 (trade) | 시그니처 명만 |
| 2025 | Q1 (tariffs), Q2 (unexcept) | 시그니처 명만 |
| 2026 | Q1 (bubble) | |

### 저장 위치
[data/raw/grantham/](grantham/) — 26 PDF, 8.6 MB

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

## INV_YACKTMAN — Don Yacktman ⚠️ 2011 cutoff

### 수집된 자료
Yacktman Fund Inc (CIK 0000885980) 의 N-CSR / N-CSRS / N-30D 시계열 — **1995년 ~ 2011년 (17년)**.

### 파일 형식 / 출처
- **EDGAR Yacktman Fund Inc (CIK 0000885980)** — N-CSR/N-CSRS/N-30D
- 1995-2011 연도별 반기

### Cadence
**반기**

### 저장 위치
[data/raw/yacktman/](yacktman/) — 31 HTML/TXT, 17 MB

### Note: 2012 이후 cutoff
Yacktman Fund Inc (CIK 885980) 는 **2012년 3월 이후 N-CSR 필링 중단**. AMG (Affiliated Managers Group) 가 운용사를 인수하면서 fund 가 AMG family 의 다른 trust 로 reorganize 된 것으로 추정 (현재 AMG Funds I/III/IV 후보 중 하나에 통합되었을 가능성).

PLAN.md §2 의 "1992~ (30y) 13F" 와 모순되지 않음 (asset management firm 수준 13F 는 별도 entity = CIK 0000874118 에서 계속). 다만 **mutual fund letter** 는 2011 cutoff. 이 시기 이후 Yacktman 의 voice 는 Stephen Yacktman (아들) / Jason Subotky 공동 운용 시기로 들어감.

### 분기 데이터 확보를 위한 추가 단계
1. **AMG fund family 후속 entity 식별** (TODO): AMG Funds Yacktman Focused Fund (현재) 의 정확한 CIK 추적 → 2012-2025 letter 보충
2. **2025-04-30 시점에는 1995-2011 만으로 진행** — Don Yacktman 본인 shareholder letter signature 시기에 부합

---

## Aggregate Stats

```
Buffett                  54 files (48 letters + 6 stubs)         8.9  MB  1977-2024
Hawkins                 125 files (57 site PDF + 68 EDGAR)      82    MB  1995-2026
Grantham                 26 files (PDF, sparse)                  8.6  MB  2008-2026
Driehaus                 65 files (HTML/TXT EDGAR)             142    MB  1996-2025
Einhorn                   2 files (GLRE 8-K best-effort)         0.02 MB  2020-2021
Baron                    76 files (HTML/TXT EDGAR)             125    MB  1996-2025
Yacktman                 31 files (HTML/TXT EDGAR)              17    MB  1995-2011
                         ──────────────────────────────────────────────────
                        379 files                              381    MB
```

`.gitignore` 처리되어 commit 안됨. 본 `raw-progress.md` 만 화이트리스트 (`data/raw/raw-progress.md`) 로 commit.

---

## Next Steps (priority order)

1. **Role 4 와 메타데이터 스키마 합의** (PLAN §9 step 3, 블로킹) — 특히 cadence 가 mixed (annual / semiannual / quarterly / 비정형) 인 점 반영해 `source_type` 어휘 + `chunk_id` 의미 + 펀드별 분리 정책 확정
2. **text_cleaner.py 파일럿** — N-CSR HTML 에서 "To Our Shareholders" / manager letter 섹션 추출. PDF→텍스트, 헤더/푸터 제거 → `data/interim/{investor}_{quarter}.xlsx`
3. **Grantham gap 보완** (HIGH) — Wayback Machine 또는 Playwright 로 2011-2016 + 일부 누락 분기 letter 보충
4. **Einhorn 우회 수집** (BLOCKING) — Playwright + Cloudflare 우회로 hedgefundalpha 또는 valuewalk archive 접근 시도. 실패 시 PLAN.md 카테고리 재논의
5. **Yacktman AMG era 통합** (LOW) — 2012-2024 letter 가 정말 필요한지 결정 후 AMG fund CIK 추적
6. **분기 cadence alignment 정책 확정** — 반기 → 분기 mapping 규칙을 text_tagger.py 단계에서 일괄 적용

---

## Reproducibility

수집은 [scripts/text_scraper.py](../../scripts/text_scraper.py) 단일 스크립트 + [scripts/_naming.py](../../scripts/_naming.py) 명명 helper + [scripts/_rename_existing.py](../../scripts/_rename_existing.py) 마이그레이션 (1회용) 로 idempotent.

```bash
cd 2026-AIFinance-Project/TextData-Processing

# 신규 수집 (인자 없으면 7명 모두)
python scripts/text_scraper.py
python scripts/text_scraper.py buffett hawkins
python scripts/text_scraper.py grantham                # GMO sitemap-driven
python scripts/text_scraper.py driehaus baron yacktman # EDGAR
python scripts/text_scraper.py einhorn                 # GLRE 8-K best-effort

# 명명규칙 마이그레이션 (1회 실행 후 끝)
python scripts/_rename_existing.py --dry-run  # 미리보기
python scripts/_rename_existing.py            # 실제 rename
```

이미 다운로드된 파일은 자동 skip. SEC EDGAR 호출은 정책 준수 UA + 0.3s rate-limit 적용 (10 req/s 제한 안에서 운용).
