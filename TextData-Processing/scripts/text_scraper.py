"""Role 1 — 통합 텍스트 수집 스크래퍼.

7명 투자자 letter/commentary 자료 수집. 모든 출력은 새 명명규칙 사용:
  Buffett_77.html, Hawkins_22_Q1_partners.pdf, Hawkins_95.txt, ...

소스
----
* Buffett   : berkshirehathaway.com (직접 letter HTML/PDF, 1977-2024)
* Hawkins   : southeasternasset.com (per-fund/combined PDF, 2007-2026) +
              SEC EDGAR Longleaf Partners Funds Trust (N-30D/N-CSR/N-CSRS, 1996-)
* Grantham  : gmo.com Research Library (분기 letter PDF, 2010-)
* Driehaus  : SEC EDGAR Driehaus Mutual Funds (N-CSR/N-CSRS)
* Einhorn   : Greenlight Re (GLRE) 8-K + 시도용 (hedge fund letters 비공개)
* Baron     : SEC EDGAR Baron Investment Funds Trust + Baron Capital Funds Trust
* Yacktman  : SEC EDGAR Yacktman Fund Inc + AMG Funds (등록 전후 모두)

idempotent: 이미 존재 + 0이 아닌 파일은 skip. EDGAR 호출은 정책 준수 UA + 0.3s rate-limit.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Iterable

import requests

# 같은 폴더의 _naming.py
sys.path.insert(0, str(Path(__file__).parent))
from _naming import fname, edgar_period_from_filing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA, "Accept": "*/*"}

EDGAR_HEADERS = {
    "User-Agent": "InvestorDNA Research yangwhyun99@gmail.com",
    "Accept": "*/*",
}

REQUEST_DELAY_SEC = 0.3
TIMEOUT = 30


# ---------------------------------------------------------------------------
# Common: download
# ---------------------------------------------------------------------------
def download(
    url: str,
    dest: Path,
    *,
    expect_pdf: bool = False,
    headers: dict[str, str] | None = None,
) -> str:
    """Returns one of: 'ok', 'skip', '404', 'err'. Logs to stdout."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip   {dest.name}")
        return "skip"
    try:
        r = requests.get(
            url,
            headers=headers or HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        print(f"  ERR    {url} -- {e}")
        return "err"

    if r.status_code == 404:
        print(f"  404    {url}")
        return "404"
    if r.status_code == 403:
        print(f"  403    {url}")
        return "err"
    if r.status_code != 200:
        print(f"  HTTP{r.status_code} {url}")
        return "err"

    body = r.content
    if expect_pdf and not body.startswith(b"%PDF"):
        ctype = r.headers.get("Content-Type", "?")
        print(f"  WARN   not a PDF ({ctype}): {url}")
        return "err"

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    print(f"  OK     {len(body) // 1024:>5} KB  {dest.name}")
    time.sleep(REQUEST_DELAY_SEC)
    return "ok"


def fetch_text(url: str, headers: dict[str, str] | None = None) -> str | None:
    """텍스트 응답 다운로드 (HTML 파싱용). 실패 시 None."""
    try:
        r = requests.get(url, headers=headers or HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.text
        print(f"  fetch_text HTTP{r.status_code} {url}")
        return None
    except requests.RequestException as e:
        print(f"  fetch_text ERR {url} -- {e}")
        return None


# ---------------------------------------------------------------------------
# Buffett
# ---------------------------------------------------------------------------
BUFFETT_BASE = "https://www.berkshirehathaway.com/letters"
BUFFETT_HTML_ONLY = range(1977, 1998)
BUFFETT_STUB_RANGE = range(1998, 2004)
BUFFETT_PDF_RANGE = range(2004, 2025)
_PDF_HREF_RE = re.compile(r'HREF="([^"]+\.pdf)"', re.IGNORECASE)


def _parse_first_pdf_href(stub_path: Path) -> str | None:
    if not stub_path.exists():
        return None
    text = stub_path.read_text(encoding="utf-8", errors="replace")
    m = _PDF_HREF_RE.search(text)
    return m.group(1) if m else None


def scrape_buffett(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    for year in BUFFETT_HTML_ONLY:
        url = f"{BUFFETT_BASE}/{year}.html"
        dest = out_dir / fname("Buffett", year, ext="html")
        counts[download(url, dest)] += 1
    for year in BUFFETT_STUB_RANGE:
        # stub 은 PDF 링크 추출용 임시 파일 — 영구 저장하지 않음 (텍스트 내용 0)
        pdf_dest = out_dir / fname("Buffett", year, ext="pdf")
        if pdf_dest.exists() and pdf_dest.stat().st_size > 0:
            print(f"  skip   {pdf_dest.name}")
            counts["skip"] += 1
            continue
        stub_url = f"{BUFFETT_BASE}/{year}.html"
        try:
            r = requests.get(stub_url, headers=HEADERS, timeout=TIMEOUT)
        except requests.RequestException as e:
            print(f"  ERR    stub fetch {stub_url} -- {e}")
            counts["err"] += 1
            continue
        if r.status_code != 200:
            print(f"  HTTP{r.status_code}  {stub_url}")
            counts["err"] += 1
            continue
        m = _PDF_HREF_RE.search(r.text)
        if not m:
            print(f"  WARN   no pdf link in {year}.html stub")
            counts["err"] += 1
            continue
        pdf_url = f"{BUFFETT_BASE}/{m.group(1)}"
        counts[download(pdf_url, pdf_dest, expect_pdf=True)] += 1
    for year in BUFFETT_PDF_RANGE:
        url = f"{BUFFETT_BASE}/{year}ltr.pdf"
        dest = out_dir / fname("Buffett", year, ext="pdf")
        counts[download(url, dest, expect_pdf=True)] += 1
    return counts


# ---------------------------------------------------------------------------
# Hawkins (Southeastern site)
# ---------------------------------------------------------------------------
HAWKINS_BASE = "https://southeasternasset.com"
HAWKINS_FUNDS = ("partners", "small-cap", "global")
HAWKINS_NEW_YEARS = range(22, 27)
HAWKINS_OLD_YEARS = range(7, 22)
QUARTERS = (1, 2, 3, 4)


def _yy_to_year(yy_int: int) -> int:
    return 2000 + yy_int if yy_int < 70 else 1900 + yy_int


def scrape_hawkins(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}

    for yy_int in HAWKINS_NEW_YEARS:
        year = _yy_to_year(yy_int)
        for q in QUARTERS:
            for fund in HAWKINS_FUNDS:
                tag = "smallcap" if fund == "small-cap" else fund
                slug = f"{q}q{yy_int:02d}-{fund}-fund-commentary"
                url = f"{HAWKINS_BASE}/commentary/{slug}/"
                dest = out_dir / fname(
                    "Hawkins", year, quarter=q, tags=[tag], ext="pdf"
                )
                counts[download(url, dest, expect_pdf=True)] += 1

    for yy_int in HAWKINS_OLD_YEARS:
        year = _yy_to_year(yy_int)
        for q in QUARTERS:
            slug = f"{q}q{yy_int:02d}-quarterly-fund-report"
            url = f"{HAWKINS_BASE}/report/{slug}/"
            dest = out_dir / fname("Hawkins", year, quarter=q, ext="pdf")
            counts[download(url, dest, expect_pdf=True)] += 1

    return counts


# ---------------------------------------------------------------------------
# EDGAR generic — N-CSR / N-CSRS / N-30D 다운로더
# ---------------------------------------------------------------------------
LETTER_FORMS_DEFAULT = (
    "N-CSR", "N-CSRS", "N-CSR/A", "N-CSRS/A", "N-30D", "N-30D/A"
)


def scrape_edgar_funds(
    investor_name: str,
    cik: str,
    out_dir: Path,
    *,
    forms: Iterable[str] = LETTER_FORMS_DEFAULT,
) -> dict[str, int]:
    """SEC EDGAR submissions JSON 으로부터 N-CSR/N-CSRS/N-30D 일괄 다운로드.

    이름은 _naming.fname 로 새 규칙 적용. 같은 (year, period) 다중 필링은
    filing month 또는 sequence 로 disambiguate.
    """
    forms_set = set(forms)
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    cik_padded = cik.lstrip("0").rjust(10, "0")
    sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

    try:
        r = requests.get(sub_url, headers=EDGAR_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERR    submissions fetch: {e}")
        counts["err"] += 1
        return counts

    data = r.json()
    company = data.get("name", "?")
    print(f"  EDGAR  {company} (CIK {cik_padded})")

    # submissions.json 에는 'recent' 와 'files' (older filings).
    # 우리는 일단 recent 만 처리. 1000건 한도이므로 charset 부족 시 더 수집 필요.
    recent = data["filings"]["recent"]
    rows = list(zip(
        recent["form"],
        recent["filingDate"],
        recent["accessionNumber"],
        recent["primaryDocument"],
    ))

    # 추가 older filings (data["filings"]["files"]) 가 있으면 가져옴
    older_files = data["filings"].get("files", [])
    for older in older_files:
        oname = older.get("name")
        if not oname:
            continue
        ourl = f"https://data.sec.gov/submissions/{oname}"
        try:
            rr = requests.get(ourl, headers=EDGAR_HEADERS, timeout=TIMEOUT)
            time.sleep(REQUEST_DELAY_SEC)
            if rr.status_code != 200:
                continue
            od = rr.json()
            rows.extend(list(zip(
                od.get("form", []),
                od.get("filingDate", []),
                od.get("accessionNumber", []),
                od.get("primaryDocument", []),
            )))
        except (requests.RequestException, ValueError):
            continue

    # 필터링: letter forms 만
    rows = [r for r in rows if r[0] in forms_set]
    if not rows:
        print(f"  WARN   no matching forms found for CIK {cik_padded}")
        return counts

    # Pass 1: parse 모두
    parsed: list[tuple[str, str, str, str, int, str | None, str]] = []
    # (date, form, acc, primary, year, period, ext)
    for form, date, acc, primary in rows:
        acc_nodash = acc.replace("-", "")
        if not primary:
            primary = _resolve_primary_doc(cik_padded, acc_nodash)
            if not primary:
                continue
        ext = (Path(primary).suffix or ".htm").lstrip(".").lower()
        if ext == "html":
            ext = "htm"
        year, period = edgar_period_from_filing(date, form)
        parsed.append((date, form, acc_nodash, primary, year, period, ext))

    # Pass 2: 같은 (year, period, ext) 그룹 식별
    target_groups: dict[tuple[int, str | None, str], list] = {}
    for item in parsed:
        date, form, acc, primary, year, period, ext = item
        target_groups.setdefault((year, period, ext), []).append(item)

    # Pass 3: 다운로드
    for key, items in target_groups.items():
        year, period, ext = key
        # date 로 정렬
        items.sort(key=lambda x: x[0])
        # 동일 filing date 다중 acc 처리 + 다른 filing date 그룹화
        by_date: dict[str, list] = {}
        for item in items:
            by_date.setdefault(item[0], []).append(item)
        dates_sorted = sorted(by_date.keys())
        is_multi_date = len(dates_sorted) > 1

        for date_idx, date in enumerate(dates_sorted):
            grp = by_date[date]
            for sub_idx, item in enumerate(grp):
                date, form, acc, primary, year_, period_, ext_ = item
                extras: list[str] = []
                if is_multi_date and date_idx > 0:
                    fm = int(date.split("-")[1])
                    extras.append(_MONTHS[fm - 1])
                if len(grp) > 1 and sub_idx > 0:
                    extras.append(f"a{acc[-6:]}")
                extra = "_".join(extras) if extras else None
                # primary 의 prefix 가 'primary_doc.xml' 같은 경우 → ext 가 xml
                # 텍스트가 아닌 형식은 skip
                if ext_ in ("xml", "json", "xsd"):
                    continue
                dest = out_dir / fname(
                    investor_name,
                    year_,
                    semi=1 if period_ == "S1" else (2 if period_ == "S2" else None),
                    extra=extra,
                    ext=ext_,
                )
                url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik_padded)}/{acc}/{primary}"
                )
                counts[download(url, dest, headers=EDGAR_HEADERS)] += 1

    return counts


_MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]


