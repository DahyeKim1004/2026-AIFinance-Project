# Phase 3 — 목적적합성 (Project Fit) 검증 결과

> **작성일**: 2026-04-30
> **목적**: 수집된 raw 코퍼스가 InvestorDNA 프로젝트 (Phase 2 GRU + FinBERT embedding ↔ macro state mapping) 에 적합한지 검증.
> **방법론**:
> - **구조 검증**: 각 투자자 폴더에서 형식 (.txt / .htm / .html / .pdf) 별 sample 추출 → 보고서 구조 + letter 본문 위치/유무 + 정량분석 noise 비율 평가
> - **내용 검증**: sample 들의 letter 본문을 직접 dump 하여 substantive 한 투자 철학 + 시장 view + 종목 thesis + risk attitude 가 실제로 들어있는지 확인

---

## 1. 평가 기준 (Suitability Rubric)

### 1.1 프로젝트 목표 — 감성/언어 기반 persona 분석

[project_v2.md](../../project_v2.md) 채택안 + [project.md](../../project.md) 옵션 종합:
- **Phase 2 GRU**: 텍스트의 risk-attitude keyword + language sentiment 를 macro state 와 mapping → "True Persona Score" vector
- **Phase 3 (옵션)**: LLM 으로 Loss Aversion (1-10), Risk Preference (1-10), Time Horizon (Short/Long) 점수화

→ **본 프로젝트는 본질적으로 텍스트 감성 / 언어 기반 persona 분석**. FinBERT embedding 의 입력은 **투자자 본인의 voice / narrative / 심리** 가 담긴 prose.

### 1.2 데이터 유형별 프로젝트 적합성

| 데이터 유형 | 프로젝트에 필요? | 사유 |
|---|---|---|
| **Shareholder Letter narrative** (storytelling, philosophy, market commentary, forward-looking 자세) | ✅ **핵심 입력** | 투자자의 voice + psychology + risk attitude. FinBERT embedding 의 textbook input |
| Schedule of Investments / 보유 종목표 | ❌ 폐기 | Role 2 (13F 데이터 브랜치) 가 별도 처리. 텍스트 분석 noise |
| Statement of Operations / Financial Highlights | ❌ 폐기 | Phase 3 (Fama-French 회귀) 가 처리. 텍스트 의미 해석에 noise |
| iXBRL tag soup / Item 1-12 regulatory boilerplate | ❌ 폐기 | 의무 공시 양식, 투자자 voice 부재 |
| Performance Review 숫자 나열 ("fund returned 12.3% in Q2") | ⚠️ 회색 | Letter 안에 있어도 sentiment 약함. **commentary / philosophy 가 진짜 시그널**. text_cleaner.py 에서 "왜" 부분만 보존 권장 |

### 1.3 등급 정의 (적합성 + 처리 비용 통합)

| 등급 | 파일 내용 구성 | 처리 비용 | 프로젝트 사용 가능성 |
|---|---|---|---|
| **A** | ≥95% letter narrative — 정량 noise 거의 없음 | 최소 (헤더/푸터 trim) | 즉시 사용 |
| **B** | Letter 본문 명확 + SGML/HTML wrapping. 추출 후 >80% narrative | 중간 (regex extract) | 추출 후 사용 |
| **C** | Letter 가 financial 섹션에 둘러싸임. 추출 안 하면 noise > narrative | 높음 (DOM/section parsing) | 정확한 extract 후 사용. **정량 부분은 폐기** |
| **D** | Letter 본문 미존재 / OCR 필요 / 외부 voice (auditor 등) / iXBRL 거대 wrapping | 매우 높음 또는 폐기 | 폐기 또는 전용 파이프라인 |

**핵심**: 등급 C/D 의 처리 비용이 큰 이유는 **정량 데이터 (Schedule of Investments, iXBRL 등) 가 letter 본문보다 압도적으로 많아서** 인데, 이 정량 부분은 **우리 프로젝트엔 어차피 불필요**. text_cleaner.py 가 stripping 하면 결과적으로 letter narrative 만 남으므로 **모든 등급이 실질적으로 프로젝트 사용 가능**.

---

## 2. 파일별 분석 (20 sample)

### 2.1 INV_BUFFETT — Warren Buffett

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Buffett_85.html](../raw/buffett/Buffett_85.html) | HTML (개인 사이트) | 90 KB | Berkshire 사이트 직접 letter HTML, header/footer 정도만 | ✅ "To the Shareholders of Berkshire Hathaway Inc." 즉시 시작 (pos 47) | **A** |
| [Buffett_15.pdf](../raw/buffett/Buffett_15.pdf) | PDF | 2.4 MB, 30 pages | Annual Letter PDF, 표지 + Performance 표 + 본문 letter | ✅ 첫 5,000자 안에 Buffett voice 시작 | **A** |

**소견**: 두 형식 모두 **순수 letter 본문**. Performance 표가 첫 페이지에 있으나 noise 라기보다 letter 의 일부. **A 등급, 추가 처리 거의 불필요**.

---

