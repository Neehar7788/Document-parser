# worker.py - Run multiple instances of this
import os, re, json, uuid
import fitz
import pandas as pd
from PIL import Image
from io import BytesIO
import pytesseract
import tabula
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import TypedDict, List
import psycopg2
from psycopg2.extras import execute_batch
from pgvector.psycopg2 import register_vector
import boto3
from botocore.exceptions import ClientError
import tempfile
from redis import Redis
from rq import Worker, SimpleWorker

# Configuration
AWS_ACCESS_KEY_ID = "AKIAQMEY5UXOESDEAXZF"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "ap-south-1"
S3_BUCKET_NAME = "alfago-company-data"

OUTPUT_FOLDER = r"C:\Users\abhir\OneDrive\Desktop\DPCSV"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PG_HOST = "localhost"
PG_PORT = "5432"
PG_DATABASE = "CHATBOT"
PG_USER = "postgres"
PG_PASSWORD = "Abhiram@007"
PG_TABLE = "document_vectors"

MIN_CHUNK_LENGTH = 100
MIN_IMAGE_TEXT_LENGTH = 200
PROCESS_IMAGES = False

# Load models once per worker
print("🔄 Loading models...")
kw_model = KeyBERT()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Models loaded!")

# S3 and PostgreSQL functions
def get_s3_client():
    return boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=AWS_REGION)

def get_pg_connection():
    conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
                           user=PG_USER, password=PG_PASSWORD)
    register_vector(conn)
    return conn

def download_from_s3(s3_key):
    s3_client = get_s3_client()
    try:
        file_ext = os.path.splitext(s3_key)[1]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        temp_path = temp_file.name
        temp_file.close()
        s3_client.download_file(S3_BUCKET_NAME, s3_key, temp_path)
        return temp_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages.append((page_num, text))
    return pages

def extract_tables_from_pdf_fitz(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        tables = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            lines = text.split('\n')
            table_lines = [line for line in lines if '\t' in line or '  ' in line]
            if len(table_lines) > 2:
                rows = [line.split() for line in table_lines if line.strip()]
                if rows:
                    try:
                        df = pd.DataFrame(rows[1:], columns=rows[0] if len(rows) > 1 else None)
                        tables.append((page_num, df))
                    except:
                        pass
        return tables
    except:
        return []

def chunk_text(text, chunk_size=800, chunk_overlap=150):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                             length_function=len, separators=["\n\n", "\n", " "])
    docs = splitter.create_documents([text])
    return [d.page_content for d in docs]

def is_address_chunk(text):
    """Detect if chunk is primarily address/contact information"""
    text_lower = text.lower()
    
    # Strong address indicators - these alone indicate address chunk
    strong_patterns = [
        r'registered office',
        r'corporate office',
        r'head office',
        r'regd\.?\s*office',
        r'correspondence address',
        r'chartered accountants.*floor',  # CA firm addresses
        r'llp.*floor.*wing',  # LLP addresses with floor/wing
        r'\d+th\s+floor.*wing',  # "14th Floor, Central B Wing"
        r'telephone\s*:\s*\+?\d',  # Telephone: +91
        r'fax\s*:\s*\+?\d',  # Fax: +91
        r'mumbai\s*—\s*\d{6}',  # City with pin code
        r'bangalore\s*—\s*\d{6}',
        r'delhi\s*—\s*\d{6}',
        r'hyderabad\s*—\s*\d{6}',
        r'chennai\s*—\s*\d{6}',
        r'pune\s*—\s*\d{6}',
        r'india\s+telephone',  # "India Telephone:"
        r'nesco.*park',  # Specific building names
        r'western express highway',
        r'goregaon|andheri|bandra|worli',  # Mumbai localities
    ]
    
    # Check strong patterns
    for pattern in strong_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Multiple weak indicators together = address chunk
    weak_patterns = [
        r'\b(phone|tel|telephone|fax)',
        r'\b(email|e-mail)',
        r'\b(website|www\.)',
        r'\d{6}',  # Any 6-digit number (likely pin code)
        r'\b(road|street|avenue|floor|building|tower|complex|premises|wing)',
        r'\b(mumbai|bangalore|delhi|hyderabad|chennai|pune|kolkata)',
        r'\+91',  # India country code
        r'chartered accountants',
        r'\bllp\b',
    ]
    
    # Count weak matches
    weak_matches = sum(1 for pattern in weak_patterns if re.search(pattern, text_lower))
    
    # If 2+ weak indicators, it's likely an address
    if weak_matches >= 2:
        return True
    
    return False