def _resolve_primary_doc(cik_padded: str, acc_nodash: str) -> str | None:
    """필링 폴더 인덱스에서 본 문서 추정. Cert/exhibit 제외 후 최대 크기."""
    idx_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{int(cik_padded)}/{acc_nodash}/index.json"
    )
    try:
        r = requests.get(idx_url, headers=EDGAR_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        items = r.json().get("directory", {}).get("item", [])
    except (requests.RequestException, ValueError):
        return None

    candidates = []
    for it in items:
        name = it.get("name", "")
        size = int(it.get("size") or 0)
        low = name.lower()
        if not name or "index" in low or low.endswith((".jpg", ".gif", ".png", ".xml")):
            continue
        if "cert" in low or "ex99" in low or low.startswith("0001"):
            continue
        if not low.endswith((".htm", ".html", ".txt")):
            continue
        candidates.append((size, name))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


# ---------------------------------------------------------------------------
# Hawkins EDGAR (위 generic 호출)
# ---------------------------------------------------------------------------
LONGLEAF_CIK = "0000806636"


def scrape_hawkins_edgar(out_dir: Path) -> dict[str, int]:
    return scrape_edgar_funds("Hawkins", LONGLEAF_CIK, out_dir)


# ---------------------------------------------------------------------------
# Grantham (GMO)
# ---------------------------------------------------------------------------
GMO_BASE = "https://www.gmo.com"
# Sitemap 에서 발견된 quarterly letter URLs (정렬: 분기별 4개씩)
# 각 landing page 에서 PDF 링크 추출
GMO_LETTER_LANDING_URLS = [
    # 정형 분기 letter 페이지
    "/americas/research-library/1q-2010-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2010-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2010-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2010-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2011-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2011-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2011-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2011-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2012-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2012-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2012-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2012-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2013-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2013-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2013-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2013-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2014-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2014-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2014-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2014-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2015-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2015-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2015-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2015-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2016-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2016-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2016-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2016-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2017-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2017-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2017-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2017-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2018-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2018-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2018-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2018-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2019-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2019-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2019-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2019-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2020-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2020-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2020-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2020-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2021-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2021-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2021-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2021-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2022-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2022-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2022-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2022-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2023-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2023-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2023-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2023-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2024-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2024-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2024-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2024-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2025-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/2q-2025-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/3q-2025-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/4q-2025-gmo-quarterly-letter_gmoquarterlyletter/",
    "/americas/research-library/1q-2026-gmo-quarterly-letter_gmoquarterlyletter/",
]

# Sitemap 추가 발견 letter 들 (slug 가 자유로운 케이스)
GMO_NAMED_LANDING_URLS = [
    # (year, quarter, landing_url, label)
    (2026, 1, "/americas/research-library/its-probably-a-bubble-but-there-is-plenty-else-to-invest-in_gmoquarterlyletter/", "bubble"),
    (2025, 2, "/americas/research-library/american-unexceptionalism_gmoquarterlyletter/", "unexcept"),
    (2025, 1, "/americas/research-library/tariffs---making-the-us-exceptional-but-not-in-a-good-way_gmoquarterlyletter/", "tariffs"),
    (2024, 3, "/americas/research-library/trade-the-most-beautiful-word-in-the-dictionary_gmoquarterlyletter/", "trade"),
    (2024, 2, "/americas/research-library/bargain-value-trap-or-something-in-between_gmoquarterlyletter/", "bargain"),
    (2008, None, "/americas/research-library/its-everywhere-in-everything-the-first-truly-global-bubble_gmoquarterlyletter/", "globalbubble"),
    (2009, None, "/americas/research-library/is-this-purgatory-or-is-it-hell_gmoquarterlyletter/", "purgatory"),
    (2017, None, "/americas/research-library/dont-act-like-stalin-but-maybe-hire-portfolio-managers-that-do_gmoquarterlyletter/", "stalin"),
]

# landing page HTML 에서 PDF 링크를 찾는 정규식
_GMO_PDF_RE = re.compile(
    r'href="(https?://[^"]*?\.pdf[^"]*?|/[^"]*?\.pdf[^"]*?)"', re.IGNORECASE
)


def _resolve_gmo_pdf(landing_url: str) -> str | None:
    """landing page HTML 에서 PDF 다운로드 URL 추출."""
    full_url = landing_url if landing_url.startswith("http") else f"{GMO_BASE}{landing_url}"
    html = fetch_text(full_url)
    if not html:
        return None
    m = _GMO_PDF_RE.search(html)
    if not m:
        return None
    href = m.group(1)
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("/"):
        return f"{GMO_BASE}{href}"
    return href


_GMO_SITEMAP = "https://www.gmo.com/research-library/sitemap.xml"
_GMO_LOC_RE = re.compile(r"<loc>([^<]+_gmoquarterlyletter[^<]*)</loc>", re.IGNORECASE)
_GMO_DATE_META_RE = re.compile(
    r'<meta[^>]*name="article:published_time"[^>]*content="(\d{4})-(\d{2})',
    re.IGNORECASE,
)
_GMO_OG_DATE_RE = re.compile(
    r'<meta[^>]*property="article:published_time"[^>]*content="(\d{4})-(\d{2})',
    re.IGNORECASE,
)


def _slug_label(landing: str) -> str:
    """landing URL 끝의 slug 에서 사람읽기 좋은 라벨 추출."""
    # /americas/research-library/{slug}_gmoquarterlyletter/
    m = re.search(r"research-library/([^/]+)_gmoquarterlyletter", landing)
    if not m:
        return "letter"
    slug = m.group(1)
    # 단어 4개 정도까지만 보존하여 파일명 길이 제한
    words = re.split(r"[-_]", slug)
    # 의미 단어 추출 (불용어 제외)
    out = []
    for w in words:
        if not w:
            continue
        if len(out) >= 5:
            break
        out.append(w[:8])
    return "".join(out) or "letter"


def _gmo_year_quarter_from_slug(landing: str) -> tuple[int, int] | None:
    """slug에서 (year, quarter) 추출 시도."""
    # 패턴: '1q-2010' or '1q2018'
    m = re.search(r"(\d)q-?(\d{4})", landing)
    if m:
        q = int(m.group(1))
        year = int(m.group(2))
        if 1 <= q <= 4 and 1990 <= year <= 2100:
            return (year, q)
    return None


def _gmo_year_from_landing_meta(landing: str) -> tuple[int, int | None] | None:
    """landing page 의 <meta article:published_time> 에서 (year, quarter) 추출.

    quarter 는 month 로부터 추정.
    """
    full_url = landing if landing.startswith("http") else f"{GMO_BASE}{landing}"
    html = fetch_text(full_url)
    if not html:
        return None
    m = _GMO_DATE_META_RE.search(html) or _GMO_OG_DATE_RE.search(html)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2))
    quarter = (month - 1) // 3 + 1  # 1-3→Q1, 4-6→Q2, etc.
    return (year, quarter)