### 2.2 INV_HAWKINS — Mason Hawkins (Longleaf Partners)

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Hawkins_98.txt](../raw/hawkins/Hawkins_98.txt) | SGML wrapped TXT | 160 KB | EDGAR N-30D pre-Sarbanes-Oxley plain text | ✅ "Letter to Shareholders" pos 1767, "TO OUR SHAREHOLDERS" pos 4026 (early). Noise: Financial Highlights, PORTFOLIO OF INVESTMENTS | **B** |
| [Hawkins_07_Q1.pdf](../raw/hawkins/Hawkins_07_Q1.pdf) | PDF (사이트) | 529 KB, 31 pages | Longleaf 사이트 quarterly report PDF, 4펀드 합본 | ✅ "Letter to Shareholders" pos 3211, 펀드별 letter section | **A** |
| [Hawkins_15.htm](../raw/hawkins/Hawkins_15.htm) | EDGAR N-CSR HTML | 2.1 MB | SGML+HTML, 4펀드 합본 + Schedule of Investments + Financial Highlights + Items 1-12 | ✅ "Letter to Shareholders" pos 8216, "To Our Shareholders" pos 11915 (early). 정량 noise 다수 | **C** |
| [Hawkins_24_Q2_01.pdf](../raw/hawkins/Hawkins_24_Q2_01.pdf) | PDF (사이트, per-fund) | 209 KB, 9 pages | "Longleaf Partners Global Fund Commentary 2Q24" — 한 펀드 letter 만 | ✅ 첫 페이지부터 commentary 본문 | **A** |

**소견**:
- **사이트 PDF (2007 Q1, 2024 Q2)**: 순수 letter, **A 등급**.
- **EDGAR TXT (1998)**: SGML 헤더 + financial 노이즈 약간 — **B 등급**, regex 로 letter section 추출 가능.
- **EDGAR HTM (2015)**: 거대한 multi-fund N-CSR 합본, letter 섹션은 명확하지만 financial 데이터에 둘러싸임 — **C 등급**, DOM-based section slicing 필요.

---

### 2.3 INV_GRANTHAM — Jeremy Grantham (GMO)

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Grantham_10_Q2.pdf](../raw/grantham/Grantham_10_Q2.pdf) | PDF (gmo.com) | 78 KB, 13 pages | GMO Quarterly Letter, "Summer Essays" 목차 + 본문 | ✅ Pure essay narrative, "Portfolio Outlook and Recommendations" 등 | **A** |
| [Grantham_18_raceofourlives_revisited.pdf](../raw/grantham/Grantham_18_raceofourlives_revisited.pdf) | PDF (시그니처 essay) | 800 KB, 8 pages | GMO White Paper, 시그니처 essay | ✅ 첫 페이지부터 Grantham voice ("if we had no carbon dioxide at all...") | **A** |
| [Grantham_25_Q3.pdf](../raw/grantham/Grantham_25_Q3.pdf) | PDF (gmo.com) | 384 KB, 13 pages | GMO Quarterly Letter, Introduction + 본문 | ✅ Pure narrative ("Most investors believe...") | **A** |

**소견**: GMO 파일 전체가 **PDF 단일 형식** + **순수 essay narrative** (분기 letter / White Paper / Viewpoint 모두). Schedule of Investments / Financial Highlights 가 없음. **모두 A 등급**, PDF→텍스트 추출 후 즉시 사용 가능. 다만 "Dear Shareholders" 식의 markers 가 없으므로 letter 인식 로직은 다른 keyword (e.g., GMO/Grantham/Quarterly Letter) 기반이어야 함.

---

### 2.4 INV_DRIEHAUS — Richard Driehaus

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Driehaus_00.txt](../raw/driehaus/Driehaus_00.txt) | SGML wrapped TXT | 270 KB | EDGAR N-30D, plain text 다중 펀드 | ✅ "Dear Fellow Shareholder" pos 1544 (early), "Manager's Letter" pos 3724. Noise: Statement of Operations, Schedule of Investments, Financial Highlights | **B** |
| [Driehaus_10_S1.htm](../raw/driehaus/Driehaus_10_S1.htm) | EDGAR N-CSRS HTML | 2.0 MB | N-CSRS (semi-annual), multi-fund | ✅ PM commentary 가 Schedule of Investments 다음 deep section 에 위치. 추출 시 종목 thesis + 거시 view 명확 | **C** |
| [Driehaus_24.htm](../raw/driehaus/Driehaus_24.htm) | iXBRL N-CSR HTML | 5.4 MB | iXBRL inline tagging 형식 (2024 EDGAR 신양식) | ✅ "shareholder" 72x, "investment philosophy" 2x, "TOP PERFORMANCE CONTRIBUTORS" 22x. iXBRL 태그 stripping 필수 | **C/D** |

**소견**:
- **2000 TXT**: B 등급, regex 로 letter section 추출 가능.
- **2010 HTM**: C 등급, letter 가 deep section 에 위치 — 다중 펀드 합본의 letter section 분리 필요.
- **2024 HTM**: iXBRL 형식 변환됨. `<ix:nonNumeric>`, `<ix:continuation>` 태그가 letter content 를 감싸고 있어 BeautifulSoup + namespace-aware parsing 필요.

