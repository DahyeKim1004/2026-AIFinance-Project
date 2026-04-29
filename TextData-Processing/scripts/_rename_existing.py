"""기존 raw/ 파일을 새 명명규칙으로 마이그레이션.

대상:
  - data/raw/buffett/{YYYY}.html → Buffett_{yy}.html
  - data/raw/buffett/{YYYY}_stub.html → Buffett_{yy}_stub.html
  - data/raw/buffett/{YYYY}ltr.pdf → Buffett_{yy}.pdf
  - data/raw/hawkins/{q}q{yy}-combined.pdf → Hawkins_{yy}_Q{q}.pdf
  - data/raw/hawkins/{q}q{yy}-{fund}.pdf → Hawkins_{yy}_Q{q}_{fund}.pdf
  - data/raw/hawkins/edgar/*  → data/raw/hawkins/  (flatten + rename)

idempotent: 이미 새 형식이면 skip. 원본 → 새이름 매핑이 모호하면 dry-run 만 하고 멈춤.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _naming import fname, edgar_period_from_filing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def rename_buffett(dry_run: bool = False) -> dict[str, int]:
    """Buffett: {YYYY}.html / {YYYY}_stub.html / {YYYY}ltr.pdf → 새 형식."""
    src = RAW / "buffett"
    counts = {"renamed": 0, "skipped": 0, "missing": 0}
    if not src.exists():
        return counts

    for f in sorted(src.iterdir()):
        if not f.is_file() or f.name == ".gitkeep":
            continue
        # 매칭 패턴
        m = re.match(r"^(\d{4})\.html$", f.name)
        if m:
            year = int(m.group(1))
            new = src / fname("Buffett", year, ext="html")
            _move(f, new, counts, dry_run)
            continue
        m = re.match(r"^(\d{4})_stub\.html$", f.name)
        if m:
            year = int(m.group(1))
            new = src / fname("Buffett", year, extra="stub", ext="html")
            _move(f, new, counts, dry_run)
            continue
        m = re.match(r"^(\d{4})ltr\.pdf$", f.name)
        if m:
            year = int(m.group(1))
            new = src / fname("Buffett", year, ext="pdf")
            _move(f, new, counts, dry_run)
            continue
        # 이미 새 형식?
        if re.match(r"^Buffett_\d{2}", f.name):
            counts["skipped"] += 1
            continue
        print(f"  WARN unrecognized buffett file: {f.name}")
    return counts


_HAWKINS_SITE_RE = re.compile(
    r"^(?P<q>[1-4])q(?P<yy>\d{2})-(?P<tag>combined|partners|small-cap|global)\.pdf$",
    re.IGNORECASE,
)


def rename_hawkins_site(dry_run: bool = False) -> dict[str, int]:
    """Hawkins 사이트 파일: {q}q{yy}-{tag}.pdf → 새 형식."""
    src = RAW / "hawkins"
    counts = {"renamed": 0, "skipped": 0, "missing": 0}
    if not src.exists():
        return counts

    for f in sorted(src.iterdir()):
        if not f.is_file() or f.name in (".gitkeep", "raw-progress.md"):
            continue
        m = _HAWKINS_SITE_RE.match(f.name)
        if not m:
            if re.match(r"^Hawkins_\d{2}", f.name):
                counts["skipped"] += 1
                continue
            # 다른 패턴 (예: 1996-02-06_N-30D.txt) 은 edgar/ 에서 옮긴 것 — 별도 처리
            continue
        q = int(m.group("q"))
        yy_int = int(m.group("yy"))
        year = 2000 + yy_int if yy_int < 70 else 1900 + yy_int
        tag = m.group("tag").lower()
        if tag == "combined":
            tags = None
        elif tag == "small-cap":
            tags = ["smallcap"]
        else:
            tags = [tag]
        new = src / fname("Hawkins", year, quarter=q, tags=tags, ext="pdf")
        _move(f, new, counts, dry_run)
    return counts


_HAWKINS_EDGAR_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<form>N-(?:CSR|CSRS|30D)(?:_A)?)"
    r"(?:_(?P<acc>[a-zA-Z0-9]+))?\.(?P<ext>htm|html|txt)$",
    re.IGNORECASE,
)


def flatten_and_rename_hawkins_edgar(dry_run: bool = False) -> dict[str, int]:
    """edgar/ 하위 → hawkins/ 로 flatten + 새 명명규칙.

    Collision 처리:
      - 같은 filing date 의 다중 파일 (acc suffix 가 다름) → acc 보존
      - 다른 filing date 가 같은 (year, period) 로 매핑 (예: 2007-08 N-CSR + 2008-02 N-CSR
        둘 다 Hawkins_07): 두 번째부터 filing date 의 월을 extra 태그로 추가
    """
    src_dir = RAW / "hawkins" / "edgar"
    dst_dir = RAW / "hawkins"
    counts = {"renamed": 0, "skipped": 0, "missing": 0, "warn": 0}
    if not src_dir.exists():
        return counts

    # Pass 1: 모든 파일의 정보 추출
    parsed: list[tuple[Path, str, str, str | None, str, int, str | None]] = []
    files = sorted(src_dir.iterdir())
    for f in files:
        if not f.is_file():
            continue
        m = _HAWKINS_EDGAR_RE.match(f.name)
        if not m:
            print(f"  WARN unrecognized edgar file: {f.name}")
            counts["warn"] += 1
            continue
        date = m.group("date")
        form = m.group("form").replace("_A", "/A").upper()
        acc = m.group("acc")
        ext = m.group("ext").lower()
        if ext == "html":
            ext = "htm"
        year, period = edgar_period_from_filing(date, form)
        parsed.append((f, date, form, acc, ext, year, period))

    # Pass 2: 같은 (year, period) 로 매핑되는 그룹 식별
    target_groups: dict[tuple[int, str | None, str], list] = {}
    for item in parsed:
        f, date, form, acc, ext, year, period = item
        key = (year, period, ext)
        target_groups.setdefault(key, []).append(item)

    # Pass 3: 각 그룹 내 파일 이름 결정
    for key, items in target_groups.items():
        year, period, ext = key
        # 같은 filing date 에 여러 acc 가 있는 케이스 와 다른 filing date 에 동일 (year, period) 가
        # 매핑되는 케이스를 함께 처리
        # 그룹화: filing date 별 묶기
        by_date: dict[str, list] = {}
        for item in items:
            f, date, form, acc, ext_, year_, period_ = item
            by_date.setdefault(date, []).append(item)
        # 각 filing date 마다 다른 식별자 필요
        dates_sorted = sorted(by_date.keys())
        is_multi_date = len(dates_sorted) > 1
        for date_idx, date in enumerate(dates_sorted):
            grp = by_date[date]
            for sub_idx, item in enumerate(grp):
                f, _date, form, acc, ext_, year_, period_ = item
                extras: list[str] = []
                # 다중 filing date 인 경우: 두 번째부터 filing month 태그
                if is_multi_date and date_idx > 0:
                    fm = int(date.split("-")[1])
                    month_abbr = [
                        "jan", "feb", "mar", "apr", "may", "jun",
                        "jul", "aug", "sep", "oct", "nov", "dec"
                    ][fm - 1]
                    extras.append(month_abbr)
                # 동일 filing date 내 다중 acc 인 경우: 첫 번째는 그대로, 두번째부터 acc suffix
                if len(grp) > 1 and sub_idx > 0 and acc:
                    extras.append(f"a{acc}")
                elif len(grp) > 1 and sub_idx > 0 and not acc:
                    extras.append(f"d{sub_idx + 1}")
                extra = "_".join(extras) if extras else None
                new = dst_dir / fname(
                    "Hawkins",
                    year_,
                    semi=1 if period_ == "S1" else (2 if period_ == "S2" else None),
                    extra=extra,
                    ext=ext_,
                )
                _move(f, new, counts, dry_run)

    # edgar/ 폴더 비우기 (성공 시)
    if not dry_run and src_dir.exists():
        try:
            remaining = list(src_dir.iterdir())
            if not remaining:
                src_dir.rmdir()
                print(f"  removed empty {src_dir.relative_to(ROOT)}")
        except OSError as e:
            print(f"  WARN cannot remove {src_dir}: {e}")
    return counts


def _move(src: Path, dst: Path, counts: dict[str, int], dry_run: bool) -> None:
    if src == dst:
        counts["skipped"] += 1
        return
    if dst.exists():
        # 이미 변환됨
        if not dry_run:
            try:
                src.unlink()  # 중복 제거
                print(f"  dup    removed duplicate {src.name} (kept {dst.name})")
            except OSError:
                pass
        counts["skipped"] += 1
        return
    if not src.exists():
        counts["missing"] += 1
        return
    if dry_run:
        print(f"  DRY    {src.name} -> {dst.name}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        print(f"  mv     {src.name} -> {dst.name}")
    counts["renamed"] += 1


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv

    print("=== Buffett rename ===")
    c = rename_buffett(dry)
    print(f"  renamed={c['renamed']}  skipped={c['skipped']}  missing={c['missing']}")

    print("\n=== Hawkins site rename ===")
    c = rename_hawkins_site(dry)
    print(f"  renamed={c['renamed']}  skipped={c['skipped']}  missing={c['missing']}")

    print("\n=== Hawkins edgar/ flatten + rename ===")
    c = flatten_and_rename_hawkins_edgar(dry)
    print(
        f"  renamed={c['renamed']}  skipped={c['skipped']}  "
        f"warn={c['warn']}  missing={c['missing']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