def _fetch_gmo_landing_urls() -> list[str]:
    """GMO research-library 사이트맵에서 모든 quarterly letter URL 수집."""
    txt = fetch_text(_GMO_SITEMAP)
    if not txt:
        return []
    urls = sorted(set(_GMO_LOC_RE.findall(txt)))
    return urls


def scrape_grantham(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}

    landings = _fetch_gmo_landing_urls()
    if not landings:
        print("  ERR    GMO sitemap fetch failed; falling back to hardcoded list")
        landings = [GMO_BASE + p for p in GMO_LETTER_LANDING_URLS]
        landings += [GMO_BASE + e[2] for e in GMO_NAMED_LANDING_URLS]

    print(f"  found  {len(landings)} GMO letter landing pages")

    for landing in landings:
        # 1) slug 에서 year+quarter 추출 시도
        yq = _gmo_year_quarter_from_slug(landing)
        label = None
        if yq is None:
            # 2) 메타데이터에서 추출 + slug 라벨 보존
            yq = _gmo_year_from_landing_meta(landing)
            label = _slug_label(landing)
            if yq is None:
                print(f"  SKIP   no date found: {landing}")
                counts["err"] += 1
                continue
        year, q = yq
        if label:
            dest = out_dir / fname(
                "Grantham", year, quarter=q, tags=[label], ext="pdf"
            )
        else:
            dest = out_dir / fname("Grantham", year, quarter=q, ext="pdf")
        if dest.exists():
            print(f"  skip   {dest.name}")
            counts["skip"] += 1
            continue
        pdf_url = _resolve_gmo_pdf(landing)
        if not pdf_url:
            print(f"  404    {landing}")
            counts["404"] += 1
            time.sleep(REQUEST_DELAY_SEC)
            continue
        counts[download(pdf_url, dest, expect_pdf=True)] += 1

    return counts


