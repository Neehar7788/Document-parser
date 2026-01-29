# monitor.py - Monitors S3 and adds jobs to queue
import boto3
from redis import Redis
from rq import Queue
import time
from datetime import datetime

# Configuration
AWS_ACCESS_KEY_ID = "AKIAQMEY5UXOESDEAXZF"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "ap-south-1"
S3_BUCKET_NAME = "alfago-company-data"
S3_PREFIX = ""

CHECK_INTERVAL = 30  # Check every 30 seconds
PROCESSED_FILES_LOG = "processed_files.txt"

def get_s3_client():
    return boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=AWS_REGION)

def list_s3_documents():
    s3_client = get_s3_client()
    documents = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=S3_PREFIX)
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.lower().endswith(('.pdf', '.txt')):
                        documents.append(key)
        return documents
    except Exception as e:
        print(f"❌ S3 Error: {e}")
        return []

def load_processed_files():
    try:
        with open(PROCESSED_FILES_LOG, 'r') as f:
            return set(line.strip() for line in f.readlines())
    except:
        return set()

def mark_as_processed(s3_key):
    with open(PROCESSED_FILES_LOG, 'a') as f:
        f.write(f"{s3_key}\n")

def monitor():
    # Connect to Redis
    redis_conn = Redis(host='localhost', port=6379, db=0)
    queue = Queue('default', connection=redis_conn)
    
    print("🔄 Monitor started!")
    print(f"📂 S3 Bucket: {S3_BUCKET_NAME}")
    print(f"📂 Prefix: {S3_PREFIX}")
    print(f"⏱️  Check Interval: {CHECK_INTERVAL}s")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] 🔍 Checking S3...")
            
            all_files = list_s3_documents()
            processed = load_processed_files()
            new_files = [f for f in all_files if f not in processed]
            
            if new_files:
                print(f"📁 Found {len(new_files)} new files")
                
                for s3_key in new_files:
                    # Add job to queue
                    from worker import process_document
                    job = queue.enqueue(process_document, s3_key, 
                                       job_timeout='30m',  # 30 min timeout
                                       result_ttl=3600)    # Keep result for 1 hour
                    
                    mark_as_processed(s3_key)
                    print(f"✅ Queued: {s3_key} (Job ID: {job.id})")
                
                # Show queue stats
                print(f"📊 Queue length: {len(queue)}")
            else:
                print(f"✅ No new files")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    monitor()
