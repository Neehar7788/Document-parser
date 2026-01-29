# dashboard.py - View queue status
from redis import Redis
from rq import Queue
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
import time

redis_conn = Redis(host='localhost', port=6379, db=0)
queue = Queue('default', connection=redis_conn)

print("📊 QUEUE DASHBOARD - Press Ctrl+C to stop\n")

while True:
    try:
        started = StartedJobRegistry('default', connection=redis_conn)
        finished = FinishedJobRegistry('default', connection=redis_conn)
        failed = FailedJobRegistry('default', connection=redis_conn)
        
        print("\033[2J\033[H")  # Clear screen
        print("="*50)
        print("📊 QUEUE DASHBOARD")
        print("="*50)
        print(f"⏳ Queued:     {len(queue)}")
        print(f"🔄 Processing: {len(started)}")
        print(f"✅ Finished:   {len(finished)}")
        print(f"❌ Failed:     {len(failed)}")
        print("="*50)
        print(f"\nRefreshing every 5 seconds...")
        
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
