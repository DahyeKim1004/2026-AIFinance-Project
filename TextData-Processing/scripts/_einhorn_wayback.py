"""Einhorn Wayback Machine fallback — Greenlight Capital LP letter 수집.

PLAN.md §2 의 Einhorn 텍스트 1차 출처(`hedgefundalpha.com`)는 Cloudflare 차단.
대안으로 `greenlightcapital.com` 자체 도메인 archived PDF 활용.

발견 (Wayback CDX):
- `greenlightcapital.com/{6digit}.pdf` (numbered ID, 2013-2018): 12개 unique
- `greenlightcapital.com/Download.aspx?ID={uuid}&Inline=1` (UUID, 2021-2024): 7개 unique URL × 다중 archive timestamp = 13 snapshots
- `greenlightcapital.com/IraSohn2014-final.pdf`: 1개 시그니처 발표

전략
----
1. 각 (URL, timestamp) 쌍을 Wayback `id_/` raw proxy 로 다운로드 — 같은 URL이라도
   timestamp 별로 다른 letter 가 호스팅됐을 수 있음 (Greenlight 가 같은 endpoint
   재사용). 다운로드 후 SHA-1 dedup.
2. 첫 페이지 텍스트 추출 (pypdf) → 분기/연도 식별 → 명명규칙 적용.
   - Letter 헤더 패턴: "Q{N} 20XX", "Quarter Ended", "December 31, 20XX" 등
3. 분류:
   - 분기 letter → `Einhorn_{YY}_Q{n}.pdf`
   - 시그니처 발표 (Sohn/Robin Hood 등) → `Einhorn_{YY}_{tag}.pdf`
   - 미식별 → `Einhorn_unidentified_{hash}.pdf` (수동 검수)
4. 중복 (SHA-1 동일 + 이미 같은 분기 보유) → 삭제.

Idempotent: 이미 다운로드된 sourcefile (raw URL+ts) 은 skip.
"""
from __future__ import annotations

import hashlib
import re
import sys
import time
from pathlib import Path

import pypdf
import requests

sys.path.insert(0, str(Path(__file__).parent))
from _naming import fname  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "einhorn"
STAGING = OUT_DIR / "_wayback_staging"  # 임시 다운로드 (분기 식별 전)

HEADERS = {
    "User-Agent": "InvestorDNA Research yangwhyun99@gmail.com",
    "Accept": "*/*",
}
DELAY = 0.8
INTRA_DELAY = 0.4
TIMEOUT = 90
MAX_RETRY = 3
RETRY_BACKOFF = 5


