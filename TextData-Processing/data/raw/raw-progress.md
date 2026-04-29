# Role 1 — Raw Data Collection Progress

> **Last updated**: 2026-04-29
> **Scope**: PLAN.md §2 의 8명 투자자 텍스트 코퍼스 수집 진행 현황 + 분기 정렬을 위한 추가 작업 정의.
> **Storage policy**: 본 파일을 제외한 `data/raw/` 하위 모든 파일은 `.gitignore` 처리. 무거운 원본은 commit 되지 않음.

---

## TL;DR — 7명 진행률

| # | Investor | 상태 | 시계열 커버 | Native cadence | 파일 형식 | 파일 수 | 디스크 |
|---|---|---|---|---|---|---|---|
| 1 | **Buffett** | ✅ 수집 완료 | 1977~2024 (48y) | 연간 | HTML(1977-1997) + PDF(1998-2024) | 48 + 6 stub | 8.9 MB |
| 2 | **Hawkins** | ✅ 수집 완료 | 1996~2026 (30y) | 1996-2021 반기 → 2022~ 분기 | PDF(site) + HTML/TXT(EDGAR) | 125 | 82 MB |
| 3 | Grantham | ⏳ 미착수 | — | 분기 letter (2010~) + 시그니처 essay | — | — | — |
| 4 | Driehaus | ⏳ 미착수 | — | 분기 (예상) | — | — | — |
| 5 | Einhorn | ⏳ 미착수 | — | 분기 (예상) | — | — | — |
| 6 | Baron | ⏳ 미착수 | — | 분기 (예상) | — | — | — |
| 7 | Yacktman | ⏳ 미착수 | — | 반기 (예상) | — | — | — |

**Aggregate**: 173 파일 / ~91 MB (Phase 1 파일럿 2명 완료)

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
[data/raw/buffett/](buffett/) — 48개 본문 + 6개 stub HTML, 8.9 MB

### 분기 데이터 확보를 위한 추가 단계

연간 → 분기 정렬을 위한 옵션 4가지 (택 1 또는 조합):

1. **Carry-forward (가장 간단)**: 연간 letter 를 그 해의 4개 분기에 동일하게 적용. Persona 가 1년 단위로 변하는 가정 → Phase 2 GRU 의 분기 시계열엔 동일 입력 4번 반복.
2. **AGM Q&A transcript 보충** (PLAN.md §2 표에서 명시): Berkshire 연차 주주총회(매년 5월) Q&A 녹취록을 추가 수집. 단발성이라 분기 갭은 여전히 존재 → carry-forward 와 결합 필요.
3. **분기 13F 발표 시점 참고용 스니펫**: 분기 13F 공개일 (보통 quarter end + 45일) 즈음의 언론 인터뷰/CNBC interview transcript 를 보조 텍스트로. 데이터 양 적음.
4. **분기 분할 (chunking)**: 연간 letter 를 의미 단위(예: 사업 부문별 섹션)로 분할 후 각 chunk 를 분기에 매핑 — 인공적이라 비추천.

**권장**: 1번 (carry-forward) + 2번 (AGM transcript) 조합. AGM transcript 는 별도 수집 작업 필요 (Berkshire 공식 transcript 비공개, CNBC/Yahoo 보도 archive 또는 fan transcription 사이트 — wisdomvalue.com, brkletters.com 등).

---

## INV_HAWKINS — Mason Hawkins

### 수집된 자료
Longleaf Partners Funds (Partners / Small-Cap / International / Global) 의 shareholder letter 전체 시계열. 사이트와 SEC EDGAR 두 채널 병행 수집.

### 파일 형식 / 출처

**채널 1 — Southeastern 사이트** (`data/raw/hawkins/`, 57 PDFs, 23 MB)
- **2007~2014 (16 PDFs)**: Q1+Q3 만 (반기 보고를 분기 슬롯에 배치) — `https://southeasternasset.com/report/{q}q{yy}-quarterly-fund-report/` 직접 PDF, **합본** (4개 펀드)
- **2018-Q3, 2019-Q1 (2 PDFs)**: 동일 패턴
- **2022-Q4 ~ 2026-Q1 (39 PDFs)**: 분기 cadence, **펀드별 분리** — `https://southeasternasset.com/commentary/{q}q{yy}-{partners|small-cap|global}-fund-commentary/`

