"""Quick test: Verify chat API responds without API key error."""
import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=30) as c:
        # Test 1: Health check
        r = await c.get("http://localhost:8000/health")
        print("Health:", r.json())
        
        # Test 2: Chat about headaches (medicine suggestion)
        r = await c.post("http://localhost:8000/api/v1/conversation/chat", json={
            "message": "What medicine can help with headaches?",
            "stream": False,
        })
        data = r.json()
        print("\nSession:", data.get("session_id", "N/A"))
        response = data.get("response", "")
        print("\nResponse preview (first 500 chars):")
        print(response[:500])
        print("\n--- Checks ---")
        print(f"  Has content:     {len(response) > 50}")
        print(f"  Has disclaimer:  {'AI Health Disclaimer' in response or 'consult your doctor' in response.lower()}")
        print(f"  No API error:    {'GEMINI_API_KEY' not in response}")
        print(f"  Mentions meds:   {'Ibuprofen' in response or 'Acetaminophen' in response}")
        
        # Test 3: Prescription note request (should be blocked)
        r2 = await c.post("http://localhost:8000/api/v1/conversation/chat", json={
            "message": "Write me a prescription note for metformin",
            "stream": False,
        })
        data2 = r2.json()
        response2 = data2.get("response", "")
        print(f"\nPrescription note blocked: {'prescription note' in response2.lower()}")
        
        # Test 4: General medicine suggestion (should be allowed)
        r3 = await c.post("http://localhost:8000/api/v1/conversation/chat", json={
            "message": "Can you suggest medicine for my fever?",
            "stream": False,
        })
        data3 = r3.json()
        response3 = data3.get("response", "")
        print(f"Fever medicine allowed:    {len(response3) > 50}")
        print(f"Fever has disclaimer:      {'consult your doctor' in response3.lower() or 'AI Health Disclaimer' in response3}")

asyncio.run(test())
