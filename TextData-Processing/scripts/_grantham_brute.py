"""GMO quarterly letter PDF brute-force.

발견된 패턴: https://www.gmo.com/globalassets/articles/quarterly-letter/{YYYY}/{slug}.pdf
slug 후보:
  - gmo-quarterly-letter_{q}q{yy}    (가장 흔한 정형)
  - gmo-quarterly-letter_{q}q-{yyyy}
  - jeremygrantham-summeressays_{q}q{yyyy}
  - {topic}_jeremy-grantham_{yyyy}
  - {topic}_grantham_{q}q{yyyy}

이 스크립트는 흔한 슬러그 패턴을 brute-force 시도한다. 404 는 무시.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from _naming import fname  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "grantham"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0"
HEADERS = {"User-Agent": UA, "Accept": "*/*"}
DELAY = 0.2


def try_url(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    except requests.RequestException:
        return "err"
    if r.status_code == 404:
        return "404"
    if r.status_code != 200:
        return "err"
    body = r.content
    if not body.startswith(b"%PDF"):
        return "err"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    print(f"  OK  {len(body) // 1024:>5} KB  {dest.name}")
    time.sleep(DELAY)
    return "ok"


def main() -> int:
    counts = {"ok": 0, "skip": 0, "404": 0, "err": 0}

    for year in range(2008, 2027):
        yy = year % 100
        for q in (1, 2, 3, 4):
            # 정형 패턴들
            slug_candidates = [
                f"gmo-quarterly-letter_{q}q{yy:02d}",
                f"gmo-quarterly-letter_{q}q-{year}",
                f"gmoquarterlyletter_{q}q{yy:02d}",
                f"jeremygrantham-summeressays_{q}q{year}",
                f"jeremy-grantham-quarterly-letter_{q}q{yy:02d}",
                f"gmo_quarterly_letter_{q}q{yy:02d}",
            ]
            dest = OUT_DIR / fname("Grantham", year, quarter=q, ext="pdf")
            if dest.exists():
                counts["skip"] += 1
                continue
            for slug in slug_candidates:
                url = f"https://www.gmo.com/globalassets/articles/quarterly-letter/{year}/{slug}.pdf"
                result = try_url(url, dest)
                if result == "ok":
                    counts["ok"] += 1
                    break
                elif result == "skip":
                    counts["skip"] += 1
                    break
                elif result == "404":
                    continue
                else:
                    counts["err"] += 1
                    break
            else:
                # 모든 후보 404
                counts["404"] += 1

    print("\nSummary:")
    print(f"  ok={counts['ok']}  skip={counts['skip']}  404={counts['404']}  err={counts['err']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