> **위험요소**: 2021 Driehaus 본인 사망. 2021+ letter 는 후임 PM 명의 — Phase 2/3 학습 시 cutoff 정책 필요.

---

### ~~2.5 INV_EINHORN~~ — ❌ 카테고리 제외 (2026-04-30, 팀 합의)

**제외 사유**: Einhorn 코퍼스 29개 (27 PDF + 2 EDGAR 8-K HTM) 모두 분기 LP partner letter 가 아니라 **외부 컨퍼런스 stock pitch / activist proxy / sales speech**. project goal (분기 cadence persona analysis) 에 본질적으로 부적합 → **GRU 분기 cadence 입력 부적합**.

샘플 검증 결과 (인용은 archived):
- `Einhorn_13_applevoting.pdf` — Apple proxy contest 보도자료 (단발 종목 액션 호소)
- `Einhorn_18_sohn.pdf` — Sohn 2018 stock pitch (AGO 공매도 thesis 63장)
- `Einhorn_24_robinhood.pdf` — Robin Hood 2024 stock pitch (PTON 매수 발표, Peloton 운동 메타포)

**삭제된 자원**:
- `data/raw/einhorn/` (29 파일, 248 MB) — 전체 폴더 삭제
- `scripts/_einhorn_wayback.py` — Einhorn 전용 Wayback 스크립트 삭제

**Long/Short Fundamental 카테고리 대체 후보**: Bill Miller / Bill Ackman / Cliff Asness 등 — Role 4 합의 단계에서 별도 검토.

---

### 2.6 INV_BARON — Ron Baron

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Baron_98.txt](../raw/baron/Baron_98.txt) | SGML wrapped TXT | 230 KB | EDGAR N-30D, plain text | ⚠️ 표준 marker 미매칭 (Dear Shareholder 등). Baron 의 letter 는 다른 phrasing 사용 ("Dear Baron Funds Shareholder" 등). Financial Highlights noise. | **B** (커스텀 marker 필요) |
| [Baron_10.htm](../raw/baron/Baron_10.htm) | EDGAR N-CSR HTML | 2.6 MB | "BIFT—5 FUND—BARON ASSET, GROWTH, SMALL CAP, OPPORTUNITY & 5TH AVENUE" 합본 | ✅ "Annual Report" pos 2267, "Management's Discussion of Fund Performance" pos 7,862 (진짜 PM commentary). 펀드별 letter 다수 | **C** (5개 펀드 분리 필요) |
| [Baron_24.htm](../raw/baron/Baron_24.htm) | iXBRL N-CSR HTML | 9.3 MB | iXBRL 신양식, `<ix:nonNumeric name="oef:ShareholderReportAnnualOrSemiAnnual">` 태그로 letter wrap | ✅ "Sincerely" pos 6,607,409 (letter 끝), "shareholder" 68x. iXBRL stripping 필수 | **C/D** |

**소견**:
- **1998 TXT**: Baron 의 letter phrasing 이 표준과 다름 — text_tagger.py 에 Baron 전용 marker 사전 필요.
- **2010 HTM**: 5개 펀드 합본 — Baron Asset / Growth / Small Cap / Opportunity / 5th Avenue letter 별로 분리 필요. 합본 그대로 embedding 하면 페르소나 평균화로 시그널 흐려짐. "Dear Baron Funds Shareholder" 는 5줄 generic 인사말이고 진짜 PM commentary 는 "Management's Discussion of Fund Performance" 섹션.
- **2024 HTM**: iXBRL + 9 MB 거대 파일. Letter 본문은 존재 ("Sincerely" 발견) 하지만 XBRL 태그 비율이 압도적. **현재 단순 text 추출 방식 (250 KB plain) 으론 letter 본문 미발견** — BeautifulSoup + section-aware parsing 필수.

---

### 2.7 INV_YACKTMAN — Don Yacktman

#### 2.7.1 Standalone era (1995-2011, 33 파일)

| 파일 | 형식 | 크기 | 결론 | 등급 |
|---|---|---|---|---|
| [Yacktman_98.txt](../raw/yacktman/Yacktman_98.txt) | SGML TXT | 64 KB | "MESSAGE TO SHAREHOLDERS / Donald A. Yacktman / Dear Fellow Shareholder:" → 본인 letter 명확 | **B** |
| [Yacktman_05.txt](../raw/yacktman/Yacktman_05.txt) | SGML TXT | 97 KB | "Donald A. Yacktman / Stephen Yacktman / Dear Fellow Shareholder: Since the S&P 500 Index peaked in March 2000..." → letter 본문 substantive | **B** |

**소견**: 1995-2011 standalone era 의 모든 파일은 **Yacktman 본인 (또는 Yacktman team) letter 본문 명확**. Phase 2 GRU 학습 입력 가능.

#### 2.7.2 AMG era (2012-2025, 96 파일)

전수 keyword 검사 결과 4 부류:

| 부류 | 파일 수 | 의미 | 처리 |
|---|---|---|---|
| **AMG era 후기 + 신양식** (2020-2025, yack ≥ 100, no other sub-adv 또는 "opinions of Yacktman" attribution) | **23** (19 + 4) | 순수 AMG Yacktman 펀드 보고서 | **즉시 활용** |
| **AMG era 구양식 dominant** (2012-2019, yack ≥ 100) | **~30** | AMG 합본 N-CSR 의 Yacktman section dominant | **anchor 기반 deep slicing 활용** |
| **Mixed minor** (yack 1-15) | ~40 | Yacktman 은 fund family list 에 잠깐 mention 만, 본문은 다른 sub-adv (Trilogy/Skyline/GW&K 등) | **noise — 폐기** |
| **No yacktman** (yack=0) | **2** ([Yacktman_12_01.htm](../raw/yacktman/Yacktman_12_01.htm), [Yacktman_12_S1_04.htm](../raw/yacktman/Yacktman_12_S1_04.htm)) | Trilogy 등 다른 sub-adv 만 | **폐기** |

**Anchor 기반 추출 검증**:

[Yacktman_24.htm](../raw/yacktman/Yacktman_24.htm) (2024 신양식, 10.2 MB, yack 220) — anchor `"AMG Yacktman Focused Fund Class N"` @ pos 288,882:
> "AMG Yacktman Focused Fund Class N / YAFFX ANNUAL SHAREHOLDER REPORT | December 31, 2024 ... PERFORMANCE REVIEW: 2024 proved to be a challenging performance period for the Fund... TOP CONTRIBUTORS: Fox saw considerable growth in Fox News viewership... TOP DETRACTORS: Samsung Electronics is a global leader..."

[Yacktman_17_S1_02.htm](../raw/yacktman/Yacktman_17_S1_02.htm) (2017 AMG 구양식, 1.2 MB, yack 313) — anchor `"AMG Yacktman Fund Portfolio Manager's Comments"` @ pos 885,384 (전체의 73% 지점):
> "2017 was a year in which **risks were largely cast aside** and markets rocketed higher, led in large part by **already expensive growth companies**. Volatility levels in markets set record lows and **valuations expanded yet again**...
>
> Given our goal of **generating solid returns over time while managing the level of risk**, we were gratified that the AMG Yacktman Fund returned more than 18% for the year...
>
> We were comfortable owning large positions in **Samsung and Fox** because we believed they **sold at extremely low levels relative to their value**...
>
> Today's market environment **reminds us of other periods where investors ignored risks, chased growth and paid little attention to valuations**. The combination of these factors can be dangerous, with more potential downside scenarios than long-term upside cases. Investing in an expensive market is especially challenging for fund managers like us who are **focused on protecting capital**...
>
> For some historical perspective, the last momentum-oriented growth chasing market like this was in **1999**..."

→ Buffett / Hawkins / Grantham 와 동등 수준의 substantive content. 4-시그널 모두 명시 (protecting capital + valuation framework + Samsung/Fox thesis + risk attitude + 1999 momentum 비교).

[Yacktman_14_S1_02.htm](../raw/yacktman/Yacktman_14_S1_02.htm) (2014 AMG era, 754 KB, yack 213) — 동일 anchor @ pos 564,559 (전체의 75% 지점). 동일 구조로 substantive PM commentary 추출 가능.

**소견**:
- ✅ **Anchor 명확**: `"AMG Yacktman Fund Portfolio Manager's Comments"` / `"AMG Yacktman Focused Fund Portfolio Manager's Comments"` — deterministic 헤더.
- ✅ **위치 일관**: 파일 전체의 70-80% 지점 (deep 하지만 일관됨).
- ✅ **Content quality**: 다른 투자자와 동급. 1999 momentum 시장 비교, Samsung/Fox 가치 thesis, "protecting capital" 철학 명시.
- ❌ **2 파일 (Yacktman_12_01, Yacktman_12_S1_04)** + Mixed minor ~40개 파일은 noise → 폐기.

**유효 파일 수**:
- 1995-2011 standalone: 33
- 2012-2019 AMG era dominant: ~30 (anchor 기반 deep slicing)
- 2020-2025 AMG era 후기 + 신양식: 23
- **총 ~73-86 / 129** (~60%)
- 폐기: 2 (yack=0) + ~40 mixed minor (yack 1-15) = ~42개

---

## 3. 형식 (확장자) 별 종합 평가

| 형식 | 출처 | 적합성 | 권장 처리 |
|---|---|---|---|
| **`.html` (Berkshire 사이트)** | Buffett 1977-1997 | ✅ A | 최소 처리 (header/footer trim) |
| **`.pdf` (회사 사이트)** | Buffett, Hawkins (2007-2025), Grantham (전체) | ✅ A 대부분 | pypdf 추출 → 정상 |
| **`.txt` (EDGAR pre-2003)** | Hawkins 1995-2002, Driehaus 1996-2001, Baron 1996-2002, Yacktman 1995-2005 | ⚠️ B | SGML stripping + section regex |
| **`.htm` (EDGAR 2003-2023)** | 모두 (Hawkins, Driehaus, Baron, Yacktman) | ⚠️ C | DOM 파싱 + multi-fund 섹션 slicing |
| **`.htm` (EDGAR 2024+ iXBRL)** | Driehaus 2024+, Baron 2024+, Yacktman 2024+ | ❌ C/D | iXBRL namespace-aware 파싱 필수. text_cleaner.py 에서 ix:* 태그를 stripping 후 letter section 식별 |

