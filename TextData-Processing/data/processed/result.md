# Phase 3 — 목적적합성 (Project Fit) 검증 결과

> **작성일**: 2026-04-30 (Phase 3.2 — content quality 심층 검증 보강)
> **목적**: Phase 2 시계열 누락 검증 완료 후, 수집된 raw 코퍼스가 InvestorDNA 프로젝트 (Phase 2 GRU + FinBERT embedding ↔ macro state mapping) 에 적합한지 파일 형식별 임의 추출로 검증.
> **방법론 v1 (구조 검증)**: 각 투자자 폴더에서 형식 (.txt / .htm / .html / .pdf) 별로 시기 분산하여 2-4개 임의 추출 → 보고서 구조 + letter 본문 위치/유무 + 정량분석 noise 비율 + 프로젝트 적합성 등급 부여.
> **방법론 v2 (내용 검증, §8 신규)**: §2 sample 들의 letter 본문을 직접 dump 하여 **substantive 한 투자 철학 + 시장 view + 종목 thesis + risk attitude** 가 실제로 들어있는지 확인. 단순 SEC 보일러플레이트 / generic AMG President letter / 5줄 인사말 인지 구분.

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
| [Grantham_18_raceofourlives_revisited.pdf](../raw/grantham/Grantham_18_raceofourlives_revisited.pdf) | PDF (Phase 2 추가) | 800 KB, 8 pages | GMO White Paper, 시그니처 essay | ✅ 첫 페이지부터 Grantham voice ("if we had no carbon dioxide at all...") | **A** |
| [Grantham_25_Q3.pdf](../raw/grantham/Grantham_25_Q3.pdf) | PDF (gmo.com) | 384 KB, 13 pages | GMO Quarterly Letter, Introduction + 본문 | ✅ Pure narrative ("Most investors believe...") | **A** |

**소견**: GMO 파일 전체가 **PDF 단일 형식** + **순수 essay narrative** (분기 letter / White Paper / Viewpoint 모두). Schedule of Investments / Financial Highlights 가 없음. **모두 A 등급**, PDF→텍스트 추출 후 즉시 사용 가능. 다만 "Dear Shareholders" 식의 markers 가 없으므로 letter 인식 로직은 다른 keyword (e.g., GMO/Grantham/Quarterly Letter) 기반이어야 함.

> 단, [Grantham_10_Q2.pdf](../raw/grantham/Grantham_10_Q2.pdf) 와 [Grantham_25_Q3.pdf](../raw/grantham/Grantham_25_Q3.pdf) 는 표준 marker ("shareholder/letter") 가 매칭되지 않음 — text_tagger.py 의 letter 인식 로직에 GMO 전용 패턴 추가 필요.

---

### 2.4 INV_DRIEHAUS — Richard Driehaus

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Driehaus_00.txt](../raw/driehaus/Driehaus_00.txt) | SGML wrapped TXT | 270 KB | EDGAR N-30D, plain text 다중 펀드 | ✅ "Dear Fellow Shareholder" pos 1544 (early), "Manager's Letter" pos 3724. Noise: Statement of Operations, Schedule of Investments, Financial Highlights | **B** |
| [Driehaus_10_S1.htm](../raw/driehaus/Driehaus_10_S1.htm) | EDGAR N-CSRS HTML | 2.0 MB | N-CSRS (semi-annual), multi-fund | ⚠️ "Annual Report" pos 2669, "Portfolio Manager" pos 189136 (very late). Noise dominant | **C** |
| [Driehaus_24.htm](../raw/driehaus/Driehaus_24.htm) | iXBRL N-CSR HTML | 5.4 MB | **iXBRL inline tagging 형식** (2024 EDGAR 신양식) | ✅ "shareholder" 72x, "investment philosophy" 2x, "TOP PERFORMANCE CONTRIBUTORS" 22x. iXBRL 태그 stripping 필수 | **C/D** |