# ---------------------------------------------------------------------------
# Driehaus  (CIK 0001016073 — DRIEHAUS MUTUAL FUNDS)
# ---------------------------------------------------------------------------
DRIEHAUS_FUNDS_CIK = "0001016073"


def scrape_driehaus(out_dir: Path) -> dict[str, int]:
    return scrape_edgar_funds("Driehaus", DRIEHAUS_FUNDS_CIK, out_dir)


# ---------------------------------------------------------------------------
# Baron (두 trust)
# ---------------------------------------------------------------------------
BARON_TRUSTS = (
    ("0000810902", None),    # Baron Investment Funds Trust
    ("0001050084", None),    # Baron Capital Funds Trust
)


def scrape_baron(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    for cik, _ in BARON_TRUSTS:
        c = scrape_edgar_funds("Baron", cik, out_dir)
        for k in counts:
            counts[k] += c[k]
    return counts


# ---------------------------------------------------------------------------
# Yacktman:
#   - CIK 0000885980 = YACKTMAN FUND INC (1995-2011 standalone)
#   - CIK 0001089951 = AMG FUNDS (post-2012, Yacktman is one of many funds.
#                     N-CSR 본문에 Yacktman-specific letter 섹션 포함)
# ---------------------------------------------------------------------------
YACKTMAN_CIKS = ("0000885980", "0001089951")


def scrape_yacktman(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    # 첫 번째: 본인 entity (1995-2011)
    c1 = scrape_edgar_funds("Yacktman", YACKTMAN_CIKS[0], out_dir)
    for k in counts:
        counts[k] += c1[k]
    # 두 번째: AMG (2012-) — N-CSR 본문에 Yacktman 섹션 포함
    # 파일이 다른 fund 와 합본이라 'amg' 태그로 별도 표시.
    # min_filing_year=2012 — AMG 가 Yacktman 을 인수한 시점, 그 이전 N-CSR
    # 은 무관한 다른 fund 만 포함하므로 노이즈
    c2 = scrape_edgar_funds_tagged(
        "Yacktman", YACKTMAN_CIKS[1], out_dir, tag="amg", min_filing_year=2012
    )
    for k in counts:
        counts[k] += c2[k]
    return counts


def scrape_edgar_funds_tagged(
    investor_name: str,
    cik: str,
    out_dir: Path,
    *,
    tag: str,
    forms: Iterable[str] = LETTER_FORMS_DEFAULT,
    min_filing_year: int | None = None,
) -> dict[str, int]:
    """scrape_edgar_funds 와 동일하되 모든 출력 파일명에 추가 태그를 prepend.

    min_filing_year 가 지정되면 그 해 이전 필링은 스킵 (예: AMG fund 가
    Yacktman 을 인수하기 전 시기의 무관한 N-CSR 제외).
    """
    forms_set = set(forms)
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    cik_padded = cik.lstrip("0").rjust(10, "0")
    sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

    try:
        r = requests.get(sub_url, headers=EDGAR_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERR    submissions fetch: {e}")
        counts["err"] += 1
        return counts

    data = r.json()
    print(f"  EDGAR  {data.get('name','?')} (CIK {cik_padded}) tag={tag}")

    recent = data["filings"]["recent"]
    rows = list(zip(
        recent["form"],
        recent["filingDate"],
        recent["accessionNumber"],
        recent["primaryDocument"],
    ))
    older_files = data["filings"].get("files", [])
    for older in older_files:
        oname = older.get("name")
        if not oname:
            continue
        try:
            rr = requests.get(
                f"https://data.sec.gov/submissions/{oname}",
                headers=EDGAR_HEADERS, timeout=TIMEOUT
            )
            time.sleep(REQUEST_DELAY_SEC)
            if rr.status_code != 200:
                continue
            od = rr.json()
            rows.extend(list(zip(
                od.get("form", []),
                od.get("filingDate", []),
                od.get("accessionNumber", []),
                od.get("primaryDocument", []),
            )))
        except (requests.RequestException, ValueError):
            continue

    rows = [r for r in rows if r[0] in forms_set]
    # filing date 가 min_filing_year 이전이면 제외
    if min_filing_year is not None:
        rows = [
            r for r in rows
            if int(r[1].split("-")[0]) >= min_filing_year
        ]
    if not rows:
        print(f"  WARN   no matching forms found for CIK {cik_padded}")
        return counts

    parsed = []
    for form, date, acc, primary in rows:
        acc_nodash = acc.replace("-", "")
        if not primary:
            primary = _resolve_primary_doc(cik_padded, acc_nodash)
            if not primary:
                continue
        ext = (Path(primary).suffix or ".htm").lstrip(".").lower()
        if ext == "html":
            ext = "htm"
        year, period = edgar_period_from_filing(date, form)
        parsed.append((date, form, acc_nodash, primary, year, period, ext))

    # 동일 (year, period, ext) 그룹 → 인덱스로 disambiguate
    target_groups: dict[tuple[int, str | None, str], list] = {}
    for item in parsed:
        date, form, acc, primary, year, period, ext = item
        target_groups.setdefault((year, period, ext), []).append(item)

    for key, items in target_groups.items():
        year, period, ext = key
        items.sort(key=lambda x: x[0])
        by_date: dict[str, list] = {}
        for item in items:
            by_date.setdefault(item[0], []).append(item)
        dates_sorted = sorted(by_date.keys())
        is_multi_date = len(dates_sorted) > 1
        for date_idx, date in enumerate(dates_sorted):
            grp = by_date[date]
            for sub_idx, item in enumerate(grp):
                date, form, acc, primary, year_, period_, ext_ = item
                tags = [tag]
                if is_multi_date and date_idx > 0:
                    fm = int(date.split("-")[1])
                    tags.append(_MONTHS[fm - 1])
                if len(grp) > 1 and sub_idx > 0:
                    tags.append(f"a{acc[-6:]}")
                if ext_ in ("xml", "json", "xsd"):
                    continue
                dest = out_dir / fname(
                    investor_name,
                    year_,
                    semi=1 if period_ == "S1" else (2 if period_ == "S2" else None),
                    tags=tags,
                    ext=ext_,
                )
                url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik_padded)}/{acc}/{primary}"
                )
                counts[download(url, dest, headers=EDGAR_HEADERS)] += 1
    return counts