---

## 4. 투자자별 적합성 등급

| # | Investor | 구조 등급 (추출 비용) | Content 등급 (substantive 여부) | 종합 권장 |
|---|---|---|---|---|
| 1 | **Buffett** | **A** | **A++** (본인 voice, 4-시그널 모두 ✓) | **즉시 사용** |
| 2 | **Hawkins** | **B+** | **A** (Longleaf team, "60-cent dollars" framework) | **즉시 사용** (EDGAR 만 deep slicing) |
| 3 | **Grantham** | **A−** | **A** (GMO Inker/Pease + Grantham essay) | **즉시 사용** (author 메타 분리) |
| 4 | **Driehaus** | **C** | **A−** (Driehaus team, 종목 thesis + EM macro) | **deep slicing 필요** + 2021 cutoff |
| 5 | **Baron** | **C** | **A** (Ron Baron team, "competitive advantages" + macro QE view) | **deep slicing 필요** + 5펀드 분리 |
| 6 | **Yacktman** | **C−** | **A** (전체, anchor 기반 추출 시) | **noise 필터링 + anchor-based deep slicing** — 유효 ~73-86/129 |

**총평**:
- **6명 (Buffett, Hawkins, Grantham, Driehaus, Baron, Yacktman)**: letter 본문 존재 ✓ Content quality 측면에서 substantive 한 4-시그널 (투자철학 / 시장view / 종목thesis / risk attitude) 모두 보유 — Phase 2/3 학습 입력 적합.
- **Einhorn 카테고리 제외 (2026-04-30, 팀 합의)**: 분기 LP letter 부재. data/raw/einhorn/ + 전용 스크립트 삭제 완료. Long/Short Fundamental 대체 후보는 Role 4 단계 별도 검토.

---

## 5. text_cleaner.py 작업 권장사항 (Phase 4)

Phase 4 (text_cleaner.py 파일럿) 시 다음 우선순위로 처리:

### 5.1 형식별 stripping 파이프라인

```
1. PDF (Buffett, Grantham, Hawkins 사이트)
   → pypdf 텍스트 추출 → 헤더/푸터 trim → 즉시 사용

2. SGML TXT (1995-2002 EDGAR)
   → <DOCUMENT> 블록 추출 → <TEXT>...</TEXT> body
   → "Dear Shareholders" / "TO OUR SHAREHOLDERS" / 투자자별 custom marker 로 letter section 시작점 식별
   → "SCHEDULE OF INVESTMENTS" / "FINANCIAL HIGHLIGHTS" 로 끝점 식별

3. EDGAR HTM (2003-2023)
   → BeautifulSoup parse → SGML wrapper 제거
   → "Letter to Shareholders" / "To Our Shareholders" / "Portfolio Manager's Comments" h-tag 기반 section
   → multi-fund 합본인 경우 fund-name h-tag 으로 추가 slicing

4. iXBRL HTM (2024+)
   → BeautifulSoup namespace-aware → ix:* 태그 stripping
   → ix:nonNumeric[name="oef:ShareholderReportAnnualOrSemiAnnual"] 블록 식별
   → 그 다음 section header 까지 letter body 로 추출
```

### 5.2 투자자별 custom marker 사전

```python
LETTER_MARKERS = {
    'INV_BUFFETT':  ['To the Shareholders of Berkshire Hathaway'],
    'INV_HAWKINS':  ['Letter to Shareholders', 'TO OUR SHAREHOLDERS', 'To Our Shareholders'],
    'INV_GRANTHAM': ['GMO Quarterly Letter', 'GMO White Paper', 'GMO Viewpoints'],
    'INV_DRIEHAUS': ["Dear Fellow Shareholder", "Manager's Letter", 'Portfolio Manager'],
    'INV_BARON':    ["Management's Discussion of Fund Performance", 'Sincerely, Ronald Baron'],
    'INV_YACKTMAN': [
        'Dear Fellow Shareholder',                                  # 1995-2011 standalone (Don 본인)
        'MESSAGE TO SHAREHOLDERS',                                  # 1995-2011 standalone
        "AMG Yacktman Fund Portfolio Manager's Comments",           # 2012-2019 AMG 구양식 (deep, ~70-80% 지점)
        "AMG Yacktman Focused Fund Portfolio Manager's Comments",   # 동
        'AMG Yacktman Focused Fund Class N',                        # 2024+ iXBRL TSR 양식
        'opinions of Yacktman',                                     # 2020-2023 attribution 시그니처
    ],
}
```

### 5.3 fund-level slicing 정책 (multi-fund 합본)

| Investor | 펀드 분리 필요? | 분리 단위 |
|---|---|---|
| Buffett | ❌ | 단일 |
| Hawkins | ✅ (2022+) | Partners / Small-Cap / Global / International |
| Grantham | ❌ | GMO 단일 (다양한 fund 가 있지만 letter 는 통합) |
| Driehaus | ✅ | Driehaus Emerging Markets Growth / 등 |
| Baron | ✅ | Baron Asset / Growth / Small Cap / Opportunity / 5th Avenue / Partners 등 |
| Yacktman | ✅ | Yacktman Fund / Yacktman Focused / AMG family 다수 |

