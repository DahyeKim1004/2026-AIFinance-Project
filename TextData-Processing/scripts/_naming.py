"""Naming convention helpers.

규칙
----
{Investor}_{YY}                     # 연간 (Buffett, EDGAR annual N-CSR)
{Investor}_{YY}_Q{n}                # 분기
{Investor}_{YY}_S{n}                # 반기 (S1=H1, S2=H2)
{Investor}_{YY}_Q{n}_{tag1}_{tag2}  # 분기 + 펀드/세부 태그

연도는 **컨텐츠 연도** (= 보고서가 다루는 fiscal period). 예:
  - Buffett 2008년 annual letter (실제 발간 2009년 초) → Buffett_08
  - Hawkins N-CSR 2023-02 발간, FY2022 보고 → Hawkins_22
  - Hawkins N-CSRS 2023-08 발간, H1 2023 보고 → Hawkins_23_S1
"""
from __future__ import annotations

from typing import Iterable


def yy(year: int) -> str:
    """연도 4자리 → 2자리 문자열. 1995 → '95', 2008 → '08'."""
    return f"{year % 100:02d}"


def fname(
    investor: str,
    year: int,
    *,
    quarter: int | None = None,
    semi: int | None = None,
    tags: Iterable[str] | None = None,
    extra: str | None = None,
    ext: str = "pdf",
) -> str:
    """파일명 생성.

    Examples
    --------
    >>> fname('Buffett', 2008, ext='pdf')
    'Buffett_08.pdf'
    >>> fname('Hawkins', 2022, quarter=4, tags=['partners'])
    'Hawkins_22_Q4_partners.pdf'
    >>> fname('Hawkins', 1995, ext='txt')
    'Hawkins_95.txt'
    >>> fname('Hawkins', 1996, semi=1, ext='txt')
    'Hawkins_96_S1.txt'
    >>> fname('Buffett', 1998, extra='stub', ext='html')
    'Buffett_98_stub.html'
    """
    parts: list[str] = [investor, yy(year)]
    if quarter is not None:
        if not 1 <= quarter <= 4:
            raise ValueError(f"quarter must be 1-4, got {quarter}")
        parts.append(f"Q{quarter}")
    elif semi is not None:
        if not 1 <= semi <= 2:
            raise ValueError(f"semi must be 1 or 2, got {semi}")
        parts.append(f"S{semi}")
    if tags:
        for t in tags:
            parts.append(_sanitize_tag(t))
    if extra:
        parts.append(_sanitize_tag(extra))
    base = "_".join(parts)
    return f"{base}.{ext.lstrip('.')}"


def _sanitize_tag(tag: str) -> str:
    """태그 정규화: 소문자, 영숫자 + - 만 허용. 'Small-Cap' → 'smallcap'."""
    out = []
    for ch in tag.lower():
        if ch.isalnum():
            out.append(ch)
    s = "".join(out)
    return s or "x"


def edgar_period_from_filing(
    filing_date_str: str, form: str
) -> tuple[int, str | None]:
    """SEC 필링 날짜 + 양식으로부터 보고기간 산출.

    반환: (year, period_kind) 여기서 period_kind는 None | 'S1' | 'S2'.

    규칙
    ----
    * Annual (N-CSR, N-30D in Feb-May): 직전 FY 보고. → (year-1, None)
    * Semi-annual (N-CSRS, N-30D in Jul-Oct): H1 of filing year. → (year, 'S1')
    * 그 외: filing year를 그대로, period는 None.
    """
    yyyy_str, mm_str, _ = filing_date_str.split("-", 2)
    fy, fm = int(yyyy_str), int(mm_str)

    is_annual_form = form.startswith("N-CSR") and not form.startswith("N-CSRS")
    is_semi_form = form.startswith("N-CSRS")

    # N-30D 는 fiscal-period-agnostic — 월로 추정
    if form.startswith("N-30D"):
        if 1 <= fm <= 5:
            return (fy - 1, None)  # annual
        elif 6 <= fm <= 10:
            return (fy, "S1")  # semi-annual
        else:
            return (fy, None)

    if is_annual_form:
        # N-CSR (Feb 발간)는 직전 FY
        if 1 <= fm <= 6:
            return (fy - 1, None)
        else:
            return (fy, None)
    if is_semi_form:
        return (fy, "S1")

    return (fy, None)


def quarter_from_slug(slug: str) -> tuple[int, int] | None:
    """'1q07', '1q-2007', '1Q22' 등 → (year, quarter). 실패 시 None.

    Examples
    --------
    >>> quarter_from_slug('1q07-quarterly-fund-report')
    (2007, 1)
    >>> quarter_from_slug('1q-2023-gmo-quarterly-letter')
    (2023, 1)
    >>> quarter_from_slug('3Q22')
    (2022, 3)
    """
    import re

    # 패턴 1: {q}q{yy} or {q}q{yyyy}  e.g. '1q07', '1q2007', '3Q22'
    m = re.search(r"(\d)q[-_]?(\d{2,4})", slug, re.IGNORECASE)
    if m:
        q = int(m.group(1))
        yr = int(m.group(2))
        if 1 <= q <= 4:
            if yr < 100:
                yr = 1900 + yr if yr >= 70 else 2000 + yr
            return (yr, q)
    return None
