import time
import httpx
import json

def benchmark():
    client = httpx.Client(timeout=30.0)
    
    # 1. Health check latency
    t0 = time.time()
    res = client.get("http://localhost:8000/health")
    t_health = (time.time() - t0) * 1000
    print(f"[1] Health Check Latency: {t_health:.2f}ms | Status: {res.status_code}")
    
    # 2. Hybrid Search Latency
    t0 = time.time()
    payload = {"query": "How do Elena Verna and Brian Balfour describe B2B vs B2C growth loops?", "limit": 5}
    res = client.post("http://localhost:8000/api/v1/knowledge/search", json=payload)
    t_search = (time.time() - t0) * 1000
    data = res.json()
    results = data.get("results", [])
    print(f"[2] Hybrid Search Latency: {t_search:.2f}ms | Returned: {len(results)} chunks")
    for i, r in enumerate(results[:3]):
        speaker = r.get("speaker", "Unknown")
        title = r.get("episode_title", "Unknown")[:30]
        score = r.get("rrf_score", 0.0)
        print(f"    - Match {i+1}: {speaker} ({title}...) RRF Score: {score:.4f}")
        
    # 3. Provider List Latency
    t0 = time.time()
    res = client.get("http://localhost:8000/health/providers")
    t_providers = (time.time() - t0) * 1000
    providers_dict = res.json().get("providers", {})
    print(f"[3] Provider Health Latency: {t_providers:.2f}ms | Providers: {list(providers_dict.keys())}")
    for p_name, p_info in providers_dict.items():
        print(f"    - {p_name}: status={p_info.get('status')} models={p_info.get('models', [])}")

    # 4. Out-of-Domain Guardrail Latency
    t0 = time.time()
    payload = {"query": "Write a python script to scrape linkedin", "limit": 5}
    res = client.post("http://localhost:8000/api/v1/knowledge/search", json=payload)
    t_guard = (time.time() - t0) * 1000
    print(f"[4] Guardrail / Search Latency: {t_guard:.2f}ms | Status: {res.status_code}")

if __name__ == "__main__":
    benchmark()
