import urllib.request
import json
import traceback

def test_embed(prompt_len):
    text = "Product growth retention metrics and customer acquisition loops. " * prompt_len
    data = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        res = urllib.request.urlopen(req, timeout=30)
        emb = json.loads(res.read())["embedding"]
        print(f"Success prompt len {len(text)} chars -> dim {len(emb)}")
    except Exception as e:
        print(f"Failed prompt len {len(text)} chars: {e}")

if __name__ == "__main__":
    test_embed(0)
    test_embed(1)
    test_embed(50)
    test_embed(200)
    test_embed(500)
    test_embed(1000)
    test_embed(2000)
