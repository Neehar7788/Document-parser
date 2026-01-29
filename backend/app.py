"""
Document Chatbot Backend - FastAPI Server
Hybrid search using vector embeddings + keyword matching
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from keybert import KeyBERT
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

app = FastAPI(title="Document Chatbot API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL Configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DATABASE = os.getenv("PG_DATABASE", "CHATBOT")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "Abhiram@007")
PG_TABLE = "document_vectors"

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize models
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT()

# PostgreSQL Connection Pool
def get_pg_connection():
    """Create PostgreSQL connection"""
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    register_vector(conn)
    return conn

# ============================================================
# MODELS
# ============================================================

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    use_keywords: Optional[bool] = True
    similarity_threshold: Optional[float] = 0.3

class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[List[dict]] = []
    top_k: Optional[int] = 5

class DocumentChunk(BaseModel):
    file_name: str
    page_num: int
    chunk_id: str
    chunk_type: str
    chunk_text: str
    keywords: List[str]
    financial_keywords: List[str]
    similarity_score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[DocumentChunk]
    query_keywords: List[str]

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def extract_query_keywords(query: str, top_n: int = 5) -> List[str]:
    """Extract keywords from user query"""
    try:
        keywords = kw_model.extract_keywords(query, top_n=top_n)
        return [kw[0] for kw in keywords]
    except Exception as e:
        print(f"Keyword extraction error: {e}")
        # Fallback: extract important words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', query.lower())
        return list(set(words))[:top_n]

def vectorize_query(query: str) -> List[float]:
    """Convert query to embedding vector"""
    embedding = embed_model.encode(query)
    return embedding.tolist()

def hybrid_search(
    query: str,
    top_k: int = 5,
    use_keywords: bool = True,
    similarity_threshold: float = 0.3
) -> List[dict]:
    """
    Hybrid search combining:
    1. Vector similarity search
    2. Keyword matching (optional)
    """
    
    # Extract keywords from query
    query_keywords = extract_query_keywords(query)
    print(f"Query keywords: {query_keywords}")
    
    # Vectorize query
    query_vector = vectorize_query(query)
    
    # Build the search query
    # Note: Supabase uses pgvector for similarity search
    # We'll fetch more results initially and then filter/rank
    
    try:
        # Vector similarity search using PostgreSQL
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Call match_documents function
        cursor.execute(
            "SELECT * FROM match_documents(%s::vector, %s, %s)",
            (query_vector, similarity_threshold, top_k * 3)
        )
        
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        print(f"Found {len(results)} results from vector search")
        
        if results:
            print(f"Top result: {results[0].get('file_name')} - similarity: {results[0].get('similarity', 0):.3f}")
            print(f"Top result text length: {len(results[0].get('chunk_text', ''))} chars")
        
    except Exception as e:
        print(f"Vector search error: {e}")
        # Fallback to keyword-only search
        results = keyword_only_search(query_keywords, top_k * 3)
        print(f"Found {len(results)} results from keyword search")
    
    # Apply keyword boosting if enabled
    if use_keywords and query_keywords:
        results = boost_by_keywords(results, query_keywords)
    
    # Sort by similarity and return top_k
    results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k]
    
    return results

def keyword_only_search(keywords: List[str], limit: int = 15) -> List[dict]:
    """Fallback keyword-based search"""
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build OR conditions for keyword search
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("(keywords ILIKE %s OR financial_keywords ILIKE %s OR chunk_text ILIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        
        where_clause = " OR ".join(conditions)
        query = f"SELECT * FROM {PG_TABLE} WHERE {where_clause} LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        # Add dummy similarity score
        for result in results:
            result['similarity'] = 0.5
        
        return results
    except Exception as e:
        print(f"Keyword search error: {e}")
        return []

def boost_by_keywords(results: List[dict], query_keywords: List[str]) -> List[dict]:
    """Boost similarity scores based on keyword matches"""
    for result in results:
        keyword_boost = 0
        
        # Parse stored keywords
        try:
            doc_keywords = json.loads(result.get('keywords', '[]'))
            doc_fin_keywords = json.loads(result.get('financial_keywords', '[]'))
            all_doc_keywords = [k.lower() for k in doc_keywords + doc_fin_keywords]
        except:
            all_doc_keywords = []
        
        # Count matching keywords
        for qk in query_keywords:
            if qk.lower() in all_doc_keywords:
                keyword_boost += 0.1
            # Check in chunk text
            if qk.lower() in result.get('chunk_text', '').lower():
                keyword_boost += 0.05
        
        # Apply boost
        current_similarity = result.get('similarity', 0)
        result['similarity'] = min(1.0, current_similarity + keyword_boost)
    
    return results

def generate_answer_with_gemini(question: str, context_chunks: List[dict], conversation_history: List[dict] = []) -> str:
    """Generate answer using Gemini API with retrieved context"""
    
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
    
    # Prepare context from retrieved chunks
    context_text = "\n\n".join([
        f"[Source: {chunk['file_name']}, Page {chunk['page_num']}, Type: {chunk['chunk_type']}]\n{chunk['chunk_text']}"
        for chunk in context_chunks
    ])
    
    # Debug: Print context length and preview
    print(f"\n=== CONTEXT SENT TO AI ===")
    print(f"Number of chunks: {len(context_chunks)}")
    print(f"Total context length: {len(context_text)} characters")
    for i, chunk in enumerate(context_chunks[:3]):  # Show first 3 chunks
        print(f"\nChunk {i+1}: {chunk['file_name']} (Page {chunk['page_num']})")
        print(f"Text length: {len(chunk.get('chunk_text', ''))} chars")
        print(f"Preview: {chunk.get('chunk_text', '')[:200]}...")
    print(f"=========================\n")
    
    # Build conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
    
    # Create prompt
    prompt = f"""You are a helpful AI assistant that answers questions based on document context.