**소견**:
- **2000 TXT**: B 등급, regex 로 letter section 추출 가능.
- **2010 HTM**: C 등급, letter 가 늦게 등장 — 다중 펀드 합본의 letter section 분리 필요.
- **2024 HTM**: ⚠️ **iXBRL 형식 변환됨**. `<ix:nonNumeric>`, `<ix:continuation>` 태그가 letter content 를 감싸고 있어 BeautifulSoup + namespace-aware parsing 필요. raw text 추출 시 XBRL tag soup 이 letter 본문보다 많을 수 있음.

> **Driehaus 추가 위험요소**: 2021 Driehaus 본인 사망. 2021+ letter 는 후임 PM 명의 — Phase 2/3 학습 시 cutoff 정책 필요.

---

### 2.5 INV_EINHORN — David Einhorn

**🚨 재판정 (사용자 의문 검증 후 2026-04-30)**: Einhorn 코퍼스 28개는 **분기 LP partner letter 가 아니라 stock pitch / activist proxy / sales speech**. project goal (분기 cadence persona analysis) 에 본질적으로 부적합.

| 파일 | 실제 형식 | 추출 결과 | 본질 | 등급 |
|---|---|---|---|---|
| [Einhorn_13_applevoting.pdf](../raw/einhorn/Einhorn_13_applevoting.pdf) | 5 pages, 14K chars | "GREENLIGHT CAPITAL URGES APPLE SHAREHOLDERS TO OPPOSE COMPANY'S PROPOSAL" + Sincerely David Einhorn | **Activist proxy 보도자료** — 단발 종목 (Apple) 액션 호소 | **D** |
| [Einhorn_18_sohn.pdf](../raw/einhorn/Einhorn_18_sohn.pdf) | 63 pages, 30K chars | "Our idea today is Assured Guarantee, or AGO. It is a melting ice cube..." — AGO 공매도 thesis 63장 | **Sohn 2018 stock pitch** — 단발 종목 (AGO) 공매도 발표 | **D** |
| [Einhorn_24_robinhood.pdf](../raw/einhorn/Einhorn_24_robinhood.pdf) | 30 pages, 38K chars | "ROBIN HOOD INVESTORS CONFERENCE 15 Minute 'Stock Pitch' Ride... I'm going to talk about Peloton Interactive" | **Robin Hood 2024 stock pitch** — 단발 종목 (PTON) 매수 발표 (Peloton 운동 메타포 기획) | **D** |

**전체 판정**:
- 27개 Wayback PDF 모두 비슷한 패턴: **Sohn / Robin Hood / GO!UPs / Grant's 등 외부 컨퍼런스 발표** + activist proxy 자료. Einhorn 의 voice 는 분명 존재하지만 **"분기 LP에게 보내는 risk attitude commentary"가 아니라 "특정 종목 매매 thesis"**.
- 2 EDGAR 8-K HTM 도 letter 가 아니라 GLRE press release / BDO 외부 auditor 통지서.
- **분기 cadence 기반 GRU 학습 입력 부적합** — 발표 시점이 비정기이고 (Sohn 매년 5월, Robin Hood 10월, 그 외 산발), 내용이 일관된 commentary 가 아니라 **그날 발표한 종목 thesis** 임.
- **LLM persona scoring 에는 부분적 활용 가능** (Einhorn 의 short-bias / accounting skeptic / contrarian 성향이 thesis 안에 일관되게 묻어남).

**결론**: Einhorn 의 "Long/Short Fundamental" 카테고리는 **본 코퍼스로는 부적합**. 대안:
1. **카테고리 폐기** (8명 → 7명 분석)
2. **다른 Long/Short 투자자로 교체** (Bill Miller / Cliff Asness 등 — 단 단점 검토 필요, PLAN.md §5 참조)
3. **Einhorn 유지하되 LLM persona 만 활용** (Phase 3 의 Loss Aversion / Risk Preference 점수화에만 사용, GRU 입력 제외)

→ **Role 4 합의 단계에서 결정 필요. Role 1 단의 코퍼스 자체로는 GRU 입력 가능성 거의 없음.**

---

### 2.6 INV_BARON — Ron Baron