# ── (timestamp, URL) 쌍 — Wayback CDX 발굴 결과 hardcoded ──────────────────
# 같은 URL이 timestamp 별로 다른 letter 인 경우 (UUID 재사용) 모두 받음.
TARGETS: list[tuple[str, str]] = [
    # numbered ID (2013-2018) — letter 추정
    ("20160413072934", "https://greenlightcapital.com/893640.pdf"),
    ("20130208104321", "https://www.greenlightcapital.com/904950.pdf"),
    ("20130603014601", "https://www.greenlightcapital.com/905284.pdf"),
    ("20150316020457", "https://www.greenlightcapital.com/922676.pdf"),
    ("20150316024201", "https://www.greenlightcapital.com/922828.pdf"),
    ("20150922112811", "https://www.greenlightcapital.com/926211.pdf"),
    ("20150919213708", "https://www.greenlightcapital.com/926698.pdf"),
    ("20160204064220", "https://www.greenlightcapital.com/929842.pdf"),
    ("20170806203937", "https://www.greenlightcapital.com/933586.pdf"),
    ("20170330001042", "https://www.greenlightcapital.com/934618.pdf"),
    ("20170614040336", "https://www.greenlightcapital.com/935084.pdf"),
    ("20180821104521", "https://www.greenlightcapital.com/938256.pdf"),
    # 2014 Sohn presentation
    ("20140701225726", "https://www.greenlightcapital.com/IraSohn2014-final.pdf"),
    # UUID Download.aspx (2021-2024) — 같은 UUID 가 다른 시점에 다른 letter 일 수 있음
    ("20210512082954", "https://www.greenlightcapital.com/Download.aspx?ID=004ad5a3-531e-48e7-bc7b-7c0795df2f9e&Inline=1"),
    ("20210512080434", "https://www.greenlightcapital.com/Download.aspx?ID=064278d5-3b5d-4fdf-90ef-f0b3810d3134&Inline=1"),
    ("20210616233028", "https://www.greenlightcapital.com/Download.aspx?ID=2a70731a-c6bc-41fa-8530-0541377db6af&Inline=1"),
    ("20210726211447", "https://www.greenlightcapital.com/Download.aspx?ID=2a70731a-c6bc-41fa-8530-0541377db6af&Inline=1"),
    ("20211108033423", "https://www.greenlightcapital.com/Download.aspx?ID=2a70731a-c6bc-41fa-8530-0541377db6af&Inline=1"),
    ("20230417194332", "https://www.greenlightcapital.com/Download.aspx?ID=2a70731a-c6bc-41fa-8530-0541377db6af&Inline=1"),
    ("20230519194255", "https://www.greenlightcapital.com/Download.aspx?ID=2a70731a-c6bc-41fa-8530-0541377db6af&Inline=1"),
    ("20230528034127", "https://www.greenlightcapital.com/Download.aspx?ID=2a70731a-c6bc-41fa-8530-0541377db6af&Inline=1"),
    ("20210512085743", "https://www.greenlightcapital.com/Download.aspx?ID=88718ece-a58e-4ffc-bedb-0d2c26cd1a6a&Inline=1"),
    ("20241108133337", "https://www.greenlightcapital.com/Download.aspx?ID=c9a435af-fdc1-4ee3-a2fd-f869be7f6952&Inline=1"),
    ("20241201210529", "https://www.greenlightcapital.com/Download.aspx?ID=c9a435af-fdc1-4ee3-a2fd-f869be7f6952&Inline=1"),
    ("20210801144354", "https://www.greenlightcapital.com/Download.aspx?ID=cd416660-3d25-40f2-b0d0-9f5eaca3d1b3&Inline=1"),
    ("20210512071521", "https://www.greenlightcapital.com/Download.aspx?ID=e6f362b1-6323-4311-be36-979fe590f2e4&Inline=1"),
]