Previous Conversation:
{history_text if history_text else "No previous conversation"}

Document Context (from multiple sources):
{context_text}

User Question: {question}

Instructions:
1. Synthesize information from ALL provided document chunks to give a complete answer
2. If chunks contain partial information, combine them to provide the full picture
3. If the context mentions a topic but lacks details, acknowledge what IS mentioned
4. Cite sources by mentioning the file name and page number
5. Be comprehensive - extract ALL relevant information from the context
6. For financial questions, be precise with numbers and units
7. If information seems incomplete, state what you found and what's missing
8. Look for patterns across multiple chunks to build a complete answer

Answer:"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error generating answer: {str(e)}"

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "Document Chatbot API",
        "version": "1.0",
        "endpoints": ["/search", "/chat", "/health"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        pg_connected = True
    except:
        pg_connected = False
    
    return {
        "status": "healthy" if pg_connected else "degraded",
        "postgresql_connected": pg_connected,
        "gemini_configured": bool(GEMINI_API_KEY)
    }

@app.post("/search", response_model=List[DocumentChunk])
async def search_documents(request: QueryRequest):
    """Search documents using hybrid search"""
    try:
        results = hybrid_search(
            query=request.question,
            top_k=request.top_k,
            use_keywords=request.use_keywords,
            similarity_threshold=request.similarity_threshold
        )
        
        # Format results
        formatted_results = []
        for result in results:
            try:
                keywords = json.loads(result.get('keywords', '[]'))
                fin_keywords = json.loads(result.get('financial_keywords', '[]'))
            except:
                keywords = []
                fin_keywords = []
            
            formatted_results.append(DocumentChunk(
                file_name=result.get('file_name', ''),
                page_num=result.get('page_num', 0),
                chunk_id=result.get('chunk_id', ''),
                chunk_type=result.get('chunk_type', ''),
                chunk_text=result.get('chunk_text', ''),
                keywords=keywords,
                financial_keywords=fin_keywords,
                similarity_score=result.get('similarity', 0)
            ))
        
        return formatted_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with context-aware responses"""
    try:
        # Extract keywords from query
        query_keywords = extract_query_keywords(request.question)
        
        # Retrieve relevant documents
        results = hybrid_search(
            query=request.question,
            top_k=request.top_k,
            use_keywords=True,
            similarity_threshold=0.1  # Lower threshold to find more results
        )
        
        if not results:
            return ChatResponse(
                answer="I couldn't find any relevant information in the documents to answer your question. Please try rephrasing or asking about different topics.",
                sources=[],
                query_keywords=query_keywords
            )
        
        # Generate answer using Gemini
        answer = generate_answer_with_gemini(
            question=request.question,
            context_chunks=results,
            conversation_history=request.conversation_history
        )
        
        # Format sources
        sources = []
        for result in results:
            try:
                keywords = json.loads(result.get('keywords', '[]'))
                fin_keywords = json.loads(result.get('financial_keywords', '[]'))
            except:
                keywords = []
                fin_keywords = []
            
            sources.append(DocumentChunk(
                file_name=result.get('file_name', ''),
                page_num=result.get('page_num', 0),
                chunk_id=result.get('chunk_id', ''),
                chunk_type=result.get('chunk_type', ''),
                chunk_text=result.get('chunk_text', '')[:500] + "...",  # Truncate for response
                keywords=keywords,
                financial_keywords=fin_keywords,
                similarity_score=result.get('similarity', 0)
            ))
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            query_keywords=query_keywords
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get database statistics with last update timestamp"""
    try:
        conn = get_pg_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Count total chunks
        cursor.execute(f"SELECT COUNT(*) as count FROM {PG_TABLE}")
        total_chunks = cursor.fetchone()['count']
        
        # Get unique files
        cursor.execute(f"SELECT COUNT(DISTINCT file_name) as count FROM {PG_TABLE}")
        unique_files = cursor.fetchone()['count']
        
        # Get last update timestamp (if table has a timestamp column, otherwise use current time)
        # This helps frontend detect changes
        cursor.execute(f"SELECT MAX(created_at) as last_update FROM {PG_TABLE}")
        result = cursor.fetchone()
        last_update = result['last_update'] if result and result['last_update'] else None
        
        cursor.close()
        conn.close()
        
        return {
            "total_chunks": total_chunks,
            "unique_files": unique_files,
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": "gemini-2.0-flash-exp",
            "last_update": last_update.isoformat() if last_update else None
        }
    except Exception as e:
        # If created_at column doesn't exist, return stats without timestamp
        try:
            conn = get_pg_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(f"SELECT COUNT(*) as count FROM {PG_TABLE}")
            total_chunks = cursor.fetchone()['count']
            
            cursor.execute(f"SELECT COUNT(DISTINCT file_name) as count FROM {PG_TABLE}")
            unique_files = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            return {
                "total_chunks": total_chunks,
                "unique_files": unique_files,
                "embedding_model": "all-MiniLM-L6-v2",
                "llm_model": "gemini-2.0-flash-exp",
                "last_update": None
            }
        except Exception as inner_e:
            raise HTTPException(status_code=500, detail=f"Stats error: {str(inner_e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