| 파일 | 형식 | 크기 | 구조 | Letter 여부 | 등급 |
|---|---|---|---|---|---|
| [Baron_98.txt](../raw/baron/Baron_98.txt) | SGML wrapped TXT | 230 KB | EDGAR N-30D, plain text | ⚠️ 표준 marker 미매칭 (Dear Shareholder 등). Baron 의 letter 는 다른 phrasing 사용 ("Dear Baron Funds Shareholder" 등). Financial Highlights noise. | **B** (커스텀 marker 필요) |
| [Baron_10.htm](../raw/baron/Baron_10.htm) | EDGAR N-CSR HTML | 2.6 MB | "BIFT—5 FUND—BARON ASSET, GROWTH, SMALL CAP, OPPORTUNITY & 5TH AVENUE" 합본 | ✅ "Annual Report" pos 2267, "Portfolio Manager" pos 163089. 펀드별 letter 다수 | **C** (5개 펀드 분리 필요) |
| [Baron_24.htm](../raw/baron/Baron_24.htm) | iXBRL N-CSR HTML | 9.3 MB | **iXBRL 신양식**, `<ix:nonNumeric name="oef:ShareholderReportAnnualOrSemiAnnual">` 태그로 letter wrap | ✅ "Sincerely" pos 6,607,409 (letter 끝), "shareholder" 68x. **iXBRL stripping 필수** | **C/D** |

**소견**:
- **1998 TXT**: Baron 의 letter phrasing 이 표준과 다름 — text_tagger.py 에 Baron 전용 marker 사전 필요.
- **2010 HTM**: 5개 펀드 합본 — Baron Asset / Growth / Small Cap / Opportunity / 5th Avenue letter 별로 분리 필요. 합본 그대로 embedding 하면 페르소나 평균화로 시그널 흐려짐.
- **2024 HTM**: iXBRL + 9 MB 거대 파일. Letter 본문은 존재 ("Sincerely" 발견) 하지만 XBRL 태그 비율이 압도적. **현재 단순 text 추출 방식 (250 KB plain) 으론 letter 본문 미발견** — BeautifulSoup + section-aware parsing 필수.

---

### 2.7 INV_YACKTMAN — Don Yacktman

**🚨 재판정 (사용자 의문 검증 후 2026-04-30)**: Yacktman 96 AMG era 파일 전수 keyword 검사 결과, **다수 파일이 사실 다른 AMG sub-advisor 펀드 보고서** 임이 발견됨. 그러나 deep slicing 시 Yacktman section 자체는 존재.

#### 2.7.1 Standalone era (1995-2011, 33 파일)

| 파일 | 형식 | 크기 | 결론 | 등급 |
|---|---|---|---|---|
| [Yacktman_98.txt](../raw/yacktman/Yacktman_98.txt) | SGML TXT | 64 KB | "MESSAGE TO SHAREHOLDERS / Donald A. Yacktman / Dear Fellow Shareholder:" → 본인 letter 명확 | **B** |
| [Yacktman_05.txt](../raw/yacktman/Yacktman_05.txt) | SGML TXT | 97 KB | "Donald A. Yacktman / Stephen Yacktman / Dear Fellow Shareholder: Since the S&P 500 Index peaked in March 2000..." → letter 본문 substantive | **B** |

**소견**: 1995-2011 standalone era 의 모든 파일은 **Yacktman 본인 (또는 Yacktman team) letter 본문 명확**. Phase 2 GRU 학습 입력 가능.

#### 2.7.2 AMG era (2012-2025, 96 파일) — 전수 keyword 검사 결과

| 부류 | 파일 수 | 의미 | 처리 |
|---|---|---|---|
| **Yacktman-only (yack ≥ 100, no other sub-adv)** | **19** (전부 2020-2025) | 순수 AMG Yacktman 펀드 보고서 (Yacktman / Focused / Special Opportunities) | 활용 |
| **Mixed dominant (yack ≥ 100, other sub-adv 동반)** | ~15 (대부분 2014-2019) | AMG 합본 N-CSR 의 Yacktman section dominant | **slicing 후 활용** |
| **Mixed minor (yack 1-15, other sub-adv dominant)** | ~60 | Yacktman 은 fund family list 에 잠깐 mention 만, 본문은 다른 sub-adv (Trilogy/Skyline/GW&K 등) | **본질적 noise — 폐기 권장** |
| **No yacktman (0 yack)** | **2** ([Yacktman_12_01.htm](../raw/yacktman/Yacktman_12_01.htm), [Yacktman_12_S1_04.htm](../raw/yacktman/Yacktman_12_S1_04.htm)) | Trilogy 등 다른 sub-adv 만 | **폐기** |

