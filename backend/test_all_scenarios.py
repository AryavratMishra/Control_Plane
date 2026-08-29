import urllib.request, json, time
time.sleep(1)

def call(scenario):
    url = f"http://localhost:8000/api/v1/demo/run/{scenario}"
    req = urllib.request.Request(url, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    result = d.get("result", {})
    decision = result.get("decision", "?")
    score = result.get("risk", {}).get("overall", {}).get("score", 0)
    ms = result.get("total_evaluation_ms", 0)
    reasons = result.get("reasons", [])
    pii = len(result.get("pii_entities", []))
    reason0 = reasons[0][:60] if reasons else "-"
    return decision, score, ms, pii, reason0

scenarios = ["safe", "hallucination", "pii", "cost_anomaly", "escalation"]
print(f"{'Scenario':<20} | {'Decision':<10} | Score | ms  | PII | Reason")
print("-" * 95)
for s in scenarios:
    try:
        decision, score, ms, pii, reason0 = call(s)
        print(f"{s:<20} | {decision:<10} | {score:.3f} | {ms:<4} | {pii}   | {reason0}")
    except Exception as e:
        print(f"{s:<20} | ERROR: {e}")