**채널 2 — SEC EDGAR Longleaf Partners Funds Trust (CIK 0000806636)** (`data/raw/hawkins/edgar/`, 68 docs, 57 MB)
- **1996-02 ~ 1999-08 (12 TXT)**: N-30D / N-30D/A — pre-Sarbanes-Oxley 양식, plain text. 동일 날짜 다수 필링은 펀드별 분리 (accession suffix 로 구분)
- **2000-02 ~ 2002-07 (5 TXT)**: N-30D, plain text
- **2002-07 (1 HTM)**: N-30D, HTML 양식 전환 시작
- **2003-02 ~ 2026-03 (48 HTM)**: N-CSR (annual, 매년 2월) + N-CSRS (semi-annual, 매년 8월). 4개 펀드 합본 + financial statements + holdings 모두 단일 HTML 에 embedded. "To Our Shareholders" 섹션이 letter 본문.

### Cadence

| 기간 | Native cadence | 출처 |
|---|---|---|
| 1996-2002 | 반기 (Feb + Aug N-30D) | EDGAR |
| 2003-2021 | 반기 (Feb N-CSR + Aug N-CSRS) | EDGAR (사이트엔 일부만) |
| 2022 Q4 ~ | 분기 (per-fund 분리) | 사이트 |

**중요**: 2014-2021 사이의 사이트 listing 갭은 EDGAR 채널이 모두 메움. **누락 분기 없음**.

### 저장 위치
- [data/raw/hawkins/](hawkins/) — 사이트 PDF, 23 MB
- [data/raw/hawkins/edgar/](hawkins/edgar/) — EDGAR HTML/TXT, 57 MB

### 분기 데이터 확보를 위한 추가 단계

1. **반기 → 분기 carry-forward** (1996-2021): Feb letter (= 12-31 기준 annual report) 를 직전 Q4 + 다음 Q1 에 적용, Aug letter (= 6-30 기준 semi-annual) 를 그 해 Q2 + Q3 에 적용. (또는 다른 mapping 정책 — Role 4 합의 필요)
2. **펀드 합본 vs 분리 결정** (2022~): Partners/Small-Cap/Global 분기 letter 가 펀드별로 분리되어 있음. 옵션:
   - (a) 3개 펀드 letter 를 concat → 한 분기당 단일 row
   - (b) Partners Fund 만 사용 (Hawkins 의 flagship)
   - (c) 3개 row 로 보존, source_type 에 펀드명 태그
3. **N-CSR HTML 에서 letter 섹션만 추출** (text_cleaner.py 작업): 1.5MB HTML → "To Our Shareholders" 섹션 시작점부터 다음 헤딩까지 추출. financial statements / holdings table 은 제외. 정규식/`bs4` 헤딩 기반 분리.
4. **N-30D plain text 정리** (1996-2002): 옛 EDGAR 양식은 PostScript 잔재나 ASCII art 가 섞여 있을 수 있음. 인코딩 정규화 + 헤더/푸터 제거 필요.
5. **(선택) 1990-1995 추가 수집**: PLAN §2 의 "1990s~ (30y)" 가정에 부합하려면 EDGAR 1995 이전 필링 (NSAR-B 등 — letter 포함 여부 검증 필요) 또는 Wayback Machine 으로 사이트 archive 시도. 현재 1996 이 EDGAR 의 가장 오래된 N-30D.

---

## INV_GRANTHAM — Jeremy Grantham (GMO)  ⏳