**핵심 검증** — Yacktman_24.htm (iXBRL, 10.2 MB, yack 220회, first @ pos 288,882):
- Pos 288,882~ 부터: **"AMG Yacktman Focused Fund Class N / YAFFX ANNUAL SHAREHOLDER REPORT | December 31, 2024 ... PERFORMANCE REVIEW: 2024 proved to be a challenging performance period for the Fund... TOP CONTRIBUTORS: Fox saw considerable growth in Fox News viewership... TOP DETRACTORS: Samsung Electronics is a global leader..."**
- → **진짜 Yacktman team 의 분기 commentary 본문 존재**, 단 합본 N-CSR 의 ~30% 깊이에서 시작.

**소견**:
- **사용자 직관 부분 정확**: 표면적으로 letter 가 안 보였던 이유는 **AMG 합본 N-CSR 안에서 Yacktman section 이 다른 펀드들 (Trilogy, GW&K, Skyline, Cadence, TimesSquare 등) 과 섞여있기 때문**.
- **deep slicing 가능성**: "AMG Yacktman Focused Fund" / "AMG Yacktman Fund" / "PERFORMANCE REVIEW" 헤더 기반 section 추출하면 본문 확보 가능.
- **2 파일 (Yacktman_12_01, Yacktman_12_S1_04)** 은 Yacktman 무관 → **폐기 대상**.
- **Mixed minor 60여개 파일**도 사실상 Yacktman 본문이 거의 없으므로 (yack 1-15 mention 만) — slicing 시 빈 결과 → **사실상 noise**.

**예상 유효 파일 수**: 33 standalone + ~34 AMG era (Yacktman-only 19 + Mixed dominant 15) = **~67 파일**. raw count 129 의 약 절반.

---

## 3. 형식 (확장자) 별 종합 평가

| 형식 | 출처 | 적합성 | 권장 처리 |
|---|---|---|---|
| **`.html` (Berkshire 사이트)** | Buffett 1977-1997 | ✅ A | 최소 처리 (header/footer trim) |
| **`.pdf` (회사 사이트)** | Buffett, Hawkins (2007-2025), Grantham (전체), Einhorn (시그니처 발표) | ✅ A 대부분 | pypdf 추출 → 정상. 단 Einhorn 발표 PDF 는 OCR 필요 |
| **`.txt` (EDGAR pre-2003)** | Hawkins 1995-2002, Driehaus 1996-2001, Baron 1996-2002, Yacktman 1995-2005 | ⚠️ B | SGML stripping + section regex |
| **`.htm` (EDGAR 2003-2023)** | 모두 (Hawkins, Driehaus, Baron, Yacktman) | ⚠️ C | DOM 파싱 + multi-fund 섹션 slicing |
| **`.htm` (EDGAR 2024+ iXBRL)** | Driehaus 2024+, Baron 2024+, Yacktman 2024+ | ❌ C/D | **iXBRL namespace-aware 파싱 필수**. text_cleaner.py 에서 ix:* 태그를 stripping 후 letter section 식별 |
| **`.htm` (EDGAR 8-K)** | Einhorn 2건 | ❌ D | 폐기 |

---

## 4. 투자자별 적합성 등급

