import urllib.request
import urllib.error
import json
import sys

BASE = "http://127.0.0.1:8000"

def req(url, data=None, headers=None, method=None):
    if headers is None:
        headers = {}
    if data is not None and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req_obj) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

print("--- Testing Live SmartLearn APIs against Real Supabase PostgreSQL ---")

# 1. Health
status, body = req(f"{BASE}/")
assert status == 200, f"Health check failed: {body}"
print("1. Health check: OK ->", body)

# 2. Register & Login
email = "livetest_student@smartlearn.local"
pwd = "LiveDemoPassword123!"
status, body = req(f"{BASE}/auth/register", data={"email": email, "password": pwd, "role": "student"})
if status not in (200, 400):
    raise AssertionError(f"Register failed: {status}, {body}")

status, body = req(f"{BASE}/auth/login", data={"email": email, "password": pwd})
assert status == 200, f"Login failed: {status}, {body}"
token = body["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("2. Register & Login: OK")

# 3. User Profile
status, body = req(f"{BASE}/auth/me", headers=headers)
assert status == 200
user_id = body["id"]
print(f"3. Profile /auth/me: OK (user_id={user_id})")

# 4. Roadmap
status, roadmap = req(f"{BASE}/api/path-planning/roadmap?user_id={user_id}&weekly_budget=180", headers=headers)
assert status == 200, f"Roadmap failed: {status}, {roadmap}"
print(f"4. Personalized Roadmap: OK ({len(roadmap['topics'])} topics evaluated)")

# 5. Next Topic
status, next_topic = req(f"{BASE}/api/path-planning/next-topic?user_id={user_id}", headers=headers)
assert status == 200, f"Next topic failed: {status}, {next_topic}"
topic_name = next_topic["next_topic"]
print(f"5. Next Recommended Topic: OK (Topic: {topic_name})")

# 6. CMAB LinUCB Recommendation
status, rec = req(f"{BASE}/api/path-planning/bandit/recommendation?user_id={user_id}&topic={topic_name}", headers=headers)
assert status == 200, f"Bandit recommendation failed: {status}, {rec}"
print(f"6. LinUCB Arm Recommendation: OK (Format: {rec['recommended_format']}, Resource: {rec['resource']['title']})")

# 7. Start Quiz
status, questions = req(f"{BASE}/quiz/start?topic={topic_name}", headers=headers)
assert status == 200, f"Start quiz failed: {status}, {questions}"
print(f"7. Quiz Start: OK ({len(questions)} questions loaded from Supabase)")

# 8. Submit Quiz
answers = [{"question_id": q["id"], "selected_answer": q["options"][0]} for q in questions]
status, quiz_res = req(f"{BASE}/quiz/submit", data={"topic": topic_name, "answers": answers}, headers=headers)
assert status == 200, f"Quiz submit failed: {status}, {quiz_res}"
score = quiz_res.get("score", 0)
print(f"8. Quiz Submit: OK (Score: {score:.2f})")

# 9. Bandit Feedback
feedback_payload = {
    "user_id": user_id,
    "topic": topic_name,
    "chosen_arm": rec["recommended_format"],
    "pre_mastery": 0.2,
    "post_mastery": 0.7,
    "quiz_score": 0.8
}
status, fb_res = req(f"{BASE}/api/path-planning/bandit/feedback", data=feedback_payload, headers=headers)
assert status == 200, f"Bandit feedback failed: {status}, {fb_res}"
print(f"9. Bandit Feedback: OK (Reward: {fb_res['reward']}, Status: {fb_res['status']})")

# 10. Security: Cross-user access blocked
req(f"{BASE}/auth/register", data={"email": "attacker@smartlearn.local", "password": "AttackerPassword123!", "role": "student"})
_, attacker_login = req(f"{BASE}/auth/login", data={"email": "attacker@smartlearn.local", "password": "AttackerPassword123!"})
attacker_token = attacker_login["access_token"]
attacker_headers = {"Authorization": f"Bearer {attacker_token}"}
status, body = req(f"{BASE}/api/path-planning/roadmap?user_id={user_id}", headers=attacker_headers)
assert status == 403, f"Cross-user authorization check failed! Status was {status}, expected 403"
print(f"10. Security Authorization: OK (HTTP {status} Forbidden on cross-user access)")

print("\n>>> ALL 10 LIVE SMOKE TESTS PASSED ON REAL FASTAPI + SUPABASE! <<<")
