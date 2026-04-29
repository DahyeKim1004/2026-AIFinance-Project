"""
Role 1 — Phase 1 파일럿 스크래퍼.

Buffett (berkshirehathaway.com)와 Hawkins (southeasternasset.com) 두 가지
URL 패턴을 검증하기 위한 스크립트. 출력은 data/raw/{investor}/ 에 원본 그대로
저장하며, 후속 단계의 text_cleaner.py 가 여기서부터 작업.

Patterns
--------
Buffett
  - 1977-2003: https://www.berkshirehathaway.com/letters/{YYYY}.html  (HTML)
  - 2004-2024: https://www.berkshirehathaway.com/letters/{YYYY}ltr.pdf (PDF)

Hawkins (Southeastern Asset Management / Longleaf Partners)
  - 2022-: https://southeasternasset.com/commentary/{q}q{yy}-{fund}-fund-commentary/
          → per-fund 분리 PDF (Partners / Small-Cap / Global)
  - ~2008-2021: https://southeasternasset.com/report/{q}q{yy}-quarterly-fund-report/
          → 단일 combined PDF
  두 URL 모두 pretty-URL 이지만 응답은 application/pdf. 존재하지 않는 분기는 404.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA, "Accept": "*/*"}

# SEC EDGAR 정책: 식별 가능한 UA + 이메일 필요 (rate limit 10 req/s)
EDGAR_HEADERS = {
    "User-Agent": "InvestorDNA Research yangwhyun99@gmail.com",
    "Accept": "*/*",
}

REQUEST_DELAY_SEC = 0.3
TIMEOUT = 30


_PDF_HREF_RE = re.compile(r'HREF="([^"]+\.pdf)"', re.IGNORECASE)


def _parse_first_pdf_href(stub_path: Path) -> str | None:
    if not stub_path.exists():
        return None
    text = stub_path.read_text(encoding="utf-8", errors="replace")
    m = _PDF_HREF_RE.search(text)
    return m.group(1) if m else None


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


# ---------------------------------------------------------------------------
# Buffett
# ---------------------------------------------------------------------------
BUFFETT_BASE = "https://www.berkshirehathaway.com/letters"
# 1977-1997: {year}.html 이 본문
# 1998-2003: {year}.html 은 stub, 실제 본문은 {year}pdf.pdf / {year}htm.html
# 2004-2024: {year}ltr.pdf 가 본문
BUFFETT_HTML_ONLY = range(1977, 1998)
BUFFETT_STUB_RANGE = range(1998, 2004)
BUFFETT_PDF_RANGE = range(2004, 2025)


def scrape_buffett(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    for year in BUFFETT_HTML_ONLY:
        url = f"{BUFFETT_BASE}/{year}.html"
        dest = out_dir / f"{year}.html"
        counts[download(url, dest)] += 1
    for year in BUFFETT_STUB_RANGE:
        # stub 페이지(1KB) → 본문 PDF 링크 파싱 후 다운로드.
        # 1999는 final1999pdf.pdf, 2003은 2003ltr.pdf 등 파일명이 비균일.
        stub_url = f"{BUFFETT_BASE}/{year}.html"
        stub_dest = out_dir / f"{year}_stub.html"
        counts[download(stub_url, stub_dest)] += 1
        pdf_href = _parse_first_pdf_href(stub_dest)
        if not pdf_href:
            print(f"  WARN   no pdf link in {stub_dest.name}")
            counts["err"] += 1
            continue
        pdf_url = f"{BUFFETT_BASE}/{pdf_href}"
        pdf_dest = out_dir / f"{year}ltr.pdf"
        counts[download(pdf_url, pdf_dest, expect_pdf=True)] += 1
    for year in BUFFETT_PDF_RANGE:
        url = f"{BUFFETT_BASE}/{year}ltr.pdf"
        dest = out_dir / f"{year}ltr.pdf"
        counts[download(url, dest, expect_pdf=True)] += 1
    return counts


# ---------------------------------------------------------------------------
# Hawkins
# ---------------------------------------------------------------------------
HAWKINS_BASE = "https://southeasternasset.com"
HAWKINS_FUNDS = ("partners", "small-cap", "global")
# Recent commentary cadence (per-fund split): probe 2022 Q1 ~ current year Q4
HAWKINS_NEW_YEARS = range(22, 27)        # 2022 ~ 2026
# Legacy combined report: probe 2007 Q1 ~ 2021 Q4 (실제 존재 분기는 try 후 확정)
HAWKINS_OLD_YEARS = range(7, 22)         # 2007 ~ 2021
QUARTERS = (1, 2, 3, 4)


def scrape_hawkins(out_dir: Path) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}

    # New: /commentary/{q}q{yy}-{fund}-fund-commentary/
    for yy in HAWKINS_NEW_YEARS:
        for q in QUARTERS:
            for fund in HAWKINS_FUNDS:
                slug = f"{q}q{yy:02d}-{fund}-fund-commentary"
                url = f"{HAWKINS_BASE}/commentary/{slug}/"
                dest = out_dir / f"{q}q{yy:02d}-{fund}.pdf"
                counts[download(url, dest, expect_pdf=True)] += 1

    # Legacy: /report/{q}q{yy}-quarterly-fund-report/
    for yy in HAWKINS_OLD_YEARS:
        for q in QUARTERS:
            slug = f"{q}q{yy:02d}-quarterly-fund-report"
            url = f"{HAWKINS_BASE}/report/{slug}/"
            dest = out_dir / f"{q}q{yy:02d}-combined.pdf"
            counts[download(url, dest, expect_pdf=True)] += 1

    return counts


# ---------------------------------------------------------------------------
# Hawkins — SEC EDGAR fallback (gap 2015-2021 + redundancy)
# ---------------------------------------------------------------------------
LONGLEAF_FUNDS_TRUST_CIK = "0000806636"


def scrape_hawkins_edgar(out_dir: Path) -> dict[str, int]:
    """N-30D + N-CSR + N-CSRS 필링 본 HTML 다운로드.

    펀드의 shareholder letter 가 들어있는 SEC 의무 제출본을 모두 수집.
      - 1996-2002: N-30D (annual/semiannual report — pre-Sarbanes-Oxley 양식)
      - 2003-now : N-CSR (annual) + N-CSRS (semiannual)

    각 필링은 0.2~2 MB HTML 한 개에 'To Our Shareholders' 섹션 + 4개 펀드
    합본 letter + 재무제표 등이 embedded. 사이트 listing 에서 사라진 2015-2021
    갭과 1996-2002 deep history 모두 SEC 채널로 커버.
    """
    # 어떤 form prefix 를 letter 후보로 인식할지
    LETTER_FORMS = ("N-CSR", "N-CSRS", "N-CSR/A", "N-CSRS/A", "N-30D", "N-30D/A")
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}
    sub_url = (
        f"https://data.sec.gov/submissions/CIK{LONGLEAF_FUNDS_TRUST_CIK}.json"
    )
    try:
        r = requests.get(sub_url, headers=EDGAR_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERR    submissions fetch: {e}")
        counts["err"] += 1
        return counts

    recent = r.json()["filings"]["recent"]
    rows = list(zip(
        recent["form"],
        recent["filingDate"],
        recent["accessionNumber"],
        recent["primaryDocument"],
    ))

    # 동일 (date, form) 다중 필링은 accession suffix 로 분리
    seen: dict[tuple[str, str], int] = {}
    for form, date, acc, primary in rows:
        if form not in LETTER_FORMS:
            continue
        acc_nodash = acc.replace("-", "")
        # primary 필드가 비어있는 옛 필링 → 인덱스에서 최대 크기 문서 추정
        if not primary:
            primary = _resolve_primary_doc(acc_nodash)
            if not primary:
                print(f"  WARN   no primary doc for {date} {form} {acc}")
                counts["err"] += 1
                continue
        url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{int(LONGLEAF_FUNDS_TRUST_CIK)}/{acc_nodash}/{primary}"
        )
        safe_form = form.replace("/", "_")
        ext = Path(primary).suffix or ".htm"
        key = (date, safe_form)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 1:
            dest = out_dir / f"{date}_{safe_form}{ext}"
        else:
            dest = out_dir / f"{date}_{safe_form}_{acc_nodash[-6:]}{ext}"
        counts[download(url, dest, headers=EDGAR_HEADERS)] += 1
    return counts


def _resolve_primary_doc(acc_nodash: str) -> str | None:
    """필링 폴더 인덱스에서 본 문서 추정. Cert/exhibit 제외 후 최대 크기."""
    idx_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{int(LONGLEAF_FUNDS_TRUST_CIK)}/{acc_nodash}/index.json"
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
# Entry
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    targets = set(argv[1:]) or {"buffett", "hawkins"}
    summary: dict[str, dict[str, int]] = {}

    if "buffett" in targets:
        out = RAW / "buffett"
        out.mkdir(parents=True, exist_ok=True)
        print("=== Buffett ===")
        summary["buffett"] = scrape_buffett(out)

    if "hawkins" in targets:
        out = RAW / "hawkins"
        out.mkdir(parents=True, exist_ok=True)
        print("=== Hawkins (Southeastern site) ===")
        summary["hawkins"] = scrape_hawkins(out)

    if "hawkins-edgar" in targets or "hawkins" in targets:
        out = RAW / "hawkins" / "edgar"
        out.mkdir(parents=True, exist_ok=True)
        print("=== Hawkins (SEC EDGAR N-CSR/N-CSRS) ===")
        summary["hawkins-edgar"] = scrape_hawkins_edgar(out)

    print("\n=== Summary ===")
    for inv, counts in summary.items():
        print(f"  {inv:10} ok={counts['ok']}  skip={counts['skip']}  "
              f"404={counts['404']}  err={counts['err']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