### 예상 cadence / 출처
- **GMO 분기 letter** (`https://www.gmo.com/americas/research-library/`) — 2010~ 무료 PDF archive 직접 접근. 저자는 Grantham 본인 시그니처 essay + Ben Inker / James Montier 등 GMO 파트너 분기 letter
- **GMO 7-Year Asset Class Forecast** — 분기 단위 발행, gmo.com 별도 페이지
- **Grantham 시그니처 에세이**: 여름 essay, "Race of Our Lives", 주요 Bubble call (2000 dotcom, 2007 housing, 2021 SPAC/superbubble) 등 — gmo.com PDF로 보존

### PDF URL 패턴
`https://www.gmo.com/globalassets/articles/quarterly-letter/{YYYY}/{slug}_{author}_{q}{yyyy}.pdf`
예시:
- `quarterly-letter/2010/jeremygrantham_summeressays_2q2010.pdf`
- `quarterly-letter/2013/the-race-of-our-lives_jeremy-grantham_2013.pdf`
- `quarterly-letter/2023/gmo-quarterly-letter_1q-2023.pdf`

### 분기 데이터 확보를 위한 추가 단계
1. **Research library 인덱싱**: gmo.com/americas/research-library/ 에서 분기 letter 슬러그 수집 (Cloudflare 보호 있으나 PDF 엔드포인트는 표준 UA 로 접근 가능)
2. **시그니처 essay 별도 태깅**: source_type 을 `quarterly_letter` 와 `signature_essay` 로 분리. 시그니처 essay 는 분기 letter 에 carry-forward 또는 별도 row
3. **저자 필터링**: Grantham 본인 작성분 vs GMO 파트너 작성분을 메타데이터(`author` 컬럼 또는 `source_type` suffix)로 구분
4. **EDGAR 폴백**: GMO Trust (CIK 0000772129) N-CSR/N-CSRS — 펀드 commentary 보충용 (Hawkins 와 동일 전략)
5. **2010 이전 letter**: Wayback Machine 으로 gmo.com archive 시도, 2000~2009 분기 letter 일부 복원 가능성 (`Required Reading` 섹션에서 1Q2000, 1Q2007 등 일부 surface 됨)

### 13F 시계열과의 정렬
GMO LLC 의 13F-HR 은 2006-02-08 부터 (CIK 1352662, 81 filings, equity 100%). 분기 letter 가 2010~ 이라 2006-2009 의 4년 갭은 EDGAR N-CSR 또는 Wayback 으로 보충 시도.

---

## INV_DRIEHAUS — Richard Driehaus  ⏳

### 예상 cadence / 출처
- **Driehaus Capital 분기 commentary** — `https://www.driehaus.com/insights`

### 분기 데이터 확보를 위한 추가 단계
1. **사이트 스크래핑**: Hawkins 와 동일 패턴 — quarterly URL slug 발견 후 try-and-skip-404. Buffett/Hawkins 파일럿 코드 재사용 가능
2. **사이트 갭 발생 시 EDGAR 폴백**: Driehaus Capital Management CIK 검색 → N-30D / N-CSR 시계열 확보 (Hawkins 와 동일 전략)
3. **Note**: Driehaus 본인은 2021년 사망. 사후 letter 는 Driehaus 펀드 매니저(Jeff James 등) 명의. 분석 시 본인 vs 펀드 구분 필요

---

## INV_EINHORN — David Einhorn  ⏳

### 예상 cadence / 출처
- **Greenlight Capital 분기 letter** — 자체 사이트 letter 비공개, third-party archive 사용
- 1차 후보: `hedgefundalpha.com`, `valuewalk.com`, `marketfolly.com`

### 분기 데이터 확보를 위한 추가 단계
1. **Third-party archive 스크래핑**: hedgefundalpha.com 등은 Cloudflare 보호 가능성 — `insane-search` Phase 2 (TLS impersonation) 필요
2. **EDGAR 폴백** (강력): Greenlight Capital Re (GLRE 상장사) 또는 Greenlight Capital LP partnership 의 SEC 필링 — investor letter 가 종종 8-K 또는 supplementary 로 첨부됨
3. **분기 letter 가 native quarterly cadence** 라 carry-forward 불필요. 누락 분기 발생 시 그대로 row 생략

---