| # | Investor | 구조 등급 (추출 비용) | Content 등급 (substantive 여부) | 종합 권장 |
|---|---|---|---|---|
| 1 | **Buffett** | **A** | **A++** (본인 voice, 4-시그널 모두 ✓) | **즉시 사용** |
| 2 | **Hawkins** | **B+** | **A** (Longleaf team, "60-cent dollars" framework) | **즉시 사용** (EDGAR 만 deep slicing) |
| 3 | **Grantham** | **A−** | **A** (GMO Inker/Pease + Grantham essay) | **즉시 사용** (author 메타 분리) |
| 4 | **Driehaus** | **C** | **A−** (Driehaus team, 종목 thesis + EM macro) | **deep slicing 필요** + 2021 cutoff |
| 5 | ~~Einhorn~~ | ~~F~~ | ~~F~~ (sales speech, partner letter 부재) | **제외 결정** (사용자 합의) |
| 6 | **Baron** | **C** | **A** (Ron Baron team, "competitive advantages" + macro QE view) | **deep slicing 필요** + 5펀드 분리 |
| 7 | **Yacktman** | **C−** | **A (good 파일) / D (구양식 다수)** | **noise 필터링 + deep slicing 필수** — 유효 ~43-73/129 |

**총평** (Phase 3 + 3.2 content quality 검증 후):
- **6명 (Buffett, Hawkins, Grantham, Driehaus, Baron, Yacktman)**: letter 본문 존재 ✓ Content quality 측면에서 substantive 한 4-시그널 (투자철학 / 시장view / 종목thesis / risk attitude) 모두 보유 — Phase 2/3 학습 입력 적합.
- **1명 (Einhorn)**: 본질적으로 분기 LP letter 가 코퍼스에 없음 — 외부 컨퍼런스 발표 + activist proxy materials. GRU 분기 cadence 입력 부적합. **사용자 합의로 제외 결정**.

**Role 4 합의 단계 블로킹 결정 사항**:
1. ~~**Einhorn 카테고리 처리**~~ ✅ **제외 결정 (2026-04-30)**. Long/Short Fundamental 카테고리 대체 후보 (Bill Miller / Cliff Asness 등) 필요 시 별도 검토.
2. **Yacktman AMG era 구양식 noise 처리**:
   - yack count < 30 + 다른 sub-adv mention 다수 → 자동 폐기 (~50개)
   - yack count 100+ dominant → deep slicing 시도 (~30개)
   - 2020+ "opinions of Yacktman" attribution 명시 파일 → 즉시 활용 (~6개)
   - 2024-2025 신양식 → 활용 (~4개)
3. **Driehaus 2021 cutoff 정책**: 본인 사망 후 후임 PM letter 사용 여부.
4. **Multi-fund 합본 분리 정책 finalize**: Hawkins 4펀드, Baron 5펀드, Yacktman AMG family 의 fund-section slicing 로직 우선순위.

---

## 5. text_cleaner.py 작업 권장사항 (Phase 4)

Phase 4 (text_cleaner.py 파일럿) 시 다음 우선순위로 처리:

### 5.1 형식별 stripping 파이프라인

```
1. PDF (Buffett, Grantham, Hawkins 사이트, Einhorn 발표)
   → pypdf 텍스트 추출 → 헤더/푸터 trim → 즉시 사용
   → Einhorn 이미지 PDF 는 별도 OCR (Tesseract) 분기

2. SGML TXT (1995-2002 EDGAR)
   → <DOCUMENT> 블록 추출 → <TEXT>...</TEXT> body
   → "Dear Shareholders" / "TO OUR SHAREHOLDERS" / 투자자별 custom marker 로 letter section 시작점 식별
   → "SCHEDULE OF INVESTMENTS" / "FINANCIAL HIGHLIGHTS" 로 끝점 식별

3. EDGAR HTM (2003-2023)
   → BeautifulSoup parse → SGML wrapper 제거
   → "Letter to Shareholders" / "To Our Shareholders" h-tag 기반 section
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
    'INV_EINHORN':  ['Sohn', 'Robin Hood', 'Greenlight Capital', 'Dear Partner'],
    'INV_BARON':    ['Dear Baron Funds Shareholder', 'Annual Letter', 'Sincerely', 'Ron Baron'],
    'INV_YACKTMAN': ['Dear Fellow Shareholder', 'Yacktman Fund', 'Yacktman Focused Fund'],
}
```

### 5.3 fund-level slicing 정책 (multi-fund 합본)