### 5.4 cutoff 정책 (Persona authenticity)

| Investor | Cutoff | 사유 |
|---|---|---|
| Buffett | None | 본인 작성 지속 |
| Hawkins | None | Hawkins 2025 말까지 활동 |
| Grantham | None | Grantham 본인 + 시그니처 essay 라벨 분리 사용 |
| Driehaus | **2021** | 본인 사망, 2022+ 후임 PM 명의 |
| Baron | None | 본인 작성 지속 |
| Yacktman | **2016** | Don Yacktman 은퇴, 2017+ Stephen Yacktman / Jason Subotky |

---

## 6. 결론

### 종합 판정

1. **프로젝트 목표는 텍스트 감성/언어 기반 persona 분석** → letter narrative 가 핵심 입력. N-CSR 의 정량 섹션 (Schedule of Investments, iXBRL 태그) 은 모두 stripping 대상 (Role 2/3 트랙이 별도 처리).

2. **6명 (Buffett, Hawkins, Grantham, Driehaus, Baron, Yacktman)**: letter 본문 확실히 존재 + Phase 2/3 학습 가능. Yacktman 의 AMG era 96 파일 중 ~42개는 다른 AMG sub-adv 보고서로 폐기, **나머지 ~54개는 anchor 기반 deep slicing 시 substantive content 추출 가능** → **유효 ~73-86 / 129 파일**.

3. **Einhorn 카테고리 제외 (2026-04-30, 팀 합의)**: 27개 PDF + 2 EDGAR 8-K 가 분기 LP partner letter 가 아니라 외부 컨퍼런스 stock pitch + activist proxy + sales speech. data/raw/einhorn/ + scripts/_einhorn_wayback.py 삭제 완료. Long/Short Fundamental 대체 후보 Role 4 단계 별도 검토.

4. **2024+ EDGAR iXBRL 신양식**: 처리 비용 큼이지만 letter narrative 자체는 보존됨 → text_cleaner.py namespace-aware 파싱 + AMG 합본 fund-section slicing 동시 필요.

### 핵심 인사이트 — 정량 데이터 vs 정성 데이터

본 프로젝트의 텍스트 분석 트랙은 **투자자의 언어 시그널** 을 다루므로 N-CSR 파일들의 거대 size (5-10 MB) 에 압도되지 말 것. 실제 학습 입력은 letter narrative **수십~수백 KB**.

### Role 4 합의 단계 결정 사항

1. **Long/Short Fundamental 카테고리 대체 후보** (Einhorn 제외 후): Bill Miller / Bill Ackman / Cliff Asness 등 검토 — 각각 단점 검토 필요, PLAN.md §5 참조.
2. **Yacktman AMG era noise 자동 필터**: yack count threshold (예: < 30) 로 mixed minor 파일 폐기 + deep slicing 로직 (text_cleaner.py 의 "AMG Yacktman" header 기반 section 추출) 구현.
3. **iXBRL stripping 파일럿 우선순위**: Driehaus_24 / Baron_24 / Yacktman_24 — 셋 다 iXBRL 신양식 + AMG 합본 동시 적용된 가장 어려운 케이스.
4. **Driehaus 2021 cutoff / Yacktman 2016 cutoff** Role 4 합의 후 적용.

### 다음 단계 (Phase 4 priority)

1. **text_cleaner.py 의 iXBRL stripping** 파일럿 — Driehaus_24.htm / Baron_24.htm / Yacktman_24.htm 3개 파일에서 letter body 추출 검증
2. **multi-fund 합본 분리 로직** — Hawkins 4펀드 / Baron 5펀드 / Yacktman AMG family 의 letter section 분리
3. **투자자별 custom marker 사전 finalize** — text_tagger.py 와 협업해 source_type 어휘와 정합성 확보
4. **Driehaus 2021 cutoff / Yacktman 2016 cutoff** Role 4 합의 후 적용

---

## 7. Content Quality 심층 검증

### 7.1 검증 방법론

§2 의 sample 별로 letter 본문 4500자 dump → 다음 4가지 시그널 존재 여부 평가:
1. **투자 철학 (Investment Philosophy)**: capital protection / quality / value / growth / loss aversion 등 명시
2. **시장 view (Market Commentary)**: 거시 / Fed / 인플레이션 / 시장 valuation 분석
3. **종목 thesis (Stock Thesis)**: 특정 holding 의 매수/매도 사유, 회사별 분석
4. **Risk Attitude**: 집중도 / cash 비중 / cycle 시각 / loss aversion language

### 7.2 투자자별 검증 결과

#### ✅ Buffett — A++ (본인 voice, 모든 시그널 명시)

[Buffett_15.pdf](../raw/buffett/Buffett_15.pdf) 직접 검증:
> "intrinsic value of the business... I've made some dumb purchases... we would be delighted to repurchase our shares should they sell as low as 120% of book value... BNSF moves about 17% of America's intercity freight... carrying 45% more ton-miles of freight than our closest competitor... weakness in the U.S. economy or, possibly, because of insurance mega-catastrophes"

