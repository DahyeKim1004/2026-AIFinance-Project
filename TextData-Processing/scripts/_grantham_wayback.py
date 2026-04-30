"""GMO Wayback Machine fallback — Grantham 2007-2017 letter 갭 보강.

`_grantham_brute.py` 가 시도한 정형 slug 패턴은 2010-2016 시기 GMO URL 구조를
못 맞춤 (당시 GMO 는 `/websitecontent/JGLetter_ALL_*.pdf` 또는
`/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=N` 사용).

Wayback CDX 로 발굴한 archived URL 을 raw proxy 로 다운로드.

URL 출처 3종
--------------
1. /websitecontent/* (2008-2015): GMO 옛 URL — 분기 letter 거의 전체
2. /docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=N (2015-2017):
   같은 URL 에 분기마다 letter 덮어쓰면서 sfvrsn 캐시버스터 증가.
   각 sfvrsn → 그 시점 letter. 분기 매핑은 PDF 첫 페이지 텍스트로 사후 결정 →
   일단 sfvrsn 번호 그대로 임시 명명. 사용자 검수 후 rename.
3. /globalassets/articles/quarterly-letter/{year}/{slug}.pdf:
   Grantham 시그니처 essay 4개 (2007 everywhere / 2012 sisters-pension /
   2013 race-of-our-lives / 2014 purgatory-or-hell)

Idempotent: 이미 존재하는 dest 는 skip.

Wayback raw bytes proxy: https://web.archive.org/web/{ts}id_/{original}
(`id_` suffix → archive header 없이 원본 그대로)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from _naming import fname  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "grantham"

HEADERS = {
    "User-Agent": "InvestorDNA Research yangwhyun99@gmail.com",
    "Accept": "*/*",
}
DELAY = 1.0  # Wayback CDX rate-limit ~ 15 req/s; 보수적 1초 간격
INTRA_DELAY = 0.5  # CDX 조회와 raw 다운로드 사이
TIMEOUT = 60
MAX_RETRY = 3
RETRY_BACKOFF = 5  # 초


# ── 발굴된 URL → dest 명 매핑 (분기/시그니처 명확) ───────────────────────
TARGETS: list[tuple[str, str]] = [
    # 2007 시그니처
    ("https://www.gmo.com/globalassets/articles/quarterly-letter/2007/jg_its-everywhere-in-everything_4-07.pdf",
     fname("Grantham", 2007, extra="everywhere", ext="pdf")),
    # 2008 분기
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_2Q08.pdf",
     fname("Grantham", 2008, quarter=2, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_3Q08.pdf",
     fname("Grantham", 2008, quarter=3, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_4Q08.pdf",
     fname("Grantham", 2008, quarter=4, ext="pdf")),
    # 2009 분기 + Reinvesting When Terrified (2009-03 시그니처)
    ("http://www.gmo.com/websitecontent/JGLetter_1Q09.pdf",
     fname("Grantham", 2009, quarter=1, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JG_ReinvestingWhenTerrified.pdf",
     fname("Grantham", 2009, quarter=1, tags=["terrified"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_2Q09.pdf",
     fname("Grantham", 2009, quarter=2, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_3Q09.pdf",
     fname("Grantham", 2009, quarter=3, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_4Q09.pdf",
     fname("Grantham", 2009, quarter=4, ext="pdf")),
    # 2010 — Q1/Q3/Q4 (Q2 는 기존 보유)
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_1Q10.pdf",
     fname("Grantham", 2010, quarter=1, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_NightofLivingFed_3Q10.pdf",
     fname("Grantham", 2010, quarter=3, tags=["nightoflivingfed"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_PavlovsBulls_4Q10.pdf",
     fname("Grantham", 2010, quarter=4, tags=["pavlovsbulls"], ext="pdf")),
    # 2011 — 분기 + part2/시그니처
    ("http://www.gmo.com/websitecontent/JGLetterALL_1Q11.pdf",
     fname("Grantham", 2011, quarter=1, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetterPart2_1Q11.pdf",
     fname("Grantham", 2011, quarter=1, tags=["part2"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_Pt2_DangerChildrenatPlay_2Q11.pdf",
     fname("Grantham", 2011, quarter=2, tags=["danger"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ResourceLimitations2_2Q11.pdf",
     fname("Grantham", 2011, quarter=2, tags=["resources"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_ShortestLetterEver_3Q11.pdf",
     fname("Grantham", 2011, quarter=3, tags=["shortest"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/JGLetter_LongestLetterEver_4Q11.pdf",
     fname("Grantham", 2011, quarter=4, tags=["longest"], ext="pdf")),
    # 2012 — Q1(4-12=April letter), Q2, Q3(11-12=Nov letter), 시그니처
    ("http://www.gmo.com/websitecontent/JGLetter_ALL_4-12.pdf",
     fname("Grantham", 2012, quarter=1, ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMOQ2Letter.pdf",
     fname("Grantham", 2012, quarter=2, ext="pdf")),
    ("http://www.gmo.com/websitecontent/JG_LetterALL_11-12.pdf",
     fname("Grantham", 2012, quarter=3, ext="pdf")),
    ("https://www.gmo.com/globalassets/articles/quarterly-letter/2012/my-sisters-pension_jeremy-grantham_apr2012.pdf",
     fname("Grantham", 2012, extra="sisterspension", ext="pdf")),
    # 2013 — Q1-Q4 + 시그니처
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_1Q2013.pdf",
     fname("Grantham", 2013, quarter=1, ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_ALL_2Q2013.pdf",
     fname("Grantham", 2013, quarter=2, ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_ALL_3Q2013.pdf",
     fname("Grantham", 2013, quarter=3, ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_ALL_4Q2013.pdf",
     fname("Grantham", 2013, quarter=4, ext="pdf")),
    ("https://www.gmo.com/globalassets/articles/quarterly-letter/2013/the-race-of-our-lives_jeremy-grantham_2013.pdf",
     fname("Grantham", 2013, extra="raceofourlives", ext="pdf")),
    # 2014 — Q1-Q4 + 시그니처
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_1Q14_FullVersion.pdf",
     fname("Grantham", 2014, quarter=1, ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_2Q14.pdf",
     fname("Grantham", 2014, quarter=2, ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMO_QtlyLetter_3Q14_full.pdf",
     fname("Grantham", 2014, quarter=3, ext="pdf")),
    ("https://www.gmo.com/globalassets/articles/quarterly-letter/2014/bi_isthispurgatoryorhell_qtlyletter_3q2014.pdf",
     fname("Grantham", 2014, quarter=3, tags=["purgatoryorhell"], ext="pdf")),
    ("http://www.gmo.com/websitecontent/GMO_Quarterly_Letter_4Q14.pdf",
     fname("Grantham", 2014, quarter=4, ext="pdf")),
    # 2015 Q1
    ("http://www.gmo.com/websitecontent/Quarterly_Letter_complete_1Q15.pdf",
     fname("Grantham", 2015, quarter=1, ext="pdf")),
]


# ── sfvrsn 시리즈 — 분기 매핑 ambiguous, 임시 sfvrsn 태그로 저장 ──────────
# 9개 unique digest 가 2015 Q2 ~ 2017 H1 letter 들에 대응. 다운로드 후 PDF
# 첫 페이지 헤더("GMO QUARTERLY LETTER • {n}Q YYYY") 를 읽어 사용자가 검수
# → `Grantham_{YY}_Q{n}.pdf` 로 rename 해야 함 (별도 단계).
SFVRSN_TARGETS: list[tuple[str, str]] = [
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=7",
     "Grantham_sfvrsn07.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=8",
     "Grantham_sfvrsn08.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=14",
     "Grantham_sfvrsn14.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=18",
     "Grantham_sfvrsn18.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=20",
     "Grantham_sfvrsn20.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=28",
     "Grantham_sfvrsn28.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=32",
     "Grantham_sfvrsn32.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=38",
     "Grantham_sfvrsn38.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=42",
     "Grantham_sfvrsn42.pdf"),
    ("https://www.gmo.com/docs/default-source/public-commentary/gmo-quarterly-letter.pdf?sfvrsn=46",
     "Grantham_sfvrsn46.pdf"),
]


def cdx_candidates(url: str, n: int = 10) -> list[str]:
    """statuscode=200 + mimetype=application/pdf 후보 timestamp 목록.

    한 timestamp 가 archived error page 인 경우 다른 timestamp 시도하기 위함.
    """
    for attempt in range(MAX_RETRY):
        try:
            r = requests.get(
                "https://web.archive.org/cdx/search/cdx",
                params={
                    "url": url,
                    "output": "json",
                    "limit": n,
                    "filter": ["statuscode:200", "mimetype:application/pdf"],
                },
                headers=HEADERS,
                timeout=30,
            )
        except requests.RequestException:
            time.sleep(RETRY_BACKOFF * (attempt + 1))
            continue
        if r.status_code == 200:
            try:
                rows = r.json()
            except ValueError:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            return [row[1] for row in rows[1:]]
        time.sleep(RETRY_BACKOFF * (attempt + 1))
    return []


def wayback_pdf(url: str) -> bytes | None:
    """Wayback raw bytes proxy 로 PDF 다운로드.

    여러 archived timestamp 후보를 순서대로 시도. 각 timestamp 마다 재시도 적용.
    """
    candidates = cdx_candidates(url, n=10)
    if not candidates:
        return None
    for ts in candidates:
        time.sleep(INTRA_DELAY)
        raw_url = f"https://web.archive.org/web/{ts}id_/{url}"
        for attempt in range(MAX_RETRY):
            try:
                r = requests.get(
                    raw_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True
                )
            except requests.RequestException:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            if r.status_code == 200 and r.content.startswith(b"%PDF"):
                return r.content
            if r.status_code in (200, 404):
                # 200 인데 PDF magic 아님 → archived error page. 다음 timestamp 로
                break
            time.sleep(RETRY_BACKOFF * (attempt + 1))
    return None


def run_targets(targets: list[tuple[str, str]], label: str) -> dict[str, int]:
    counts = {"ok": 0, "skip": 0, "fail": 0}
    print(f"\n=== {label} ({len(targets)} URLs) ===")
    for url, dest_name in targets:
        dest = OUT_DIR / dest_name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  skip  {dest.name}")
            counts["skip"] += 1
            continue
        body = wayback_pdf(url)
        if not body:
            print(f"  FAIL  {url}")
            counts["fail"] += 1
            time.sleep(DELAY)
            continue
        dest.write_bytes(body)
        print(f"  ok    {len(body) // 1024:>5} KB  {dest.name}")
        counts["ok"] += 1
        time.sleep(DELAY)
    return counts


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    a = run_targets(TARGETS, "named (분기/시그니처)")
    b = run_targets(SFVRSN_TARGETS, "sfvrsn (분기 매핑 사후 검수)")
    total = {k: a[k] + b[k] for k in a}
    print(f"\nTotal: ok={total['ok']}  skip={total['skip']}  fail={total['fail']}")
    return 0 if total["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