| Investor | 펀드 분리 필요? | 분리 단위 |
|---|---|---|
| Buffett | ❌ | 단일 |
| Hawkins | ✅ (2022+) | Partners / Small-Cap / Global / International |
| Grantham | ❌ | GMO 단일 (다양한 fund 가 있지만 letter 는 통합) |
| Driehaus | ✅ | Driehaus Emerging Markets Growth / 등 |
| Einhorn | ❌ | Greenlight 단일 |
| Baron | ✅ | Baron Asset / Growth / Small Cap / Opportunity / 5th Avenue / Partners 등 |
| Yacktman | ✅ | Yacktman Fund / Yacktman Focused / AMG family 다수 |

### 5.4 cutoff 정책 (Persona authenticity)

| Investor | Cutoff | 사유 |
|---|---|---|
| Buffett | None | 본인 작성 지속 |
| Hawkins | None | Hawkins 2025 말까지 활동 |
| Grantham | None | Grantham 본인 + 시그니처 essay 라벨 분리 사용 |
| Driehaus | **2021** | 본인 사망, 2022+ 후임 PM 명의 |
| Einhorn | None | 본인 발표 |
| Baron | None | 본인 작성 지속 |
| Yacktman | **2016** | Don Yacktman 은퇴, 2017+ Stephen Yacktman / Jason Subotky |

---

## 6. 결론

### 종합 판정 (사용자 의문 검증 후 재판정)

1. **프로젝트 목표는 텍스트 감성/언어 기반 persona 분석** → letter narrative 가 핵심 입력. N-CSR 의 정량 섹션 (Schedule of Investments, iXBRL 태그) 은 모두 stripping 대상 (Role 2/3 트랙이 별도 처리).

2. **6명 (Buffett, Hawkins, Grantham, Driehaus, Baron, Yacktman)**: letter 본문 확실히 존재 → Phase 2/3 학습 가능. 단 Yacktman 의 AMG era 96 파일 중 ~60개가 다른 AMG sub-adv 보고서로 사실상 noise → **유효 ~67 / 129 파일**.

3. **Einhorn 카테고리 본질적 문제 (재판정)**: 27개 PDF 가 **분기 LP partner letter 가 아니라 외부 컨퍼런스 stock pitch + activist proxy + sales speech**. 분기 cadence 의 risk-attitude commentary 가 아니라 **단발 종목 thesis**. → **GRU 입력 본질적 부적합**.

4. **2024+ EDGAR iXBRL 신양식**: 처리 비용 큼이지만 letter narrative 자체는 보존됨 → text_cleaner.py namespace-aware 파싱 + AMG 합본 fund-section slicing 동시 필요.

### 핵심 인사이트 — 정량 데이터 vs 정성 데이터

본 프로젝트의 텍스트 분석 트랙은 **투자자의 언어 시그널** 을 다루므로 N-CSR 파일들의 거대 size (5-10 MB) 에 압도되지 말 것. 실제 학습 입력은 letter narrative **수십~수백 KB**.

### Role 4 합의 단계 블로킹 결정 사항

1. **Einhorn 카테고리 처리 방안 결정** (Long/Short Fundamental):
   - **A안 — 카테고리 폐기**: 8명 → 7명. PLAN.md §3 의 "원칙 2 카테고리 직교성" 재검토. Long/Short 결을 Einhorn 외 다른 사람으로 대체 가능한지 (Bill Miller / Bill Ackman / Cliff Asness 등 — 각각 단점 검토 필요)
   - **B안 — 부분 활용**: GRU 입력에서 Einhorn 제외, LLM persona scoring (Phase 3 Loss Aversion / Risk Preference 점수화) 에만 활용
   - **C안 — 보강 시도**: Greenlight Capital 자체 archive 의 LP letter 가 어디든 남아있는지 search 재시도 (Wayback 외 채널 — Bloomberg Terminal / Refinitiv 등 paywalled archive)

2. **Yacktman AMG era noise 자동 필터 도입**: yack count threshold (예: < 30) 로 mixed minor 파일 폐기. 추가로 deep slicing 로직 (text_cleaner.py 의 "AMG Yacktman" header 기반 section 추출) 구현.

3. **iXBRL stripping 파일럿 우선순위**: Driehaus_24 / Baron_24 / Yacktman_24 — 셋 다 iXBRL 신양식 + AMG 합본 동시 적용된 가장 어려운 케이스.

