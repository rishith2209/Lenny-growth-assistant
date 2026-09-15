import asyncio
import json
import time
import httpx
from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.services.retrieval.engine import HybridRetrievalEngine
from apps.api.src.providers.ollama import OllamaProvider

async def main():
    print("=" * 80, flush=True)
    print(" LENNY GROWTH ASSISTANT — REAL END-TO-END GROUNDED PI WORKFLOW VERIFICATION", flush=True)
    print("=" * 80, flush=True)

    user_query = "What advice does Adam Fishman give regarding growth teams, competencies, and career frameworks?"
    print(f"\n[1] USER QUERY: \"{user_query}\"", flush=True)

    provider = OllamaProvider()
    
    # 1. First Turn: Send prompt to LLM with retrieve_knowledge_test tool definition
    tools = [
        {
            "name": "retrieve_knowledge_test",
            "description": "Retrieves podcast transcript insights, growth frameworks, and guest quotes from Lenny's Podcast.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for knowledge retrieval (e.g. 'Adam Fishman growth career framework')",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of chunks to retrieve (default 3)",
                    }
                },
                "required": ["query"]
            }
        }
    ]

    from apps.api.src.providers.base import ChatMessage, ToolDefinition
    tool_defs = [
        ToolDefinition(name=t["name"], description=t["description"], parameters=t["parameters"])
        for t in tools
    ]

    print("\n[2] PI AGENT (Turn 1): Evaluating user query with tool definitions...", flush=True)
    messages = [
        ChatMessage(
            role="system",
            content="You are the Lenny Growth Assistant. Always use the retrieve_knowledge_test tool to retrieve grounded facts from Lenny's podcast transcripts before answering growth questions."
        ),
        ChatMessage(role="user", content=user_query)
    ]

    t0 = time.time()
    resp1 = await provider.complete(messages=messages, tools=tool_defs, model="qwen3:4b")
    t1 = time.time()

    print(f"    Turn 1 Latency: {int((t1 - t0)*1000)}ms", flush=True)
    print(f"    Tool calls generated: {len(resp1.tool_calls or [])}", flush=True)

    if not resp1.tool_calls:
        print("    [!] No tool calls generated. Fallback to explicit search.", flush=True)
        tool_query = "Adam Fishman growth team career competencies framework"
        tool_call_id = "call_manual_1"
    else:
        tc = resp1.tool_calls[0]
        tool_call_id = tc.id
        tool_args = tc.arguments
        tool_query = tool_args.get("query", user_query) if isinstance(tool_args, dict) else user_query
        print(f"    Invoked Tool: {tc.name}", flush=True)
        print(f"    Tool Arguments: {json.dumps(tool_args)}", flush=True)

    # 2. Execute Hybrid Retrieval Engine directly over PostgreSQL + pgvector
    print(f"\n[3] FASTAPI / RETRIEVAL ENGINE: Executing Hybrid Search (Vector + BM25 + RRF) for: '{tool_query}'...", flush=True)
    async with AsyncSessionLocal() as session:
        engine = HybridRetrievalEngine(db_session=session, embedding_model="nomic-embed-text")
        search_res = await engine.search(query=tool_query, top_k=3)

    print(f"    Retrieved {len(search_res.results)} evidence chunks from PostgreSQL:", flush=True)
    for idx, r in enumerate(search_res.results, 1):
        print(f"    [{idx}] Episode: '{r.provenance.episode_title}' | Speaker: {r.provenance.speaker} | Timestamp: {r.provenance.timestamp_formatted}", flush=True)
        print(f"        RRF Score: {r.rrf_score:.4f} | Semantic Score: {r.semantic_score:.4f} | Lexical Score: {r.lexical_score:.4f}", flush=True)
        preview = r.content.replace("\n", " ")[:140]
        print(f"        Snippet: \"{preview}...\"", flush=True)

    # 3. Turn 2: Synthesize Grounded Response using evidence
    print("\n[4] PI AGENT (Turn 2): Synthesizing Grounded Answer with Provenance Citations...", flush=True)
    evidence_text_list = []
    for idx, r in enumerate(search_res.results, 1):
        evidence_text_list.append(
            f"[Source {idx}]: Episode '{r.provenance.episode_title}', Speaker: {r.provenance.speaker}, Timestamp: {r.provenance.timestamp_formatted or 'N/A'}\n"
            f"Content: {r.content}\n"
        )
    formatted_evidence = "\n---\n".join(evidence_text_list)
    
    messages_turn2 = [
        ChatMessage(
            role="system",
            content="You are the Lenny Growth Assistant. Synthesize a concise 2-3 paragraph answer strictly based on the retrieved transcript evidence. Always cite the speaker and episode."
        ),
        ChatMessage(role="user", content=user_query),
        ChatMessage(
            role="assistant",
            content="",
            tool_calls=resp1.tool_calls
        ),
        ChatMessage(
            role="tool",
            tool_call_id=tool_call_id,
            content=formatted_evidence
        )
    ]

    t2 = time.time()
    resp2 = await provider.complete(messages=messages_turn2, model="qwen3:4b")
    t3 = time.time()

    print(f"    Turn 2 Latency: {int((t3 - t2)*1000)}ms", flush=True)
    print("\n" + "=" * 80, flush=True)
    print(" GROUNDED AGENT RESPONSE:", flush=True)
    print("=" * 80, flush=True)
    print(resp2.content, flush=True)
    print("=" * 80, flush=True)
    print(f"Total Workflow Latency: {int((t3 - t0)*1000)}ms | Cost: ₹0.00 (Ollama Local)", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
