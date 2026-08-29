import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as c:
        r = await c.post("http://localhost:8000/api/v1/demo/run/hallucination", timeout=30)
        d = r.json()
        result = d.get("result", {})
        decision = result.get("decision")
        overall = result.get("risk", {}).get("overall", {})
        reasons = result.get("reasons", [])[:2]
        total_ms = result.get("total_evaluation_ms")
        print(f"Scenario: hallucination")
        print(f"Decision: {decision}")
        print(f"Overall: {overall}")
        print(f"Reasons: {reasons}")
        print(f"Total ms: {total_ms}")
        
        r2 = await c.post("http://localhost:8000/api/v1/demo/run/pii", timeout=30)
        d2 = r2.json()
        result2 = d2.get("result", {})
        print(f"\nScenario: pii")
        print(f"Decision: {result2.get('decision')}")
        print(f"PII entities: {len(result2.get('pii_entities', []))}")
        
        r3 = await c.post("http://localhost:8000/api/v1/demo/run/escalation", timeout=30)
        d3 = r3.json()
        result3 = d3.get("result", {})
        print(f"\nScenario: escalation")
        print(f"Decision: {result3.get('decision')}")

asyncio.run(test())