def extract_keywords(text, top_n=8):
    try:
        keywords = [kw[0] for kw in kw_model.extract_keywords(text, top_n=top_n)]
    except:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        keywords = list(set(words))[:top_n]
    
    financial_terms = ["revenue", "profit", "loss", "income", "growth", "EBITDA", "EPS", "operating",
                      "cash flow", "margin", "expenditure", "cost", "assets", "liabilities", "equity",
                      "dividend", "ROI", "expenses", "tax", "sales"]
    fin_keywords = [kw for kw in keywords if kw.lower() in financial_terms or 
                   any(ft in kw.lower() for ft in financial_terms)]
    return keywords, fin_keywords

# Main processing function (called by RQ)
def process_document(s3_key):
    """Process a single document - this is the job function"""
    print(f"\n🚀 Processing: {s3_key}")
    
    file_name = os.path.basename(s3_key)
    file_ext = os.path.splitext(file_name)[1].lower()
    
    # Download
    temp_path = download_from_s3(s3_key)
    if not temp_path:
        raise Exception(f"Failed to download {s3_key}")
    
    try:
        # Extract
        all_chunks = []
        text_pages = extract_text_from_pdf(temp_path)
        tables = extract_tables_from_pdf_fitz(temp_path)
        
        # Process text
        for page_num, text in text_pages:
            for i, chunk in enumerate(chunk_text(clean_text(text))):
                if len(chunk) < MIN_CHUNK_LENGTH:
                    continue
                
                # Skip address chunks
                if is_address_chunk(chunk):
                    print(f"⏭️  Skipping address chunk on page {page_num}")
                    continue
                
                is_table = '\t' in chunk or (chunk.count('  ') > 10 and '\n' in chunk)
                chunk_type = "table" if is_table else "text"
                keywords, fin_keywords = extract_keywords(chunk)
                
                all_chunks.append({
                    "file_name": file_name,
                    "page_num": page_num,
                    "chunk_id": f"{chunk_type}_{page_num}_{i+1}",
                    "chunk_type": chunk_type,
                    "chunk_text": chunk,
                    "keywords": json.dumps(keywords, ensure_ascii=False),
                    "financial_keywords": json.dumps(fin_keywords, ensure_ascii=False)
                })
        
        # Process tables
        for tbl_num, table in tables:
            table_text = table.to_csv(index=False)
            keywords, fin_keywords = extract_keywords(table_text)
            all_chunks.append({
                "file_name": file_name,
                "page_num": tbl_num,
                "chunk_id": f"table_{tbl_num}",
                "chunk_type": "table",
                "chunk_text": table_text,
                "keywords": json.dumps(keywords, ensure_ascii=False),
                "financial_keywords": json.dumps(fin_keywords, ensure_ascii=False)
            })
        
        print(f"📊 Extracted: {len(all_chunks)} chunks")
        
        # Save CSV
        df = pd.DataFrame(all_chunks)
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
        csv_name = os.path.splitext(safe_name)[0] + "_extracted.csv"
        csv_path = os.path.join(OUTPUT_FOLDER, csv_name)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV saved")
        
        # Vectorize
        texts = []
        for idx, row in df.iterrows():
            try:
                parsed_kws = json.loads(row["keywords"])
                texts.append(' '.join(parsed_kws) if parsed_kws else row["chunk_text"][:100])
            except:
                texts.append(row["chunk_text"][:100])
        
        embeddings = embed_model.encode(texts, batch_size=16, show_progress_bar=False)
        
        # Store in PostgreSQL
        records = []
        for i, row in df.iterrows():
            record = (str(uuid.uuid4()), row["file_name"], int(row["page_num"]),
                     row["chunk_id"], row["chunk_type"], row["chunk_text"],
                     row["keywords"], row["financial_keywords"], embeddings[i].tolist())
            records.append(record)
        
        conn = get_pg_connection()
        cursor = conn.cursor()
        insert_query = f"""INSERT INTO {PG_TABLE} 
            (id, file_name, page_num, chunk_id, chunk_type, chunk_text, keywords, financial_keywords, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        execute_batch(cursor, insert_query, records, page_size=50)
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Inserted {len(records)} records")
        
        # Cleanup
        os.unlink(temp_path)
        
        return {"status": "success", "file": file_name, "chunks": len(records)}
        
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e

# Start worker
if __name__ == '__main__':
    redis_conn = Redis(host='localhost', port=6379, db=0)
    # Use SimpleWorker for Windows (no fork support)
    worker = SimpleWorker(['default'], connection=redis_conn)
    print("🔄 Worker started! Waiting for jobs...")
    worker.work()