# ---------------------------------------------------------------------------
# Einhorn (Greenlight) — 직접 letter 출처 빈약
# ---------------------------------------------------------------------------
# Greenlight Capital Re (GLRE 상장사) 8-K 첨부에 가끔 letter 가 포함됨.
# CIK 0001385613 = Greenlight Capital Re Ltd
# 또한 valuewalk / hedgefundalpha 는 Cloudflare 차단 → Playwright 필요
GLRE_CIK = "0001385613"


def scrape_einhorn(out_dir: Path) -> dict[str, int]:
    """Greenlight letter is third-party only. Try GLRE 8-K EX-99.1."""
    print("  NOTE   Einhorn (Greenlight) - direct letters not public")
    print("         3rd-party (hedgefundalpha) blocked by Cloudflare")
    print("         GLRE 8-K EX-99.1 best-effort (LP letter sometimes attached)")

    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    cik_padded = GLRE_CIK
    sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        r = requests.get(sub_url, headers=EDGAR_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERR    GLRE submissions: {e}")
        counts["err"] += 1
        return counts

    data = r.json()
    recent = data["filings"]["recent"]
    rows = list(zip(
        recent["form"],
        recent["filingDate"],
        recent["accessionNumber"],
        recent["primaryDocument"],
    ))

    # 8-K 만 — letter 가 EX-99.1 에 첨부되는 경우가 다수
    eight_k = [r for r in rows if r[0] in ("8-K", "8-K/A")]
    print(f"  found  {len(eight_k)} GLRE 8-K filings")

    # 각 8-K 의 EX-99.1 다운로드 시도
    for form, date, acc, primary in eight_k[:50]:  # 우선 최근 50개
        acc_nodash = acc.replace("-", "")
        # 파일 인덱스 조회
        idx_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{int(cik_padded)}/{acc_nodash}/index.json"
        )
        try:
            ir = requests.get(idx_url, headers=EDGAR_HEADERS, timeout=TIMEOUT)
            ir.raise_for_status()
            items = ir.json().get("directory", {}).get("item", [])
        except (requests.RequestException, ValueError):
            continue
        time.sleep(REQUEST_DELAY_SEC)

        # ex99 또는 letter 라는 파일명 찾기
        for it in items:
            name = it.get("name", "").lower()
            if not (
                "ex99" in name or "exhibit99" in name or "letter" in name
                or "ex_99" in name
            ):
                continue
            if not name.endswith((".htm", ".html", ".pdf", ".txt")):
                continue
            url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik_padded)}/{acc_nodash}/{it['name']}"
            )
            year, period = edgar_period_from_filing(date, form)
            ext = Path(name).suffix.lstrip(".")
            if ext == "html":
                ext = "htm"
            # 이름: Einhorn_{year}_{file_stem}
            stem_safe = Path(name).stem.replace(".", "").replace("-", "")[:20]
            dest = out_dir / fname(
                "Einhorn",
                year,
                semi=1 if period == "S1" else None,
                extra=stem_safe,
                ext=ext,
            )
            counts[download(url, dest, headers=EDGAR_HEADERS)] += 1
    return counts


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    targets = set(argv[1:]) or {
        "buffett", "hawkins", "grantham", "driehaus", "baron", "yacktman", "einhorn"
    }
    summary: dict[str, dict[str, int]] = {}

    if "buffett" in targets:
        out = RAW / "buffett"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Buffett ===")
        summary["buffett"] = scrape_buffett(out)

    if "hawkins" in targets:
        out = RAW / "hawkins"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Hawkins (site) ===")
        summary["hawkins"] = scrape_hawkins(out)
        print("\n=== Hawkins (EDGAR) ===")
        summary["hawkins-edgar"] = scrape_hawkins_edgar(out)

    if "grantham" in targets:
        out = RAW / "grantham"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Grantham (GMO) ===")
        summary["grantham"] = scrape_grantham(out)

    if "driehaus" in targets:
        out = RAW / "driehaus"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Driehaus (EDGAR) ===")
        summary["driehaus"] = scrape_driehaus(out)

    if "baron" in targets:
        out = RAW / "baron"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Baron (EDGAR) ===")
        summary["baron"] = scrape_baron(out)

    if "yacktman" in targets:
        out = RAW / "yacktman"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Yacktman (EDGAR) ===")
        summary["yacktman"] = scrape_yacktman(out)

    if "einhorn" in targets:
        out = RAW / "einhorn"
        out.mkdir(parents=True, exist_ok=True)
        print("\n=== Einhorn (GLRE 8-K best-effort) ===")
        summary["einhorn"] = scrape_einhorn(out)

    print("\n=== Summary ===")
    for inv, counts in summary.items():
        print(f"  {inv:18} ok={counts['ok']:>4}  skip={counts['skip']:>4}  "
              f"404={counts['404']:>4}  err={counts['err']:>4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