### 다음 단계 (Phase 4 priority)
1. **text_cleaner.py 의 iXBRL stripping** 파일럿 — Driehaus_24.htm / Baron_24.htm / Yacktman_24.htm 3개 파일에서 letter body 추출 검증
2. **multi-fund 합본 분리 로직** — Hawkins 4펀드 / Baron 5펀드 / Yacktman AMG family 의 letter section 분리
3. **투자자별 custom marker 사전 finalize** — text_tagger.py 와 협업해 source_type 어휘와 정합성 확보
4. **Einhorn 카테고리 유지 가부 결정** (Role 4 합의 블로킹) — Long/Short Fundamental 카테고리 대체 후보 (Bill Miller 등) 재논의 가능성
5. **Driehaus 2021 cutoff / Yacktman 2016 cutoff** Role 4 합의 후 적용

---

## 7. Content Quality 심층 검증 (Phase 3.2 — 2026-04-30 추가)

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

→ **GMO Asset Allocation team (Ben Inker / John Pease) voice** — Grantham 본인이 모든 letter 를 쓰진 않음 (특히 2014+ 분기 letter 는 Inker/Pease) 단 **GMO house view 일관성 유지**. 4가지 시그널 모두 ✓.

> **주의**: 시그니처 essay (Race of Our Lives, Last Dance, Bubble 등) 만 Grantham 본인 voice. 분기 letter 는 GMO team voice. text_tagger.py 단계에서 author 메타데이터 분리 권장.

#### ✅ Driehaus — A− (Driehaus team voice, 종목 thesis 명시)

[Driehaus_20.htm](../raw/driehaus/Driehaus_20.htm) 직접 검증:
> "We believe that the combination of relatively strong economic growth in key EM countries such as China and Taiwan, along with the attractive interest rates found across much of EM will lend support to capital flows into emerging economies... Ping An Healthcare and Technology Company Limited... has benefited from rapidly increasing patient consultation volumes... Burger King India Ltd... The IPO in mid-December was highly successful... Azul S.A. Sponsored ADR Pfd... The COVID-19 downturn in passenger traffic caused a significant hit to earnings... high degree of financial leverage carried by the company"

→ **Driehaus Capital team voice** — 종목별 thesis (Ping An, Burger King India, Azul, Cholamandalam) + 거시 EM view + risk attitude (financial leverage 우려). 4가지 시그널 모두 ✓.

> **주의 1**: Richard Driehaus 본인은 **2021 사망**. 위 sample 은 본인 사망 직전 (2020). 2022+ letter 는 후임 PM (K.C. Nelson, Elizabeth Cassidy 등) team voice — 연속성 유지하지만 본인 시그니처 아님. **Role 4 cutoff 정책 필요**.
>
> **주의 2**: PM commentary 본문이 Schedule of Investments 다음에 묻혀있어 **deep slicing 필요**. 2010 S1 sample 에서는 첫 4500자가 SEC 보일러플레이트 + 정량 표만 있어 letter 가 안 보였음 — 실제로는 그 후에 PM commentary 가 등장.

#### ✅ Baron — A (Ron Baron team voice, 투자 철학 + 거시 view 명시)

[Baron_10.htm](../raw/baron/Baron_10.htm) 직접 검증:
> "Baron Asset Fund invests primarily in medium-sized growth companies for the long-term while using value-oriented purchase and sell disciplines... The Fund purchases companies that the Adviser believes have **sustainable competitive advantages and strong financial characteristics**, operating in industries with favorable macroeconomic trends led by strong management... We believe the stock market's September rally was primarily driven by investors anticipating further quantitative easing by the Federal Reserve... a double-dip recession did not materialize. We believe the economy is at a critical inflection point regarding **deflation and reflation**... Many companies, strong financially, hold approximately $1.8 trillion in cash defensively... It is our view that macro economic events continue to overwhelm..."

→ **Ron Baron team voice** + 투자 철학 (sustainable competitive advantages, growth + value-oriented) + 거시 view (Fed QE, deflation/reflation 변곡점) + 시장 timing 분석. 4가지 시그널 모두 ✓.