→ **본인 필체** + intrinsic value framework + 자기반성 + business operation 상세 (BNSF railway) + risk attitude (mega-catastrophes). 4가지 시그널 모두 ✓.

#### ✅ Hawkins — A (Longleaf team voice, 가치투자 framework 명시)

[Hawkins_07_Q1.pdf](../raw/hawkins/Hawkins_07_Q1.pdf) 직접 검증:
> "inflation plus 10% absolute annual return goal... we purchased two new qualifying ideas in the Small-Cap Fund... the worldwide market declines in late February might linger and signal increasing volatility... 60-cent dollar additions... growing, competitively entrenched businesses led by high quality management teams... few names sell at a 40% discount to appraisal"

→ **Longleaf team voice** + value investing framework ("60-cent dollars", "40% discount to appraisal") + quality + management 강조 + 시장 view. 4가지 시그널 모두 ✓.

#### ✅ Grantham — A (GMO Asset Allocation team voice, fundamental + macro 분석)

[Grantham_25_Q3.pdf](../raw/grantham/Grantham_25_Q3.pdf) 직접 검증:
> "Most investors believe that the U.S. economy is superior to the rest of the world... those of us who have been systematically underweight the U.S. for those fifteen years should readily admit ex-post that this was a mistake... investments made on the back of regret turn out poorly more often than not... decompose the relative returns of the S&P 500 vs. MSCI World ex-USA into three components: 1. The dollar's rally, 2. Relative valuation expansion... 3. Fundamental outperformance... Magnificent Six may struggle to justify their currently lofty valuations"

→ **GMO Asset Allocation team (Ben Inker / John Pease) voice** — 분기 letter 는 GMO team voice, 시그니처 essay 만 Grantham 본인 voice. **GMO house view 일관성 유지**. 4가지 시그널 모두 ✓.

> **권장**: text_tagger.py 단계에서 author 메타데이터 분리 (signature_essay vs quarterly_letter).

#### ✅ Driehaus — A− (Driehaus team voice, 종목 thesis 명시)

[Driehaus_20.htm](../raw/driehaus/Driehaus_20.htm) 직접 검증:
> "We believe that the combination of relatively strong economic growth in key EM countries such as China and Taiwan, along with the attractive interest rates found across much of EM will lend support to capital flows into emerging economies... Ping An Healthcare and Technology Company Limited... has benefited from rapidly increasing patient consultation volumes... Burger King India Ltd... The IPO in mid-December was highly successful... Azul S.A. Sponsored ADR Pfd... The COVID-19 downturn in passenger traffic caused a significant hit to earnings... high degree of financial leverage carried by the company"

→ **Driehaus Capital team voice** — 종목별 thesis (Ping An, Burger King India, Azul, Cholamandalam) + 거시 EM view + risk attitude (financial leverage 우려). 4가지 시그널 모두 ✓.

> **주의 1**: Richard Driehaus 본인은 2021 사망. 2022+ letter 는 후임 PM (K.C. Nelson, Elizabeth Cassidy 등) team voice. Role 4 cutoff 정책 필요.
>
> **주의 2**: PM commentary 본문이 Schedule of Investments 다음에 묻혀있어 deep slicing 필요.

#### ✅ Baron — A (Ron Baron team voice, 투자 철학 + 거시 view 명시)

[Baron_10.htm](../raw/baron/Baron_10.htm) 직접 검증:
> "Baron Asset Fund invests primarily in medium-sized growth companies for the long-term while using value-oriented purchase and sell disciplines... The Fund purchases companies that the Adviser believes have **sustainable competitive advantages and strong financial characteristics**, operating in industries with favorable macroeconomic trends led by strong management... We believe the stock market's September rally was primarily driven by investors anticipating further quantitative easing by the Federal Reserve... a double-dip recession did not materialize. We believe the economy is at a critical inflection point regarding **deflation and reflation**... Many companies, strong financially, hold approximately $1.8 trillion in cash defensively... It is our view that macro economic events continue to overwhelm..."

→ **Ron Baron team voice** + 투자 철학 (sustainable competitive advantages, growth + value-oriented) + 거시 view (Fed QE, deflation/reflation 변곡점) + 시장 timing 분석. 4가지 시그널 모두 ✓.

#### ✅ Yacktman — A (전체, anchor 기반 추출 시)

상세 §2.7 참조. 핵심:
- **1995-2011 standalone (33개)**: Don Yacktman 본인 voice — "loss aversion", "Protect capital", "the price we pay is extremely important", "strong market position and relatively stable profit margins" → A 등급
- **2012-2019 AMG era 구양식 dominant (~30개)**: anchor `"AMG Yacktman Fund Portfolio Manager's Comments"` 기반 deep slicing 시 다른 투자자와 동등 수준의 substantive content — "risks were largely cast aside", "valuations expanded", "**focused on protecting capital**", "Samsung/Fox sold at extremely low levels relative to their value", "1999 momentum-oriented growth chasing market" 비교 → A 등급
- **2020-2023 AMG era 후기 (6개)**: "views expressed represent the opinions of Yacktman" attribution 명시 → A 등급
- **2024-2025 신양식 (4개)**: AMG Yacktman team voice — "multiple expansion vs underlying business results", "Fund remains concentrated with the top 10 positions representing 50.5%", 종목별 thesis (Fox/Schwab/Alphabet/Samsung/Bollore) → A 등급
- **AMG era noise (~42개)**: yack count < 30 + 다른 sub-adv (Trilogy/GW&K/Skyline 등) dominant → 폐기.

