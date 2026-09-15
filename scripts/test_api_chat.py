import urllib.request
import json
import time

def test_api_chat():
    payload = {
        "model": "qwen3:4b",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "stream": False,
        "options": {"num_predict": 50, "temperature": 0.1}
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    res = urllib.request.urlopen(req, timeout=120)
    data = json.loads(res.read())
    print(f"/api/chat success in {int((time.time()-t0)*1000)}ms: {data['message']['content']}")

if __name__ == "__main__":
    test_api_chat()
