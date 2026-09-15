import urllib.request
import json
import time

def test_model(model_name):
    print(f"\n--- Testing {model_name} ---")
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello! Give 1 growth tip in 10 words."}],
        "stream": False
    }
    req = urllib.request.Request(
        "http://localhost:11434/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        res = urllib.request.urlopen(req, timeout=120)
        data = json.loads(res.read())
        elapsed = int((time.time() - t0) * 1000)
        content = data["choices"][0]["message"]["content"]
        print(f"Success in {elapsed}ms: {content.strip()}")
    except Exception as e:
        print(f"Failed {model_name} after {int((time.time()-t0)*1000)}ms: {e}")

if __name__ == "__main__":
    test_model("qwen3:4b")
    test_model("qwen3:8b")
    test_model("llama3.1:8b")