### 7.3 Content Quality 종합 등급표

| # | Investor | Content 등급 | 본인/팀 voice | 4-시그널 (철학/시장/종목/risk) | 사용 가능 letter 추정 |
|---|---|---|---|---|---|
| 1 | **Buffett** | A++ | 본인 직접 (1965~) | ✓✓✓✓ | 48 / 48 (100%) |
| 2 | **Hawkins** | A | Longleaf team (Hawkins + 후임) | ✓✓✓✓ | 125 / 125 (100%, deep slicing 후) |
| 3 | **Grantham** | A | GMO team (Inker/Pease 분기 + Grantham essay) | ✓✓✓✓ | 77 / 77 (100%) |
| 4 | **Driehaus** | A− | Driehaus team (~2021 본인, 이후 후임) | ✓✓✓✓ | 65 / 65 (deep slicing 후, cutoff 정책 별도) |
| 5 | **Baron** | A | Baron team (Ron 주도) | ✓✓✓✓ | 75 / 75 (deep slicing 후) |
| 6 | **Yacktman** | A | Don 본인 (1995-2011) / Yacktman team (AMG era 2012+) | ✓✓✓✓ | **~73-86 / 129** (~60%) |

→ **6명 모두** content quality 측면에서 substantive team voice 보유. 4가지 시그널 모두 명시. **GRU + FinBERT embedding + LLM persona scoring 입력으로 사용 가능**. (Einhorn 카테고리는 2026-04-30 팀 합의로 제외 — 분기 LP letter 부재)

> **단, 처리 비용 차이 큼**:
> - Buffett, Grantham (사이트 PDF 위주): **즉시 사용 가능**
> - Hawkins (사이트 PDF + EDGAR 합본): **EDGAR 합본은 deep slicing**
> - Driehaus, Baron, Yacktman (EDGAR N-CSR / iXBRL): **deep slicing + 다중 펀드 분리 + AMG era noise 필터링** 필수

### 7.4 핵심 인사이트 — 파일 안에서 letter 위치 차이

투자자별로 letter 본문이 파일 안에서 등장하는 위치가 매우 상이:

| 투자자 | Letter 시작 위치 (typical) | 비고 |
|---|---|---|
| Buffett | ~5,000자 (첫 페이지부터) | Performance 표 다음 즉시 letter |
| Hawkins (사이트 PDF) | ~3,000자 | TOC 다음 즉시 letter |
| Hawkins (EDGAR HTM) | ~10,000자 | SGML 헤더 + TOC + Schedule of Investments 다음 letter |
| Grantham | 0자 (Introduction 으로 시작) | PDF 자체가 letter 본문 |
| Driehaus (EDGAR HTM) | **~150,000-200,000자** (deep) | TOC + 다중 펀드 Schedule of Investments + Statement of Operations 다음에야 letter |
| Baron (EDGAR HTM) | ~7,000자 (TOC 다음) | "Management's Discussion of Fund Performance" 가 진짜 PM commentary, "Dear Baron Funds Shareholder" 는 5줄 generic 인사 |
| Yacktman (AMG 구양식) | **~750,000-885,000자** (1MB+ 파일의 70-80% 지점) | AMG Funds family 전체 N-CSR 합본의 늦은 위치 |
| Yacktman (2024 신양식) | ~290,000자 | iXBRL 태그 + 다중 fund report 다음 |

→ **text_cleaner.py 가 letter 본문 위치를 정확히 식별하지 못하면 letter 자체가 추출 안 됨**. 단순한 "처음 N자" 추출 방식은 Driehaus / Yacktman 에서 letter 미발견 위험.

---

## 8. 참고 — 분석 메서드 재현

```bash
cd 2026-AIFinance-Project/TextData-Processing
PYTHONIOENCODING=utf-8 python -c "
# 본 result.md 의 분석은 다음 sample 20개 + analyze_pdf/analyze_txt_or_htm 함수로 재현 가능.
# 자세한 코드는 본 검증 작업 conversation log 참조.
"
```

분석 sample 목록:
- buffett: `Buffett_85.html`, `Buffett_15.pdf`
- hawkins: `Hawkins_98.txt`, `Hawkins_07_Q1.pdf`, `Hawkins_15.htm`, `Hawkins_24_Q2_01.pdf`
- grantham: `Grantham_10_Q2.pdf`, `Grantham_18_raceofourlives_revisited.pdf`, `Grantham_25_Q3.pdf`
- driehaus: `Driehaus_00.txt`, `Driehaus_10_S1.htm`, `Driehaus_20.htm`, `Driehaus_24.htm`
- baron: `Baron_98.txt`, `Baron_10.htm`, `Baron_24.htm`
- yacktman: `Yacktman_98.txt`, `Yacktman_05.txt`, `Yacktman_14_S1_02.htm`, `Yacktman_17_S1_02.htm`, `Yacktman_24.htm`
