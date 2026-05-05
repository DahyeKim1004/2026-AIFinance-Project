"""
Extract FinBERT embeddings from InvestorDNA text files.

The script supports the current Role 1 raw corpus formats:
PDF, TXT/SGML, HTM, and HTML. It preserves the raw/native period parsed from
filenames (`YYYY`, `YYYY-Hn`, `YYYY-Qn`) and writes one CSV per investor.

Usage:
    python finbert_embedding/scripts/embedding_extraction.py \
        --model_type ProsusAI/finbert \
        --input_file TextData-Processing/data/raw \
        --output_file finbert_embedding/results
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".htm", ".html"}


def parse_period(filename: str) -> dict[str, int | str | None]:
    """Parse native document period from Role 1 raw filenames."""
    name_stem = Path(filename).stem
    parts = name_stem.split("_")

    year_match = re.search(r"_(\d{2})(?:_|$)", name_stem)
    if not year_match:
        return {
            "timestamp": "UNKNOWN",
            "year": None,
            "quarter": None,
            "half": None,
            "period_type": "unknown",
        }

    year_short = int(year_match.group(1))
    year_full = 2000 + year_short if year_short < 50 else 1900 + year_short

    q_match = None
    for part in parts:
        q_match = re.fullmatch(r"Q([1-4])", part, re.IGNORECASE)
        if q_match:
            break
    if q_match:
        quarter = int(q_match.group(1))
        return {
            "timestamp": f"{year_full}-Q{quarter}",
            "year": year_full,
            "quarter": quarter,
            "half": None,
            "period_type": "quarter",
        }

    s_match = None
    for part in parts:
        s_match = re.fullmatch(r"S([1-2])", part, re.IGNORECASE)
        if s_match:
            break
    if s_match:
        half = int(s_match.group(1))
        return {
            "timestamp": f"{year_full}-H{half}",
            "year": year_full,
            "quarter": None,
            "half": half,
            "period_type": "half",
        }

    return {
        "timestamp": str(year_full),
        "year": year_full,
        "quarter": None,
        "half": None,
        "period_type": "year",
    }


def parse_date(filename: str) -> str:
    """Backward-compatible wrapper for older notebooks/scripts."""
    return str(parse_period(filename)["timestamp"])


def clean_extracted_text(text: str) -> str:
    """Normalize whitespace and strip leftover SGML/HTML tags."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: Path) -> str:
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as exc:
        print(f"Error reading {pdf_path}: {exc}")
    return clean_extracted_text(text)


def extract_text_from_txt(txt_path: Path) -> str:
    """Extract text from plain TXT or EDGAR SGML TXT files."""
    try:
        raw = txt_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        print(f"Error reading {txt_path}: {exc}")
        return ""

    text_blocks = re.findall(
        r"<TEXT[^>]*>(.*?)</TEXT>", raw, flags=re.IGNORECASE | re.DOTALL
    )
    text = "\n\n".join(text_blocks) if text_blocks else raw
    return clean_extracted_text(text)


def extract_text_from_html(html_path: Path) -> str:
    """Extract visible text from HTML/HTM, including EDGAR iXBRL filings."""
    try:
        raw = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        print(f"Error reading {html_path}: {exc}")
        return ""

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return clean_extracted_text(soup.get_text(separator="\n"))


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    if suffix in {".htm", ".html"}:
        return extract_text_from_html(file_path)
    return ""


def investor_from_file(file_path: Path, input_path: Path) -> str:
    """Infer investor slug from raw folder layout or filename prefix."""
    if file_path.parent != input_path:
        return file_path.parent.name
    return file_path.stem.split("_")[0].lower()


def get_embeddings(text: str, model, tokenizer, device) -> np.ndarray:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    ).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).cpu().numpy()


def embed_document(
    text: str,
    model,
    tokenizer,
    device,
    chunk_size: int = 510,
) -> np.ndarray | None:
    """Chunk a document and average chunk-level FinBERT embeddings."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
    if not chunks:
        return None

    embeddings = []
    for chunk in tqdm(chunks, desc="    [Chunks]", leave=False):
        chunk_text = tokenizer.decode(chunk, skip_special_tokens=True)
        embeddings.append(get_embeddings(chunk_text, model, tokenizer, device))

    if not embeddings:
        return None
    return np.vstack(embeddings).mean(axis=0).flatten()


def collect_input_files(input_path: Path) -> dict[str, list[Path]]:
    files = [
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    investor_files: dict[str, list[Path]] = {}
    for file_path in files:
        investor = investor_from_file(file_path, input_path)
        investor_files.setdefault(investor, []).append(file_path)
    return investor_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract FinBERT embeddings from InvestorDNA text files"
    )
    parser.add_argument(
        "--model_type",
        type=str,
        default="ProsusAI/finbert",
        help="Hugging Face model name",
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="TextData-Processing/data/raw",
        help="Input directory containing raw PDF/TXT/HTM/HTML files",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="finbert_embedding/results",
        help="Output directory for embedding CSVs",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    output_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: input path does not exist: {input_path}")
        return 1

    investor_files = collect_input_files(input_path)
    file_count = sum(len(files) for files in investor_files.values())
    if file_count == 0:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(f"No supported files found in {input_path} ({supported})")
        return 1

    print(f"Found {file_count} files across {len(investor_files)} investors.")

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using device: {device}")
    print(f"Loading model and tokenizer ({args.model_type})...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_type)
    model = AutoModel.from_pretrained(args.model_type).to(device)
    model.eval()

    for investor, files in tqdm(sorted(investor_files.items()), desc="[Investors]"):
        rows = []
        for file_path in tqdm(sorted(files), desc=f"  [Files: {investor}]", leave=False):
            period = parse_period(file_path.name)
            text = extract_text(file_path)
            if not text:
                continue

            embedding = embed_document(text, model, tokenizer, device)
            if embedding is None:
                continue

            row = {
                "investor_id": f"INV_{investor.upper()}",
                "timestamp": period["timestamp"],
                "Date": period["timestamp"],
                "year": period["year"],
                "quarter": period["quarter"],
                "half": period["half"],
                "period_type": period["period_type"],
                "filename": file_path.name,
                "source_ext": file_path.suffix.lower().lstrip("."),
                "word_count": len(text.split()),
            }
            for idx, value in enumerate(embedding):
                row[f"dim_{idx}"] = value
            rows.append(row)

        if rows:
            df = pd.DataFrame(rows)
            output_csv = output_path / f"finbert_embeddings_{investor}.csv"
            df.to_csv(output_csv, index=False)
            print(f"Wrote {len(rows)} rows to {output_csv}")

    print("\nEmbedding extraction completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