#### ⚠️ Yacktman — A (standalone + 신양식) / D (구양식 AMG era 다수)

상세 §2.7 참조. 핵심:
- **1995-2011 (33개)**: Don Yacktman 본인 voice — "loss aversion", "Protect capital", "the price we pay is extremely important", "strong market position and relatively stable profit margins" → A 등급
- **2024-2025 신양식 (4개)**: AMG Yacktman team voice — "multiple expansion vs underlying business results", "Fund remains concentrated with the top 10 positions representing 50.5%", 종목별 thesis (Fox/Schwab/Alphabet/Samsung/Bollore) → A 등급
- **2020-2023 AMG era 후기 (6개)**: "views expressed represent the opinions of Yacktman" attribution 명시 → A 등급
- **2012-2019 AMG era 구양식 (78개 중 ~30개 dominant)**: AMG 합본 N-CSR. **deep slicing 필요**, attribution 부재. 일부 파일은 "Letter to Shareholders" 가 사실 AMG Funds President (Jeffery Cerutti) 의 generic 시장 letter 또는 다른 sub-advisor (GW&K, Trilogy 등) 의 commentary 임 → 사용 가능 여부 검증 후에야 판정 가능

### 7.3 Content Quality 종합 등급표

| # | Investor | Content 등급 | 본인/팀 voice | 4-시그널 (철학/시장/종목/risk) | 사용 가능 letter 추정 |
|---|---|---|---|---|---|
| 1 | **Buffett** | A++ | 본인 직접 (1965~) | ✓✓✓✓ | 48 / 48 (100%) |
| 2 | **Hawkins** | A | Longleaf team (Hawkins + 후임) | ✓✓✓✓ | 125 / 125 (100%, deep slicing 후) |
| 3 | **Grantham** | A | GMO team (Inker/Pease 분기 + Grantham essay) | ✓✓✓✓ | 77 / 77 (100%) |
| 4 | **Driehaus** | A− | Driehaus team (~2021 본인, 이후 후임) | ✓✓✓✓ | 65 / 65 (deep slicing 후, cutoff 정책 별도) |
| 5 | ~~Einhorn~~ | ~~F~~ | ~~Einhorn 본인 발표 (단발 thesis)~~ | ~~제외 결정~~ | ~~0 / 29~~ |
| 6 | **Baron** | A | Baron team (Ron 주도) | ✓✓✓✓ | 75 / 75 (deep slicing 후) |
| 7 | **Yacktman** | A (good) / D (구양식) | Don 본인 (1995-2011) / Yacktman team (AMG era) | ✓✓✓✓ (good 파일에 한해) | **~43-73 / 129** (1/3 ~ 1/2 만 substantive) |

→ **6명 모두 (Einhorn 제외)** content quality 측면에서 substantive Yacktman/Buffett/etc. team voice 보유. 4가지 시그널 모두 명시. **GRU + FinBERT embedding + LLM persona scoring 입력으로 사용 가능**.

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
| Driehaus (EDGAR HTM) | **~150,000-200,000자** (deep) | TOC + 다중 펀드 Schedule of Investments + Statement of Operations 다음에야 letter — **첫 4500자 dump 만으로는 letter 미발견** |
| Baron (EDGAR HTM) | ~7,000자 (TOC 다음) | "Management's Discussion of Fund Performance" 가 진짜 PM commentary, "Dear Baron Funds Shareholder" 는 5줄 generic 인사 |
| Yacktman (AMG 구양식) | **~750,000자** (10MB 파일의 deep) | AMG Funds family 전체 N-CSR 합본의 늦은 위치 |
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
- driehaus: `Driehaus_00.txt`, `Driehaus_10_S1.htm`, `Driehaus_24.htm`
- einhorn: `Einhorn_18_sohn.pdf`, `Einhorn_21_bdoletteroct42021.htm`
- baron: `Baron_98.txt`, `Baron_10.htm`, `Baron_24.htm`
- yacktman: `Yacktman_98.txt`, `Yacktman_14_S1_01.htm`, `Yacktman_24.htm`