def wayback_pdf(ts: str, url: str) -> bytes | None:
    """Wayback raw bytes proxy 로 PDF 다운로드 (재시도 포함)."""
    raw_url = f"https://web.archive.org/web/{ts}id_/{url}"
    for attempt in range(MAX_RETRY):
        try:
            r = requests.get(raw_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        except requests.RequestException:
            time.sleep(RETRY_BACKOFF * (attempt + 1))
            continue
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            return r.content
        if r.status_code in (200, 404):
            return None
        time.sleep(RETRY_BACKOFF * (attempt + 1))
    return None


def all_pages_text(path: Path, max_pages: int = 4) -> str:
    """PDF 첫 N 페이지 텍스트 추출. cover-only 발표용."""
    try:
        reader = pypdf.PdfReader(str(path))
        pages = reader.pages[:max_pages]
        return "\n".join(p.extract_text() or "" for p in pages)
    except Exception:
        return ""


def pdf_creation_year(path: Path) -> int | None:
    """PDF metadata /CreationDate 에서 연도 추출. 'D:20240316123045' 형태."""
    try:
        reader = pypdf.PdfReader(str(path))
        d = reader.metadata.get("/CreationDate") if reader.metadata else None
        if not d:
            return None
        m = re.search(r"D?:?(\d{4})", str(d))
        if m:
            yr = int(m.group(1))
            if 2000 <= yr <= 2030:
                return yr
    except Exception:
        pass
    return None


# 분기 식별 패턴들 — 가장 명시적인 것부터
QUARTER_RE = [
    (re.compile(r"\b(First|Second|Third|Fourth)\s+Quarter[\s,]+(20\d{2})", re.IGNORECASE), "QW"),
    (re.compile(r"\bQ([1-4])[\s\-,]+(20\d{2})\b", re.IGNORECASE), "Q"),
    (re.compile(r"\b([1-4])Q[\s\-]?(20\d{2})\b", re.IGNORECASE), "Q"),
    (re.compile(r"\b([1-4])Q(\d{2})\b", re.IGNORECASE), "Q2"),  # "1Q17"
    (re.compile(r"\b(March|June|September|December)\s+\d{1,2},?\s+(20\d{2})", re.IGNORECASE), "QM"),
    (re.compile(r"\bQuarter\s+Ended[\s,]+(March|June|September|December)\s+\d{1,2},?\s+(20\d{2})", re.IGNORECASE), "QM"),
]

QM_MONTH_TO_Q = {"march": 1, "june": 2, "september": 3, "december": 4, "sept": 3, "sep": 3}
QW_TO_Q = {"first": 1, "second": 2, "third": 3, "fourth": 4}


def detect_quarter(text: str) -> tuple[int, int] | None:
    """전체 텍스트에서 (year, quarter) 추출."""
    for regex, kind in QUARTER_RE:
        m = regex.search(text)
        if not m:
            continue
        if kind == "Q":
            q, yr = int(m.group(1)), int(m.group(2))
            if 1 <= q <= 4 and 2000 <= yr <= 2030:
                return (yr, q)
        elif kind == "Q2":
            q = int(m.group(1))
            yy = int(m.group(2))
            yr = 2000 + yy if yy < 50 else 1900 + yy
            if 1 <= q <= 4 and 2000 <= yr <= 2030:
                return (yr, q)
        elif kind == "QW":
            return (int(m.group(2)), QW_TO_Q[m.group(1).lower()])
        elif kind == "QM":
            q = QM_MONTH_TO_Q.get(m.group(1).lower())
            yr = int(m.group(2))
            if q and 2000 <= yr <= 2030:
                return (yr, q)
    return None


def _norm(text: str) -> str:
    """공백·줄바꿈 정규화 + ASCII drop + lowercase. PyPDF 텍스트 변형 회피
    (예: `!` → � replacement char 으로 추출되는 경우)."""
    s = re.sub(r"\s+", " ", text)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.lower()


def detect_signature(text: str) -> str | None:
    """시그니처 발표 검출 (Sohn / Robin Hood / value investing congress 등). 전체 텍스트 검사."""
    s = _norm(text)
    sohn_keys = (
        "ira sohn", "sohn investment conference", "sohn conference",
        "annual sohn", "look forward to sohn", "forward to sohn", "sohn 20",
    )
    if any(k in s for k in sohn_keys):
        return "sohn"
    if ("robin hood" in s and "conference" in s) or "robin hood investors conference" in s:
        return "robinhood"
    if "value investing congress" in s:
        return "vic"
    grants_keys = ("grant's conference", "grants conference",
                   "thank you for inviting me back", "jim, thank you for inviting")
    if any(k in s for k in grants_keys):
        return "grants"
    goups_keys = ("goups presentation", "goups", "go ups presentation",
                  "go ups inc")
    if any(k in s for k in goups_keys):
        return "goups"
    return None


def detect_doctype(text: str) -> str | None:
    """비-letter 카테고리 식별: regulatory disclosure / proxy contest / conf call."""
    s = _norm(text)
    if "fca pillar 3" in s or "pillar 3 disclosure" in s or "capital requirements directive" in s:
        return "pillar3"
    if "urges" in s and "shareholders" in s and "proposal" in s:
        return "applevoting"
    if "unlocking value at gm" in s or "two classes of common shares" in s:
        return "gmproxy"
    return None


def detect_year_anywhere(text: str, hint: int | None = None) -> int | None:
    """시그니처/모호 발표의 연도 추출. 가장 큰 (가장 최근) 4자리 연도 사용 — 발표 본문이
    이전 연도 기록을 언급하므로 max 가 발표 시점에 가까움. hint 가 있으면 ±1 안에서만 채택."""
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    years = [y for y in years if 2000 <= y <= 2030]
    if not years:
        return hint
    candidate = max(years)
    if hint and abs(candidate - hint) > 1:
        return hint
    return candidate


def ts_to_year(ts: str) -> int:
    """Wayback timestamp (YYYYMMDDHHMMSS) → year."""
    return int(ts[:4])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)

    # 1) 다운로드
    print("=== Step 1: Wayback download ===")
    counts = {"download_ok": 0, "download_skip": 0, "download_fail": 0}
    for ts, url in TARGETS:
        # staging 파일명: {ts}_{url의 뒷부분}.pdf
        url_id = re.sub(r"[^A-Za-z0-9]+", "_", url.split("/")[-1])[:40]
        staged = STAGING / f"{ts}_{url_id}.pdf"
        if staged.exists() and staged.stat().st_size > 0:
            counts["download_skip"] += 1
            continue
        body = wayback_pdf(ts, url)
        if not body:
            print(f"  FAIL  {ts}  {url}")
            counts["download_fail"] += 1
            time.sleep(DELAY)
            continue
        staged.write_bytes(body)
        print(f"  ok    {len(body) // 1024:>5} KB  {staged.name}")
        counts["download_ok"] += 1
        time.sleep(DELAY)

    print(f"\n  download: ok={counts['download_ok']}  skip={counts['download_skip']}  fail={counts['download_fail']}")

    # 2) 전체 페이지 텍스트 + 메타데이터 분석 + dedup + rename
    print("\n=== Step 2: Identify + rename ===")
    # 기존 잘못 분류된 Einhorn_*.pdf 모두 삭제 (staging 은 보존, 재실행)
    for old in OUT_DIR.glob("Einhorn_*.pdf"):
        old.unlink()

    seen_sha: dict[str, str] = {}
    classified = {"quarter": 0, "signature": 0, "unknown": 0, "dup": 0}

    for staged in sorted(STAGING.glob("*.pdf")):
        body = staged.read_bytes()
        sha = hashlib.sha1(body).hexdigest()[:12]
        if sha in seen_sha:
            print(f"  dup    {staged.name} ↔ {seen_sha[sha]}")
            classified["dup"] += 1
            continue

        # staged 파일명 prefix = wayback timestamp (e.g. "20210726211447_...")
        ts_year = int(staged.name[:4]) if staged.name[:4].isdigit() else None
        full_text = all_pages_text(staged, max_pages=4)
        meta_year = pdf_creation_year(staged)

        # 우선순위: 1) signature 발표 2) doctype (regulatory/proxy) 3) 분기 letter 4) unknown
        signature = detect_signature(full_text)
        doctype = detect_doctype(full_text)
        quarter = detect_quarter(full_text)

        if signature:
            yr = meta_year or detect_year_anywhere(full_text, hint=ts_year) or ts_year or 2014
            dest_name = fname("Einhorn", yr, extra=signature, ext="pdf")
            classified["signature"] += 1
        elif doctype:
            yr = meta_year or detect_year_anywhere(full_text, hint=ts_year) or ts_year or 2014
            dest_name = fname("Einhorn", yr, extra=doctype, ext="pdf")
            classified["signature"] += 1  # 통계상 signature 카테고리에 합산
        elif quarter:
            yr, q = quarter
            dest_name = fname("Einhorn", yr, quarter=q, ext="pdf")
            classified["quarter"] += 1
        else:
            # quarter/sig 식별 실패 → 사용자 검수용
            dest_name = f"Einhorn_unidentified_{ts_year or '0000'}_{sha}.pdf"
            classified["unknown"] += 1

        # collision: 같은 분기에 letter 2개 이상이면 _01, _02 suffix
        dest = OUT_DIR / dest_name
        if dest.exists() and dest.stat().st_size > 0 and hashlib.sha1(dest.read_bytes()).hexdigest()[:12] != sha:
            stem, ext = dest.stem, dest.suffix
            for n in range(1, 10):
                alt = OUT_DIR / f"{stem}_{n:02d}{ext}"
                if not alt.exists():
                    dest = alt
                    break
        if dest.exists():
            classified["dup"] += 1
            continue

        dest.write_bytes(body)
        seen_sha[sha] = dest.name
        snippet = re.sub(r"\s+", " ", full_text[:120]).encode("ascii", "replace").decode()
        print(f"  {dest.name:50}  <- {staged.name}")
        print(f"    {snippet[:100]}")

    print(f"\n  classified: quarter={classified['quarter']}  signature={classified['signature']}  "
          f"unknown={classified['unknown']}  dup={classified['dup']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
