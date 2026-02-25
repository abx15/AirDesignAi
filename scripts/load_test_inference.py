import asyncio
import httpx
import time
import base64
import json
from typing import List, Dict
import statistics

# A tiny 1x1 white pixel PNG as base64 for testing
TEST_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

async def test_solve_endpoint(client: httpx.AsyncClient, url: str, token: str) -> Dict:
    start_time = time.perf_counter()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"image_base64": TEST_IMAGE_BASE64}
    
    try:
        response = await client.post(f"{url}/solve/", json=payload, headers=headers, timeout=10.0)
        duration = time.perf_counter() - start_time
        return {
            "status_code": response.status_code,
            "duration": duration,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "status_code": 0,
            "duration": time.perf_counter() - start_time,
            "success": False,
            "error": str(e)
        }

async def run_load_test(url: str, token: str, concurrency: int, num_requests: int):
    print(f"\n--- Starting Load Test (Concurrency: {concurrency}, Total Requests: {num_requests}) ---")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        # We'll drip feed them based on concurrency if we wanted more control, 
        # but simple asyncio.gather of batches works for a basic load test.
        
        results = []
        for i in range(0, num_requests, concurrency):
            batch_size = min(concurrency, num_requests - i)
            batch_tasks = [test_solve_endpoint(client, url, token) for _ in range(batch_size)]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
    durations = [r["duration"] for r in results if r["success"]]
    success_count = sum(1 for r in results if r["success"])
    fail_count = num_requests - success_count
    
    if durations:
        avg_time = statistics.mean(durations)
        p95_time = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations)
        min_time = min(durations)
        max_time = max(durations)
    else:
        avg_time = p95_time = min_time = max_time = 0

    print(f"Results:")
    print(f"  Success: {success_count}/{num_requests}")
    print(f"  Failures: {fail_count}")
    print(f"  Avg Response Time: {avg_time:.4f}s")
    print(f"  P95 Response Time: {p95_time:.4f}s")
    print(f"  Min/Max Time: {min_time:.4f}s / {max_time:.4f}s")
    print(f"  Throughput: {success_count / sum(r['duration'] for r in results):.2f} req/s (cumulative)")

async def main():
    # Configuration - assume default local dev setup or environment variables
    BASE_URL = "http://localhost:8000"
    
    # In a real test, you'd login or use a test token
    # For now, we'll try to get a token or expect the user to provide one if needed
    # Let's check if we can skip auth for this specific test or if we need to create a test user
    print("Pre-flight: Checking connectivity...")
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{BASE_URL}/health")
            print(f"Health check: {health.status_code}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return

    # Mock token or real one if available
    # Since we have control, we could generate a token if we have a test user
    TEST_TOKEN = "TEST_TOKEN" # Placeholder
    
    # Let's run a small test first
    await run_load_test(BASE_URL, TEST_TOKEN, concurrency=5, num_requests=20)
    await run_load_test(BASE_URL, TEST_TOKEN, concurrency=10, num_requests=50)

if __name__ == "__main__":
    asyncio.run(main())
