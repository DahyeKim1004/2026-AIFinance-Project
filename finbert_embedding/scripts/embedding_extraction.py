"""
Investor의 Text 데이터를 FinBERT 모델을 이용하여 임베딩을 추출하는 스크립트

Usage-User:
    python finbert_embedding/scripts/embedding_extraction.py --model_type ProsusAI/finbert --input_file TextData-Processing/data/raw/{investor_name} --output_file finbert_embedding/results

    Args:
        --model_type: 모델 타입 (default: 'ProsusAI/finbert')
        --input_file: 입력 디렉토리 경로 (default: 'TextData-Processing/data/raw')
        --output_file: 결과 저장 디렉토리 경로 (default: 'finbert_embedding/results')
    
    Returns:
        Processed csv file with embedding extracted from each investor's text data
"""

import os
import argparse
import pandas as pd
import torch
import fitz  # PyMuPDF
from transformers import AutoTokenizer, AutoModel
from pathlib import Path
import re
from tqdm import tqdm

def parse_date(filename):
    """
    Parses NQYY format from filename.
    Date is at the end of the raw pdf file names: ex) Buffet_01 means 2001, Grantham_19_Q1 means 2019-Q1
    """
    name_stem = Path(filename).stem
    
    # Check for Q format: Grantham_19_Q1
    q_match = re.search(r'Q([1-4])', name_stem, re.IGNORECASE)
    year_match = re.search(r'_(\d{2})(?:_|$)', name_stem)
    
    if not year_match:
        return "UNKNOWN"
    
    year_short = year_match.group(1)
    
    if q_match:
        quarter = q_match.group(1).upper()
        return f"{quarter}Q{year_short}"
    else:
        # Create a single row for the entire year (YYYY) if quarterly data does not exist
        year_full = f"20{year_short}" if int(year_short) < 50 else f"19{year_short}"
        return year_full

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

# extract embedding from text using FinBERT model
def get_embeddings(text, model, tokenizer, device):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use mean pooling of the last hidden state
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.cpu().numpy()

def main():
    parser = argparse.ArgumentParser(description="Extract FinBERT embeddings from Investor Text PDFs")
    parser.add_argument("--model_type", type=str, default="ProsusAI/finbert", help="FinBERT model type")
    parser.add_argument("--input_file", type=str, default="TextData-Processing/data/raw", help="Input directory containing raw PDFs (e.g. TextData-Processing/data/raw/{investor_name})")
    parser.add_argument("--output_file", type=str, default="finbert_embedding/results", help="Output directory for results")
    
    args = parser.parse_args()
    
    # device selection
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_type)
    model = AutoModel.from_pretrained(args.model_type).to(device)
    model.eval()
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # open raw pdf files in input_file path recursively
    all_pdf_files = list(input_path.rglob("*.pdf"))
    if not all_pdf_files:
        print(f"No PDF files found in {input_path}")
        return

    investor_files = {}
    for pdf_file in all_pdf_files:
        # Identify investor name from parent directory or prefix
        investor_name = pdf_file.parent.name if pdf_file.parent != input_path else pdf_file.stem.split('_')[0]
        if investor_name not in investor_files:
            investor_files[investor_name] = []
        investor_files[investor_name].append(pdf_file)
        
    print(f"Found {len(investor_files)} investors to process.")

    # Main progress bar for investors
    investor_pbar = tqdm(sorted(investor_files.items()), desc="[Investors]")
    for investor, files in investor_pbar:
        investor_pbar.set_description(f"[Investors] Current: {investor}")
        all_embeddings = []
        
        # Progress bar for files of current investor
        file_pbar = tqdm(sorted(files), desc=f"  [Files: {investor}]", leave=False)
        for file in file_pbar:
            date_nqyy = parse_date(file.name)
            file_pbar.set_description(f"  [Files: {investor}] {file.name}")
            
            # extract text from pdf files
            text = extract_text_from_pdf(file)
            
            if not text.strip():
                continue
                
            # extract embedding from text using FinBERT model
            tokens = tokenizer.encode(text, add_special_tokens=False)
            chunk_size = 510 
            chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
            
            file_embeddings = []
            # Progress bar for chunks within the file
            chunk_pbar = tqdm(chunks, desc="    [Chunks]", leave=False)
            for chunk in chunk_pbar:
                chunk_text = tokenizer.decode(chunk)
                emb = get_embeddings(chunk_text, model, tokenizer, device)
                file_embeddings.append(emb)
                
            if file_embeddings:
                # Average embeddings for the whole document
                doc_embedding = torch.tensor(file_embeddings).mean(dim=0).numpy().flatten()
                
                res = {
                    "investor_id": f"INV_{investor.upper()}",
                    "Date": date_nqyy,
                    "filename": file.name
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
