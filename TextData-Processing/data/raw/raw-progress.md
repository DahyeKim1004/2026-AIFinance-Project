# Role 1 — Raw Data Collection Progress

> **Last updated**: 2026-04-30 (Phase 2 — 시계열 누락 검증 완료)
> **Scope**: PLAN.md §2 의 7명 투자자 텍스트 코퍼스 수집 진행 현황 + 분기 정렬을 위한 추가 작업 정의.
> **Storage policy**: 본 파일을 제외한 `data/raw/` 하위 모든 파일은 `.gitignore` 처리. 무거운 원본은 commit 되지 않음.
> **Naming**: PLAN §7 규칙 — `{Investor}_{YY}` (annual), `{Investor}_{YY}_Q{n}` (quarterly), `{Investor}_{YY}_S{n}` (semi-annual), `{Investor}_{YY}_Q{n}_{tag}` (per-fund/세부 태그).

---

## TL;DR — 7명 진행률

| # | Investor | 상태 | 시계열 커버 | Native cadence | 주요 파일 형식 | 파일 수 | 디스크 |
|---|---|---|---|---|---|---|---|
| 1 | **Buffett** | ✅ 수집 완료 | 1977~2024 (48y) | 연간 | HTML(1977-1997) + PDF(1998-2024) | 48 | 8.8 MB |
| 2 | **Hawkins** | ✅ 수집 완료 | 1995~2026 (32y) | 1995-2021 반기 → 2022~ 분기 | PDF(site) + HTML/TXT(EDGAR) | 125 | 81 MB |
| 3 | **Grantham** | ✅ 수집 완료 | 2007~2026 (20y, gap 2016만) | 분기 letter + 시그니처 essay | PDF(gmo.com + Wayback) | 77 | 38 MB |
| 4 | **Driehaus** | ✅ 수집 완료 | 1996~2025 (30y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 65 | 141 MB |
| 5 | **Einhorn** | ⚠️ 부분 수집 | 2012-2024 (시그니처/proxy 위주) | 비정형 (Sohn/Robin Hood 발표 + activist letter) | HTML(EDGAR) + PDF(Wayback) | 29 | 124 MB |
| 6 | **Baron** | ✅ 수집 완료 | 1996~2025 (30y) | 반기 (N-CSR/N-CSRS) | HTML/TXT(EDGAR) | 75 | 123 MB |
| 7 | **Yacktman** | ✅ 수집 완료 | 1995~2025 (30y) | 1995-2011 + 2012-2025 (운용사 변경) | HTML/TXT(EDGAR) | 129 | 265 MB |

**Aggregate**: 548 파일 / ~781 MB (전체 7명 수집 완료, Phase 2 시계열 누락 검증 + 보강 완료)

> **확장 이력**: 1차 379 → 487 → 526 → 520 → 518 → 544 → 548 파일
> - Grantham 26 → 38 → 75 → 77 (gmo.com brute-force + Wayback Machine + 2026-04-30 시그니처 essay 보강)
> - Einhorn 2 → 28 → 29 (greenlightcapital.com 자체 도메인 Wayback fallback)
> - Yacktman 31 → 127 → 129 (AMG FUNDS CIK 1089951 추가 + 2026-04-30 1차 1995-2011 standalone gap 보완)
> - Baron 76 → 75 (2026-04-30 Phase 2: 5 internal duplicate 제거 + 4 truly new + 13 cross-bucket dup 제거 + 3 bucket misclassification 수정)
> - 2026-04-30: Baron/Driehaus/Yacktman/Hawkins 의 month/accession/per-fund collision suffix → 시점 bucket + sequence 번호 로 정규화
> - 2026-04-30: Buffett stub HTML 6개 삭제 (PDF redirect 페이지, 텍스트 내용 0); Yacktman `_amg` 태그 제거 (포트폴리오 본질 동일)
> - 2026-04-30 **Phase 2** (시계열 누락 검증): Grantham +2 시그니처 essay (Race of Our Lives Revisited 2018-08, Waiting for the Last Dance 2021-01); Yacktman +2 (FY2000 + H1 2000 N-30D, 1차 누락); Baron net -1 (renormalize 단계 의 5 internal duplicate + 13 cross-bucket dup 제거 + 4 truly new 추가); GMO 비발행 분기 4건 (2018 Q3 / 2019 Q4 / 2020 Q4 / 2023 Q2) 직접 URL 404 검증 완료

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

## INV_GRANTHAM — Jeremy Grantham (GMO)  ✅ 수집 완료

### 수집된 자료
GMO 분기 letter + Grantham 시그니처 essay 시계열 (2007-2026). 세 채널 조합:
1. **sitemap.xml 등재 landing page** → landing 에서 PDF 추출 (시그니처 essay 포함)
2. **PDF URL 패턴 brute-force** ([scripts/_grantham_brute.py](../../scripts/_grantham_brute.py)) — `gmo-quarterly-letter_{q}q{yy}.pdf` 정형 패턴
3. **Wayback Machine archive** ([scripts/_grantham_wayback.py](../../scripts/_grantham_wayback.py)) — GMO 옛 URL 구조 (2008-2017) 가 사이트에서 제거됐으나 archive.org에 보존. CDX API 로 발굴 후 Wayback `id_/` raw proxy 로 다운로드

### 파일 형식 / 출처

**채널 1 — GMO 현행 사이트** (`/globalassets/articles/quarterly-letter/{YYYY}/`)
- 정형 slug: `gmo-quarterly-letter_{q}q{yy}.pdf` → `Grantham_17_Q1.pdf` 등 (2017+)
- 자유 slug (시그니처 essay): `up-at-night`, `race-of-our-lives`, `tariffs-...` 등

**채널 2 — Wayback Machine 발굴** (현재 GMO 사이트에 없음)
- `gmo.com/websitecontent/JGLetter_*.pdf` (2008-2014): 옛 단순 경로
- `gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=N` (2015 Q2 ~ 2017 Q2): GMO가 같은 URL 에 분기마다 letter 덮어쓰면서 캐시버스터 `sfvrsn=N` 만 증가시킨 시기. 9개 unique digest = 9개 letter
- `gmo.com/globalassets/articles/quarterly-letter/2007|2012|2013|2014/` 시그니처 essay 4개

**sfvrsn → 분기 매핑** (PDF 첫 페이지 헤더로 자동 식별, [pypdf](../../scripts/) 사용)

| sfvrsn | 분기 | 처리 |
|---|---|---|
| 7 | 2Q 2015 | → `Grantham_15_Q2.pdf` |
| 14 | 3Q 2016 | → `Grantham_16_Q3.pdf` |
| 18 | 4Q 2015 | → `Grantham_15_Q4.pdf` |
| 20 | 3Q 2015 | → `Grantham_15_Q3.pdf` |
| 38 | 4Q 2016 | → `Grantham_16_Q4.pdf` |
| 8/26/28/36/42/44/46 | 다른 sfvrsn 과 SHA-1 중복 또는 기존 보유 letter 와 동일 | DELETE |
| 32 | 미상 (1Q-2Q 2016 추정) | Wayback archive 자체가 truncated (524288 bytes) → 영구 손실 |

### Cadence + 커버리지

**분기 native + 시그니처 essay**. 최종 77 PDF.

| 연도 | 수집 분기 letter | 시그니처 essay | 비고 |
|---|---|---|---|
| 2007 | — | `everywhere` (4Q07 cover) | |
| 2008 | Q2, Q3, Q4 | `globalbubble` (1Q08 cover) | Q1 letter 는 globalbubble essay 로 publish |
| 2009 | Q1, Q2, Q3, Q4 | `Q1_terrified` (Reinvesting When Terrified) | |
| 2010 | Q1, Q2, Q3 (`nightoflivingfed`), Q4 (`pavlovsbulls`) | — | full |
| 2011 | Q1, Q1 (`part2`), Q2 (`danger` + `resources`), Q3 (`shortest`), Q4 (`longest`) | — | full |
| 2012 | Q1, Q2, Q3 | `sisterspension` (My Sister's Pension, 2012-04) | full |
| 2013 | Q1, Q2, Q3, Q4 | `raceofourlives` (The Race of Our Lives) | full |
| 2014 | Q1, Q2, Q3, Q3 (`purgatoryorhell`), Q4 | — | full |
| 2015 | Q1, Q2, Q3, Q4 | — | full |
| 2016 | Q3, Q4 | — | **Q1, Q2 누락 (sfvrsn=32 archive truncated, 영구 손실)** |
| 2017 | Q1, Q2, Q3, Q4 | `stalin` | full + 시그니처 |
| 2018 | Q1, Q2, Q4 | `raceofourlives_revisited` (2018-08 GMO White Paper) | **Q3 분기 letter 비발행** → White Paper 가 사실상 Q3 substitute |
| 2019 | Q1, Q2, Q3 | — | **Q4 GMO 비발행** (대체 essay 도 부재) |
| 2020 | Q1, Q2, Q3 | `lastdance` (Waiting for the Last Dance, 2021-01-05 Viewpoint) | **Q4 분기 letter 비발행** → Viewpoint 가 사실상 Q4 substitute |
| 2021 | Q1, Q2, Q3, Q4 | — | full |
| 2022 | Q1, Q2, Q3, Q4 | — | full |
| 2023 | Q1, Q3, Q4 | — | **Q2 GMO 비발행** (대체 essay 도 부재) |
| 2024 | Q1, Q2 (+`bargain`), Q3 (`trade`), Q4 | — | full |
| 2025 | Q1 (`tariffs`), Q2 (`unexcept`), Q3, Q4 | — | full |
| 2026 | Q1 (`bubble`) | — | (현재 시점) |

### 비발행 분기 검증 (2026-04-30 Phase 2 보강)

**1차 검증 (Wayback Machine)**: GMO `/americas/research-library/` 페이지의 archive.org 스냅샷 (2017-2024) 에서 letter landing slug 전수 조사 → 4건 비발행.

**2차 검증 (직접 URL 404)**: 2026-04-30 GMO 사이트의 정형 quarterly-letter URL 직접 호출:
- `https://www.gmo.com/americas/research-library/3q-2018-gmo-quarterly-letter/` → **404**
- `https://www.gmo.com/americas/research-library/4q-2019-gmo-quarterly-letter/` → **404**
- `https://www.gmo.com/americas/research-library/4q-2020-gmo-quarterly-letter/` → **부재** (URL 자체 미존재)
- `https://www.gmo.com/americas/research-library/2q-2023-gmo-quarterly-letter/` → **404**

→ 4개 분기 모두 **분기 letter 비발행 확정**.

**시그니처 essay 대체본 발견 (2건 추가 수집 완료)**:
- **2018 Q3 substitute**: ["The Race of Our Lives Revisited"](https://www.gmo.com/globalassets/articles/white-paper/2018/jg_morningstar_race-of-our-lives_8-18---short-version.pdf) — Grantham GMO White Paper, 2018-08, 800 KB. → `Grantham_18_raceofourlives_revisited.pdf`. 2013 원본 ([Grantham_13_raceofourlives.pdf](grantham/Grantham_13_raceofourlives.pdf)) 의 5년 후 update 본.
- **2020 Q4 substitute**: ["Waiting for the Last Dance"](https://www.gmo.com/americas/research-library/waiting-for-the-last-dance/) — Grantham GMO Viewpoint, 2021-01-05, 177 KB. → `Grantham_20_lastdance.pdf`. Grantham 의 대표 bubble warning essay.

**진짜 침묵 분기 (대체본 없음, 영구 누락)**:
- **2019 Q4**: 시그니처 essay/Viewpoint/White Paper 모두 부재. 1Q 2020 letter 가 2020-06-04 비정상 늦게 발간된 것을 보면, 당시 GMO 의 quarterly cadence 가 COVID 직전 정체된 흔적으로 추정 (확정 사유는 GMO 측 공개 자료에 부재).
- **2023 Q2**: 1Q 2023 ("The Quality Spectrum") 와 3Q 2023 ("Beyond the Landing") 사이 letter 부재. 사유 공개 자료 부재.

**해석**: GMO 의 quarterly letter cadence 는 **strict 한 분기별 발간 의무가 아님**. Ben Inker / Grantham / John Pease 가 substantive content 가 있을 때 발간하며, 4분기 모두 발간되는 해는 오히려 일부에 그침. 시그니처 Viewpoint/White Paper 가 대체하기도 하고, 그냥 침묵하기도 함.

→ 모델 학습 관점에서 **2019 Q4, 2023 Q2 는 `null` 마커 또는 직전 분기 carry-forward** 로 처리 권장 (Phase 2 GRU 입력 시).

### 저장 위치
[data/raw/grantham/](grantham/) — 77 PDF, 38 MB

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward 불필요** (분기 native)
2. **시그니처 essay 의 source_type 분리** — `signature_essay` 어휘 (PLAN §7) 로 태깅. quarter 정렬 시 같은 분기의 표준 letter 와 별도 chunk
3. **sfvrsn=32 (1-2Q 2016) 영구 손실 수용**: Wayback CDX 에 single archived snapshot 만 있고 truncated. archive.org 에 보고 가능하나 복구 보장 없음
4. **2008 Q1 결정**: globalbubble essay 가 사실상 1Q 2008 cover (분기 letter 부재) → text_tagger.py 에서 `Grantham_08_globalbubble.pdf` 를 1Q 2008 chunk 로 매핑

### Wayback 발굴 재현 명령

```bash
cd 2026-AIFinance-Project/TextData-Processing
PYTHONIOENCODING=utf-8 python scripts/_grantham_wayback.py  # named + sfvrsn 시리즈
# 자동으로 idempotent skip — 이미 있는 dest 는 건너뜀
```

`_grantham_wayback.py` 는 hardcoded URL 목록 (CDX 발굴분) 을 Wayback `id_/` raw proxy 로 다운로드. 각 URL 마다 CDX timestamp candidate 10개 시도 → archived error page (PDF magic bytes 아님) 면 다음 후보로 fallback. 재시도 3회 + 5s exponential backoff 적용.

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

## INV_EINHORN — David Einhorn (Greenlight Capital)  ⚠️ 부분 수집 (분기 letter 부재)

### 수집된 자료

**채널 1 — EDGAR GLRE 8-K EX-99** (best-effort, 2 건)
- `Einhorn_20_exhibit991glrexpress.htm` (10 KB) / `Einhorn_21_bdoletteroct42021.htm` (2 KB)
- 167건 8-K 중 letter-style 문서 2건만 발견

**채널 2 — `greenlightcapital.com` 자체 도메인 Wayback Machine fallback** (26 PDF)
- Greenlight Capital 자체 사이트가 robots/auth wall 로 직접 접근 불가하나 archive.org 에 보존됨. CDX 발굴 → Wayback `id_/` raw proxy 다운로드 → PDF 첫 4 페이지 텍스트 + metadata + Wayback timestamp 로 자동 분류
- URL 패턴 2종: `greenlightcapital.com/{6digit}.pdf` (2013-2018 numbered ID, 12개) + `greenlightcapital.com/Download.aspx?ID={uuid}&Inline=1` (2021-2024 UUID, 7 unique URL × 다중 timestamp)

### 자동 분류 결과 (15 identified, 11 unidentified)

| # | 파일명 | 카테고리 | 시기 |
|---|---|---|---|
| 1 | `Einhorn_12_goups.pdf` | GO!UPs presentation | 2012-05 |
| 2 | `Einhorn_13_applevoting.pdf` | Apple proxy contest letter | 2013 Q1 |
| 3 | `Einhorn_14_sohn.pdf` (×2) | 19th Annual Sohn Investment Conference | 2014 |
| 4 | `Einhorn_15_grants.pdf` | Grant's Conference 발표 | 2015 |
| 5 | `Einhorn_15_sohn.pdf` | Sohn 발표 | 2015 |
| 6 | `Einhorn_17_gmproxy.pdf` | "Unlocking Value at GM: Two Classes of Common Shares" | 2017-03 |
| 7 | `Einhorn_18_sohn.pdf` | Sohn 발표 (April 23, 2018) | 2018 |
| 8 | `Einhorn_21_pillar3.pdf` (×2) | FCA Pillar 3 regulatory disclosure | 2021 |
| 9 | `Einhorn_21_sohn.pdf` (×2) | Sohn 발표 (May 12, 2021) | 2021 |
| 10 | `Einhorn_23_sohn.pdf` (×2) | Sohn 2021 archived 2023 | 2021 |
| 11 | `Einhorn_24_robinhood.pdf` | Robin Hood Investors Conference (10/23/24) | 2024 |

**Unidentified 11개** — 주로 image-only PDF (텍스트 추출 빈) 또는 시그니처 발표인데 키워드 미매칭. wayback timestamp 기반 연도 + sha 로 임시 명명 (`Einhorn_unidentified_{YYYY}_{sha}.pdf`). 사용자 수동 검수 시 분류 가능.

### Cadence — Greenlight LP partner letter 부재

**Greenlight Capital LP 의 정식 분기 letter 는 자체 archive 에 거의 없음**. 우리가 받은 26개는 letter 가 아닌:
- 시그니처 발표 (Sohn 2014/2015/2018/2021, Robin Hood 2024, GO!UPs 2012, Grant's 2015)
- Activist proxy contest letters (Apple 2013, GM 2017)
- Regulatory disclosure (FCA Pillar 3 2021)

**시도했으나 실패한 채널**:
- `hedgefundalpha.com` PDF: Wayback 0건 (robots.txt 차단으로 archive 자체 부재)
- `valuewalk.com/wp-content/uploads/`: Wayback 0건
- `tilsonfunds.com` 라이브: 301 redirect (PDF 부재)
- `csinvesting.org` Einhorn: 1 PDF (2005 March) — 단일 historical
- archive.org direct collection: 0건
- SEC EDGAR full-text (Greenlight Capital, partner letter): 0건

### 저장 위치
[data/raw/einhorn/](einhorn/) — 2 HTML + 26 PDF (15 identified + 11 unidentified) ≈ 248 MB
- staging: `_wayback_staging/` 26 PDF (재실행 idempotency 용 raw 사본, gitignored)

### 분기 데이터 확보를 위한 추가 단계
1. **Image-only PDF OCR** — 빈 텍스트 6개 PDF 는 image/scan 기반. Tesseract / pdf2image 로 OCR 후 분기 식별 가능
2. **남은 unidentified 5개 수동 검수** — `_wayback_staging/` 의 첫 페이지 texted 발췌 와 wayback timestamp 로 사용자가 직접 분류
3. **Playwright로 hedgefundalpha/valuewalk live Cloudflare 우회** — 단 Greenlight LP partner letter 가 거기에 publish 됐을 가능성 낮음 (자체 archive 에도 없음). 우선순위 ↓
4. **GLRE earnings call transcript** — Einhorn 본인 발언 추출 (Q&A 부분)
5. **Robin Hood / Sohn YouTube transcript** — Einhorn 발표 영상 transcript

**Long/Short Fundamental 카테고리 가능성 평가**: 이전 "사실상 부재" → "**시그니처/proxy/regulatory 위주, 분기 letter 없음**" 으로 갱신. 시계열 cadence 가 일정하지 않지만 (불규칙 시그니처 발표) Einhorn voice 가 담긴 텍스트 15개 확보 → 분기 GRU 입력 어렵지만 LLM persona 분석에는 활용 가능. 카테고리 유지 가부 결정은 Role 4 단계.

### Wayback 발굴 재현 명령

```bash
cd 2026-AIFinance-Project/TextData-Processing
PYTHONIOENCODING=utf-8 python scripts/_einhorn_wayback.py
# 1) staging dir 에 27 URL × Wayback raw download
# 2) PDF 첫 4 페이지 텍스트 + metadata + Wayback ts → signature/doctype/quarter 자동 분류 + rename
# 3) idempotent — staging 사본은 skip, OUT_DIR Einhorn_*.pdf 는 매 실행마다 재분류
```

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
[data/raw/baron/](baron/) — 75 HTML/TXT, 123 MB

### Phase 2 보강 (2026-04-30) — 양 trust EDGAR 비교 검증

EDGAR Baron Investment Funds Trust (CIK 810902) + Baron Capital Funds Trust (CIK 1050084) 양 trust 의 1999-2008 originals (N-CSR/N-CSRS/N-30D, amendment 제외) 38건 vs 로컬 inner FILENAME 매칭 결과:

**기존 renormalize step 의 버그 흔적 — Baron_06_S1 bucket 에 5 internal duplicate 발견** (다른 bucket 의 파일이 잘못 복사된 상태):
- `Baron_06_S1_05` (annualreport0904) == `Baron_04_01` 본판 → 삭제
- `Baron_06_S1_07` (annualreport0905) == `Baron_05` 본판 → 삭제
- `Baron_06_S1_08` (semiannualreport0305) == `Baron_04_S1_01` 본판 → 삭제
- `Baron_06_S1_01` (sarreport0306) == `Baron_05_S1_02` 본판 → 삭제
- `Baron_06_S1_02` (ar0906) == `Baron_06` 본판 → 삭제

**3건 bucket misclassification 수정** (파일 자체는 정상이지만 잘못된 bucket 에 저장된 상태):
- `Baron_06_S1_09` (ar0307, period 2007-03-31, filed 2007-06-08) → `Baron_07_S1.txt`
- `Baron_06_S1_03` (sarreport0606, period 2006-06-30, filed 2006-08-29) → `Baron_06_02.txt`
- `Baron_06_S1_06` (semiannualrpt0605, period 2005-06-30, filed 2005-08-25) → `Baron_05_04.txt`

**진짜 누락 4건 신규 다운로드** (1050084 Baron Capital Funds Trust 단독 보고분):
- `Baron_99_03.txt` (1050084 1999-08-16 N-30D, period H1 1999, 59 KB)
- `Baron_99_S1_02.txt` (1050084 2000-02-18 N-30D, period FY1999, 78 KB)
- `Baron_00.txt` (810902 2000-12-06 N-30D, period 2000-09-30, 287 KB) — H2 2000 annual bucket이 비어있던 진짜 gap
- `Baron_05_03.txt` (1050084 2005-08-25 N-CSR, period H1 2005, 61 KB)

**Net 변경**: 76 → 75 파일 (5 internal dup 제거 + 17 다운로드 - 13 cross-bucket dup = 4 truly new). 1996-2025 모든 연도 _S1 + _annual bucket cover.

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward** (Hawkins 와 동일)
2. **Baron Investment Conference keynote transcript** — 매년 10월/11월 (Ron Baron 본인 발표) → 별도 추가 수집 (YouTube + Baron 사이트). PLAN §2 의 보충 텍스트
3. **펀드별 letter 분리** — Baron Growth / Baron Partners / Baron Small-Cap 등 11개 펀드의 N-CSR 합본에서 펀드별 letter 추출 필요
4. **Scraper root cause** — `_renormalize_edgar.py` 의 collision suffix 정규화 로직이 cross-bucket 으로 동일 파일을 다중 복사한 흔적. 추후 renormalize 재실행 시 inner FILENAME 우선 매칭 도입 필요

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
[data/raw/yacktman/](yacktman/) — 129 HTML/TXT, 265 MB
- 33 standalone (1995-2011, 2 docs/year — Phase 2 에서 +2)
- 96 AMG-era (2012-2025, 다중 N-CSR — 각 series 별로)

### Phase 2 보강 (2026-04-30) — 1차 1995-2011 standalone gap 보완

**누락 발견**: raw-progress.md "31 standalone" 카운트가 사실 1년치 누락을 hide 하고 있었음 (정상 17년 × 2 = 34, 1995 첫해 1건 제외 시 33이 정상 — 31은 2000년 전체 누락을 반영한 수치).

EDGAR (CIK 0000885980) 가 보고한 2000-2001 N-30D 3건 vs 로컬 매칭:
- 2000-02-14 N-30D → `Yacktman_99_S1.txt` (이미 있음) ✓
- **2000-08-18 N-30D** (period H1 2000) → `Yacktman_00.txt` ❌ **누락 → 다운로드** (51 KB)
- **2001-02-22 N-30D** (period FY2000) → `Yacktman_00_S1.txt` ❌ **누락 → 다운로드** (65 KB)
- 2001-08-22 N-30D → `Yacktman_01.txt` (이미 있음) ✓

→ 2건 신규 추가, 1995-2025 전기간 cover (1995는 첫해 1건만 정상).

### Phase 2 검증 (2026-04-30) — AMG 2024-2025 series consolidation

**의심**: raw-progress.md TL;DR 에 2012-2018 연 8-11 파일 → 2024-2025 연 2 파일로 급감 → 데이터 손실인지 fund consolidation 인지 의심.

**검증 결과**: AMG FUNDS (CIK 0001089951) 의 2023-2026 N-CSR/N-CSRS 10건 EDGAR 보고 = 로컬 파일 (Yacktman_22_S1_01/02 + Yacktman_23_01/02 + Yacktman_23_S1_01/02 + Yacktman_24 + Yacktman_24_S1 + Yacktman_25 + Yacktman_25_S1) **완전 매칭**.

→ AMG Funds Trust 가 2024년부터 fund series 를 통합 발간하는 정책 변경. **데이터 손실 아님**.

### Note: Don Yacktman 본인 vs AMG era
PLAN.md §2 의 "Don Yacktman 은 2016년 은퇴" — AMG 시기 중 2012-2016 은 Don Yacktman 직접 운용, 2016 이후는 Stephen Yacktman / Jason Subotky 공동 운용. Persona 분석 시 **2016 cutoff** 권장.

### 분기 데이터 확보를 위한 추가 단계
1. **반기 → 분기 carry-forward** (Hawkins 와 동일)
2. **AMG N-CSR 에서 Yacktman-specific 섹션만 추출** — text_cleaner.py 가 "Yacktman Focused Fund" 또는 "Yacktman Fund" 헤더 기반으로 Slice
3. **2016 cutoff 적용 결정**: Role 4 합의 후 본인-only 모드와 후임 포함 모드 분리

---

## Aggregate Stats

```
Buffett                  48 files (HTML 1977-1997 + PDF 1998-2024)              8.8  MB  1977-2024
Hawkins                 125 files (57 site PDF + 68 EDGAR)                     81    MB  1995-2026
Grantham                 77 files (sitemap+brute + Wayback + Phase 2 essay 2건) 38    MB  2007-2026
Driehaus                 65 files (HTML/TXT EDGAR)                            141    MB  1996-2025
Einhorn                  29 files (2 GLRE 8-K + 27 greenlightcapital Wayback) 124    MB  2012-2024
Baron                    75 files (HTML/TXT EDGAR, Phase 2 cleanup+gap 보완)  123    MB  1996-2025
Yacktman                129 files (33 own + 96 AMG-era, Phase 2 +2)           265    MB  1995-2025
                         ─────────────────────────────────────────────────────────────
                        548 files                                             781    MB
```

`.gitignore` 처리되어 commit 안됨. 본 `raw-progress.md` 만 화이트리스트 (`data/raw/raw-progress.md`) 로 commit.

---

## Next Steps (priority order)

1. **Role 4 와 메타데이터 스키마 합의** (PLAN §9 step 3, 블로킹) — 특히 cadence 가 mixed (annual / semiannual / quarterly / 비정형) 인 점 반영해 `source_type` 어휘 + `chunk_id` 의미 + 펀드별 분리 정책 확정
2. **text_cleaner.py 파일럿** — N-CSR HTML 에서 "To Our Shareholders" / manager letter 섹션 추출. PDF→텍스트, 헤더/푸터 제거 → `data/interim/{investor}_{quarter}.xlsx`
3. ~~**Grantham gap 보완**~~ ✅ Wayback Machine + Phase 2 시그니처 essay 2건 추가 (38 → 75 → 77 PDF). 잔여 갭: 2016 Q1-Q2 (Wayback truncated, 영구 손실) / 2019 Q4 / 2023 Q2 (GMO 진짜 침묵 — 시그니처 substitute 부재)
4. ~~**Einhorn 우회 수집**~~ ✅ greenlightcapital.com 자체 도메인 Wayback fallback 으로 2 → 28 파일 확보 (시그니처 발표 / proxy / regulatory 위주). 진짜 분기 letter 는 여전히 부재 — 별도 cadence 정책 필요. Long/Short Fundamental 카테고리 유지 가부는 Role 4 단계에서 결정
5. ~~**Yacktman 1차 standalone 갭 (2000)**~~ ✅ Phase 2: EDGAR 직접 다운로드 2건 추가 (127 → 129 파일)
6. ~~**Baron 양 trust gap 보완**~~ ✅ Phase 2: 1050084 Baron Capital Funds Trust 단독 보고분 4건 추가 + renormalize bucket 미스 5건 정리 (76 → 75 파일, 모든 1996-2025 연도 _S1+_annual cover)
7. **AMG N-CSR 에서 Yacktman 섹션 추출** — 2012-2025 의 96 AMG 합본 N-CSR 에서 Yacktman-specific 부분만 slice (text_cleaner.py 단계)
8. **분기 cadence alignment 정책 확정** — 반기 → 분기 mapping 규칙을 text_tagger.py 단계에서 일괄 적용
9. **목적적합성 (project fit) 검증** — Phase 3: 각 폴더별 형식 별 임의 추출 → 보고서 구조 + letter 본문 유무 + Phase 2 GRU/embedding 적합성 평가 → `data/processed/result.md` 작성

---

## Reproducibility

수집은 다음 스크립트 조합으로 idempotent:
- [scripts/text_scraper.py](../../scripts/text_scraper.py) — 7명 통합 스크래퍼
- [scripts/_naming.py](../../scripts/_naming.py) — 명명 helper
- [scripts/_rename_existing.py](../../scripts/_rename_existing.py) — 마이그레이션 (1회용)
- [scripts/_grantham_brute.py](../../scripts/_grantham_brute.py) — Grantham PDF URL brute-force 보강
- [scripts/_grantham_wayback.py](../../scripts/_grantham_wayback.py) — Grantham Wayback Machine fallback (2007-2017 옛 GMO URL)
- [scripts/_einhorn_wayback.py](../../scripts/_einhorn_wayback.py) — Einhorn Wayback fallback (greenlightcapital.com 자체 archive + 자동 분류)
- [scripts/_renormalize_edgar.py](../../scripts/_renormalize_edgar.py) — collision suffix → sequence 번호 정규화

```bash
cd 2026-AIFinance-Project/TextData-Processing

# 신규 수집 (인자 없으면 7명 모두)
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py buffett hawkins
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py grantham         # GMO sitemap-driven
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py driehaus baron yacktman  # EDGAR
PYTHONIOENCODING=utf-8 python scripts/text_scraper.py einhorn          # GLRE 8-K best-effort

# Grantham brute-force 추가 수집 (현행 사이트 PDF URL 패턴)
PYTHONIOENCODING=utf-8 python scripts/_grantham_brute.py

# Grantham Wayback fallback (2007-2017 옛 GMO URL — 사이트에서 사라진 letter)
PYTHONIOENCODING=utf-8 python scripts/_grantham_wayback.py

# Einhorn Wayback fallback (greenlightcapital.com 자체 archive + 자동 분류)
PYTHONIOENCODING=utf-8 python scripts/_einhorn_wayback.py

# 명명규칙 마이그레이션 (1회 실행 후 끝)
python scripts/_rename_existing.py --dry-run  # 미리보기
python scripts/_rename_existing.py            # 실제 rename

# Collision suffix → sequence 번호 정규화 (Baron/Driehaus/Yacktman/Hawkins)
python scripts/_renormalize_edgar.py --dry-run
python scripts/_renormalize_edgar.py
```

이미 다운로드된 파일은 자동 skip. SEC EDGAR 호출은 정책 준수 UA + 0.3s rate-limit 적용 (10 req/s 제한 안에서 운용).

Windows 환경에서는 `PYTHONIOENCODING=utf-8` 필요 (cp949 콘솔 인코딩 회피).
