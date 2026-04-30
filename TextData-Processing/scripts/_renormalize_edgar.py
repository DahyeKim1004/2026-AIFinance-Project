"""EDGAR-sourced raw 파일 명명규칙 재정규화.

사용자 결정 (2026-04-30):
  - Baron 의 collision 파일들 (`_mar`, `_jun`, `_may`, `_a000074`, `_mara000074` 등)
    은 같은 Trust 내 다른 펀드의 N-CSR (다른 fiscal year-end). Grantham 의
    essay 제목 라벨과 달리 의미 없는 collision marker.
  - 따라서 **filing month 로 bucket 결정 + sequence 번호로 통일**:
    * filing month 1~6 → `_S1` bucket
    * filing month 7~12 → annual bucket (no period suffix)
    * 같은 bucket 에 2+ 파일 → 모두 `_01`, `_02`, ... sequence
    * 1 파일 → canonical name (no sequence)

대상 폴더:
  - data/raw/baron/
  - data/raw/driehaus/
  - data/raw/yacktman/  (`_amg` 태그는 보존)
  - data/raw/hawkins/   (.htm/.txt EDGAR 파일만; 사이트 PDF `_Q*_partners` 등은 제외)

idempotent: 이미 새 규칙이면 skip.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]

# 파일명 파싱 정규식
# {Investor}_{YY}[_period][_extra1][_extra2]...{ext}
# period: S1 | S2 | Q1-Q4
# extra: month name (jan/feb/.../dec) | a000XXX | <month>a000XXX | smallcap/partners/global/amg | etc.
_FNAME_RE = re.compile(
    r"^(?P<investor>[A-Za-z]+)_(?P<yy>\d{2})"
    r"(?:_(?P<period>S[12]|Q[1-4]))?"
    r"(?P<rest>(?:_[A-Za-z0-9]+)*)"
    r"\.(?P<ext>htm|html|txt|pdf|md)$"
)


def _parse(filename: str) -> dict | None:
    m = _FNAME_RE.match(filename)
    if not m:
        return None
    investor = m.group("investor")
    yy = int(m.group("yy"))
    period = m.group("period")
    rest = m.group("rest").lstrip("_")
    ext = m.group("ext")
    extras = rest.split("_") if rest else []
    return {
        "investor": investor,
        "yy": yy,
        "period": period,
        "extras": extras,
        "ext": ext,
    }


def _extract_filing_month(extras: list[str]) -> int | None:
    """extras 에서 filing month 추출. e.g. ['mar'], ['mara000074'], ['may', 'a000094']."""
    for token in extras:
        low = token.lower()
        # 정확히 month name?
        if low in MONTHS:
            return MONTHS.index(low) + 1
        # month name + accession suffix? e.g. "mara000074", "maya000094"
        for i, mname in enumerate(MONTHS):
            if low.startswith(mname) and len(low) > 3 and any(c.isdigit() for c in low):
                return i + 1
    return None


def _has_meaningful_tag(extras: list[str]) -> str | None:
    """extras 에서 의미 있는 태그 (entity source / file kind) 추출.

    원칙 (사용자 결정 2026-04-30):
      - **펀드 종류** 태그 (partners, smallcap, global 등) 는 collision marker 로
        취급 → consolidate 후 sequence 번호 부여 (Baron/Driehaus/Yacktman 과 일관성)
      - **Entity source** 태그 (amg) 는 보존 — 시기/소스 구분 의미
      - **File kind** 태그 (stub) 는 보존 — 다른 파일 형식
      - **Essay 라벨** (Grantham purgatory, stalin, bargain 등 본인 명명 letter) 은 보존
    """
    # 보존할 태그 (파일 형식 / 의미 있는 라벨만)
    preserve = {
        "stub",      # Buffett: HTML stub vs PDF body
        "annual",    # 명시적 annual 표시
    }
    # consolidate 할 collision 태그 (펀드/엔티티/운용사 변경은 모두 collision 으로 처리)
    fund_tags_to_drop = {
        # 펀드 종류
        "partners", "smallcap", "global", "international",
        "growth", "opportunity", "focused",
        # 운용사/entity 변경 (Yacktman: AMG 인수 전후) — 포트폴리오 본질은 같음
        "amg",
    }
    for token in extras:
        low = token.lower()
        if low in preserve:
            return low
        if low in fund_tags_to_drop:
            continue  # collision 으로 처리 → sequence 부여
        # month/accession suffix 는 collision marker
        if low in MONTHS:
            continue
        if re.match(r"^a\d+$", low):
            continue
        if any(low.startswith(m) and any(c.isdigit() for c in low) for m in MONTHS):
            continue
        # 그 외 영문자 token 은 essay 라벨로 간주 (e.g. purgatory, stalin, bargain)
        if re.match(r"^[a-z]+$", low) and len(low) >= 4:
            return low
    return None


def renormalize_folder(
    folder: Path,
    extension_filter: tuple[str, ...] = ("htm", "txt"),
    dry_run: bool = False,
) -> dict[str, int]:
    """폴더 내 EDGAR 파일들을 새 규칙으로 rename.

    extension_filter: 어느 확장자만 처리할지. EDGAR 는 보통 htm/txt.
    pdf 는 사이트 다운로드 (Hawkins 사이트, Grantham 등) 라 건드리지 않음.
    """
    counts = {"renamed": 0, "kept": 0, "skipped": 0, "warn": 0}
    if not folder.exists():
        return counts

    # Pass 1: 파일 파싱
    items: list[dict] = []
    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.name == ".gitkeep":
            continue
        if f.suffix.lstrip(".").lower() not in extension_filter:
            counts["skipped"] += 1
            continue
        info = _parse(f.name)
        if not info:
            print(f"  WARN  unparseable: {f.name}")
            counts["warn"] += 1
            continue
        info["path"] = f
        items.append(info)

    # Pass 2: 각 파일의 target bucket 결정
    # bucket key = (yy, target_period, meaningful_tag, ext)
    buckets: dict[tuple[int, str | None, str | None, str], list[dict]] = {}
    for info in items:
        filing_month = _extract_filing_month(info["extras"])
        meaningful_tag = _has_meaningful_tag(info["extras"])
        # 이미 의미 있는 period (Q1-Q4 사이트 letter) 는 그대로 보존
        if info["period"] and info["period"].startswith("Q"):
            target_period = info["period"]
        elif filing_month is not None:
            # filing month 기반 재분류
            target_period = "S1" if filing_month <= 6 else None
        else:
            # filing month 정보 없음 → 기존 period 유지
            target_period = info["period"]
        key = (info["yy"], target_period, meaningful_tag, info["ext"])
        buckets.setdefault(key, []).append(info)

    # Pass 3: 각 bucket 내 sequence 부여
    for key, group in buckets.items():
        yy, target_period, meaningful_tag, ext = key
        # 그룹 내 정렬: filing month 알면 그것으로, 없으면 원본 파일명
        def sort_key(it):
            fm = _extract_filing_month(it["extras"])
            return (fm if fm else 99, it["path"].name)
        group.sort(key=sort_key)

        n = len(group)
        for idx, info in enumerate(group):
            # 새 파일명 구성
            parts = [info["investor"], f"{yy:02d}"]
            if target_period:
                parts.append(target_period)
            if meaningful_tag:
                parts.append(meaningful_tag)
            if n > 1:
                parts.append(f"{idx + 1:02d}")
            new_name = "_".join(parts) + f".{ext}"
            new_path = info["path"].parent / new_name

            if info["path"].name == new_name:
                counts["kept"] += 1
                continue

            if new_path.exists() and new_path != info["path"]:
                # 충돌 - 기존 파일 보존, 현재 건 skip (idempotent)
                print(f"  CLASH {info['path'].name} -> {new_name} (target exists)")
                counts["warn"] += 1
                continue

            if dry_run:
                print(f"  DRY   {info['path'].name} -> {new_name}")
            else:
                info["path"].rename(new_path)
                print(f"  mv    {info['path'].name} -> {new_name}")
            counts["renamed"] += 1
    return counts


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv

    targets = [
        ("baron", ("htm", "txt"), "Baron"),
        ("driehaus", ("htm", "txt"), "Driehaus"),
        ("yacktman", ("htm", "txt"), "Yacktman"),
        ("hawkins", ("htm", "txt"), "Hawkins (EDGAR only - .htm/.txt)"),
    ]

    overall = {"renamed": 0, "kept": 0, "skipped": 0, "warn": 0}
    for folder_name, ext_filter, label in targets:
        folder = RAW / folder_name
        print(f"\n=== {label} ===")
        c = renormalize_folder(folder, extension_filter=ext_filter, dry_run=dry)
        for k in overall:
            overall[k] += c[k]
        print(
            f"  renamed={c['renamed']}  kept={c['kept']}  "
            f"skipped={c['skipped']}  warn={c['warn']}"
        )

    print(f"\n=== Total ===")
    print(
        f"renamed={overall['renamed']}  kept={overall['kept']}  "
        f"skipped={overall['skipped']}  warn={overall['warn']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
