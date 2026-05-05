"""
Investor의 Text 데이터를 FinBERT 모델을 이용하여 임베딩을 추출하는 스크립트

Usage-User:
    python finbert_embedding/scripts/embedding_extraction.py --model_type ProsusAI/finbert --input_file TextData-Processing/data/raw/{investor_name} --output_file results

    Args:
        --model_type: 모델 타입 (default: 'ProsusAI/finbert')
        --input_file: 입력 디렉토리 경로 (default: 'TextData-Processing/data/raw')
        --output_file: 결과 저장 디렉토리 경로 (default: 'results')
    
    Returns:
        Processed csv file with embedding extracted from each investor's text data
"""

import argparse
from pathlib import Path
import re

from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".htm", ".html"}


def parse_period(filename):
    """
    Parse TextData-Processing raw filename periods.

    Examples
    --------
    Buffett_01.pdf -> 2001
    Grantham_19_Q1.pdf -> 2019-Q1
    Hawkins_22_S1.htm -> 2022-H1
    Baron_06_S1_02.txt -> 2006-H1
    """
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


def parse_date(filename):
    """Backward-compatible wrapper for older notebooks/scripts."""
    return parse_period(filename)["timestamp"]


# extract text from pdf files
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


def extract_text_from_txt(txt_path):
    """Extract readable text from EDGAR TXT/SGML or plain text files."""
    try:
        raw = Path(txt_path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
        return ""

    text_blocks = re.findall(
        r"<TEXT[^>]*>(.*?)</TEXT>", raw, flags=re.IGNORECASE | re.DOTALL
    )
    text = "\n\n".join(text_blocks) if text_blocks else raw
    return clean_extracted_text(text)


def extract_text_from_html(html_path):
    """Extract visible text from HTML/HTM, including EDGAR iXBRL filings."""
    try:
        raw = Path(html_path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Error reading {html_path}: {e}")
        return ""

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return clean_extracted_text(soup.get_text(separator="\n"))


def clean_extracted_text(text):
    """Normalize whitespace and strip common SEC/HTML leftovers."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text(file_path):
    """Dispatch text extraction by raw file type."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return clean_extracted_text(extract_text_from_pdf(file_path))
    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    if suffix in {".htm", ".html"}:
        return extract_text_from_html(file_path)
    return ""


def investor_from_file(file_path, input_path):
    """Infer investor name from raw folder layout or filename prefix."""
    if file_path.parent != input_path:
        return file_path.parent.name
    return file_path.stem.split("_")[0].lower()


# extract embedding from text using FinBERT model
def get_embeddings(text, model, tokenizer, device):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    ).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use mean pooling of the last hidden state
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.cpu().numpy()


def embed_document(text, model, tokenizer, device, chunk_size=510):
    """Chunk a document and average chunk-level FinBERT embeddings."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
    if not chunks:
        return None

    file_embeddings = []
    chunk_pbar = tqdm(chunks, desc="    [Chunks]", leave=False)
    for chunk in chunk_pbar:
        chunk_text = tokenizer.decode(chunk, skip_special_tokens=True)
        emb = get_embeddings(chunk_text, model, tokenizer, device)
        file_embeddings.append(emb)

    if not file_embeddings:
        return None
    return np.vstack(file_embeddings).mean(axis=0).flatten()


def main():
    parser = argparse.ArgumentParser(
        description="Extract FinBERT embeddings from Investor text files"
    )
    parser.add_argument("--model_type", type=str, default="ProsusAI/finbert", help="FinBERT model type")
    parser.add_argument(
        "--input_file",
        type=str,
        default="TextData-Processing/data/raw",
        help="Input directory containing raw PDF/TXT/HTM/HTML files",
    )
    parser.add_argument("--output_file", type=str, default="finbert_embedding/results", help="Output directory for results")
    
    args = parser.parse_args()
    
    # device selection
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check if input directory exists
    if not input_path.exists():
        print(f"Error: Input path '{input_path}' does not exist.")
        return

    print(f"Searching for raw text files in {input_path}...")
    all_text_files = [
        path for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not all_text_files:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(f"No supported files found in {input_path} ({supported})")
        return

    investor_files = {}
    for text_file in all_text_files:
        investor_name = investor_from_file(text_file, input_path)
        if investor_name not in investor_files:
            investor_files[investor_name] = []
        investor_files[investor_name].append(text_file)
        
    print(
        f"Found {len(all_text_files)} files across {len(investor_files)} investors."
    )

    # Load model and tokenizer only after confirming files exist
    print(f"Loading model and tokenizer ({args.model_type})...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_type)
    model = AutoModel.from_pretrained(args.model_type).to(device)
    model.eval()

    # Main progress bar for investors
    investor_pbar = tqdm(sorted(investor_files.items()), desc="[Investors]")
    for investor, files in investor_pbar:
        investor_pbar.set_description(f"[Investors] Current: {investor}")
        all_embeddings = []
        
        # Progress bar for files of current investor
        file_pbar = tqdm(sorted(files), desc=f"  [Files: {investor}]", leave=False)
        for file in file_pbar:
            period = parse_period(file.name)
            file_pbar.set_description(f"  [Files: {investor}] {file.name}")
            
            text = extract_text(file)
            
            if not text.strip():
                continue
                
            doc_embedding = embed_document(text, model, tokenizer, device)
            if doc_embedding is not None:
                investor_id = f"INV_{investor.upper()}"
                
                res = {
                    "investor_id": investor_id,
                    "timestamp": period["timestamp"],
                    "Date": period["timestamp"],
                    "year": period["year"],
                    "quarter": period["quarter"],
                    "half": period["half"],
                    "period_type": period["period_type"],
                    "filename": file.name,
                    "source_ext": file.suffix.lower().lstrip("."),
                    "word_count": len(text.split()),
                }
                # Add embedding dimensions as columns
                for i, val in enumerate(doc_embedding):
                    res[f"dim_{i}"] = val
                    
                all_embeddings.append(res)
                
        if all_embeddings:
            # save embedding to output_file path as a csv file
            df = pd.DataFrame(all_embeddings)
            output_csv = output_path / f"finbert_embeddings_{investor}.csv"
            df.to_csv(output_csv, index=False)
            
    print("\n✅ Embedding extraction completed successfully!")

if __name__ == "__main__":
    main()