## INV_BARON — Ron Baron  ⏳

### 예상 cadence / 출처
- **Baron Funds 분기 letter** — `https://www.baronfunds.com/insights/quarterly-reports`
- **Baron Investment Conference** — 연 1회 (10월), 본인 keynote transcript

### 분기 데이터 확보를 위한 추가 단계
1. **사이트 스크래핑**: Baron 사이트는 비교적 정적, Hawkins 의 사이트 패턴 응용
2. **Conference transcript**: 매년 베어런 인베스트먼트 컨퍼런스 keynote — YouTube + 사이트 archive
3. **EDGAR 폴백**: Baron Capital Funds Trust CIK → N-CSR / N-CSRS (Hawkins 와 동일 전략)

---

## INV_YACKTMAN — Don Yacktman  ⏳

### 예상 cadence / 출처
- **Yacktman Funds 반기 letter** — `https://www.yacktman.com` (사이트 자체 빈약)
- **AMG Yacktman Focused Fund commentary** — AMG (운용 모회사) 사이트 / fund factsheet

### 분기 데이터 확보를 위한 추가 단계
1. **EDGAR 1차** (강력 추천): AMG Funds I (Yacktman Focused Fund 가 속한 trust) 또는 The Yacktman Funds, Inc. CIK 검색 → N-CSR / N-CSRS. Hawkins 와 정확히 동일 패턴
2. **반기 → 분기 carry-forward** (Hawkins 와 동일)
3. **Note**: Don Yacktman 은 2016년 은퇴, 이후 letter 는 Stephen Yacktman / Jason Subotky 명의. 본인 시그널 분석 시 2016년 cutoff 고려 필요 (PLAN §6 의 "각 투자자 활동 기간" 정책에 부합)

---

## Aggregate Stats

```
Buffett                  48 letters + 6 stubs           8.9 MB
Hawkins (site)            57 PDFs                       23  MB
Hawkins (EDGAR)           68 HTML/TXT (1996-2026)       57  MB
                       ──────────────────────────────────────
                         173 files                      89  MB
```

`.gitignore` 처리되어 commit 안됨. 본 `raw-progress.md` 만 화이트리스트로 commit 가능.

---

## Next Steps (priority order)

1. **Role 4 와 메타데이터 스키마 합의** (PLAN §9 step 3, 블로킹) — 특히 cadence 가 mixed (annual / semiannual / quarterly / 비정형) 인 점 반영해 `source_type` 어휘 + `chunk_id` 의미 + 펀드별 분리 정책 확정
2. **text_cleaner.py 파일럿** (Buffett + Hawkins 만 우선) — N-CSR HTML 에서 "To Our Shareholders" 섹션 추출, PDF→텍스트, 헤더/푸터 제거 → `data/interim/{investor}_{quarter}.xlsx`
3. **나머지 5명 수집**: 우선순위 — 사이트 정적인 Driehaus/Baron/Yacktman → EDGAR 활용 가능한 Einhorn → GMO Grantham (gmo.com PDF 정적 패턴, Buffett/Hawkins 스크래퍼 재사용)
4. **분기 cadence alignment 정책 확정**: §6 의 cadence 노트 표 기반으로 carry-forward / chunk 분할 / 다중 fund 처리 규칙을 text_tagger.py 단계에서 일괄 적용

---

## Reproducibility

수집은 [scripts/text_scraper.py](../../scripts/text_scraper.py) 단일 스크립트로 idempotent.

```bash
cd 2026-AIFinance-Project/TextData-Processing
python scripts/text_scraper.py              # buffett + hawkins (site + EDGAR)
python scripts/text_scraper.py buffett      # buffett only
python scripts/text_scraper.py hawkins      # hawkins site + EDGAR
python scripts/text_scraper.py hawkins-edgar  # EDGAR only (1996-2026 N-30D/N-CSR/N-CSRS)
```

이미 다운로드된 파일은 자동 skip. SEC EDGAR 호출은 정책 준수 UA + 0.3s rate-limit 적용 (10 req/s 제한 안에서 운용).
