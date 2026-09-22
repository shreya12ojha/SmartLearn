"""
Live Integration Check for SmartLearn Backend & CMAB System
Validates live HTTP API endpoints on http://127.0.0.1:8000
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, data=None, headers=None, method=None):
    if headers is None:
        headers = {}
    if data is not None and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body


def run_live_integration():
    print("=" * 60)
    print("SMARTLEARN LIVE INTEGRATION VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    # 1. Health Check
    status, body = make_request(f"{BASE_URL}/")
    assert status == 200, f"Health check failed ({status}): {body}"
    print("[PASS] 1. Health Check OK ->", body)

    # 2. Authentication (Signup / Login)
    test_email = "student_live_verifier@example.com"
    test_password = "SecurePassword123!"
    test_name = "LiveVerifier"

    # Attempt signup first
    status, body = make_request(
        f"{BASE_URL}/api/auth/signup",
        data={"name": test_name, "email": test_email, "password": test_password},
    )
    if status == 200:
        token = body["token"]
        user_id = body["user_id"]
        print(f"[PASS] 2. Signup OK (User ID: {user_id})")
    elif status == 400:
        # Already registered, perform login
        status, body = make_request(
            f"{BASE_URL}/api/auth/login",
            data={"email": test_email, "password": test_password},
        )
        assert status == 200, f"Login failed ({status}): {body}"
        token = body["token"]
        user_id = body["user_id"]
        print(f"[PASS] 2. Login OK (User ID: {user_id})")
    else:
        raise AssertionError(f"Auth failed with status {status}: {body}")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Roadmap API (GET /api/path-planning/roadmap/{user_id})
    status, roadmap = make_request(
        f"{BASE_URL}/api/path-planning/roadmap/{user_id}",
        headers=auth_headers,
    )
    assert status == 200, f"Roadmap failed ({status}): {roadmap}"
    assert "roadmap" in roadmap, "Roadmap response missing 'roadmap' field"
    assert "summary" in roadmap, "Roadmap response missing 'summary' field"
    print(f"[PASS] 3. Roadmap API OK (Topics evaluated: {len(roadmap['roadmap'])})")

    # 4. Next Topic API (GET /api/path-planning/next-topic/{user_id})
    status, next_topic_resp = make_request(
        f"{BASE_URL}/api/path-planning/next-topic/{user_id}",
        headers=auth_headers,
    )
    assert status == 200, f"Next topic failed ({status}): {next_topic_resp}"
    next_topic = next_topic_resp.get("next_topic") or roadmap.get("next_topic")
    assert next_topic is not None, "Expected next topic to be available"
    topic_id = next_topic["topic_id"]
    topic_name = next_topic["topic_name"]
    print(f"[PASS] 4. Next Topic API OK (Next Topic: ID {topic_id} - '{topic_name}')")

    # 5. CMAB / LinUCB Resource Recommendation (GET /api/recommendations/resource)
    status, cmab_rec = make_request(
        f"{BASE_URL}/api/recommendations/resource?user_id={user_id}&topic_id={topic_id}",
        headers=auth_headers,
    )
    assert status == 200, f"CMAB recommendation failed ({status}): {cmab_rec}"
    selected_arm = cmab_rec.get("selected_arm")
    assert selected_arm in ["video", "text", "practice", "interactive"], f"Invalid arm: {selected_arm}"
    ucb_score = cmab_rec.get("ucb_score", 0.0)
    print(f"[PASS] 5. CMAB LinUCB Recommendation OK (Arm: '{selected_arm}', Score: {ucb_score:.3f})")

    # 6. Quiz Questions (GET /api/quiz?topic={topic_id})
    status, quiz_data = make_request(
        f"{BASE_URL}/api/quiz?topic={topic_id}",
        headers=auth_headers,
    )
    assert status == 200, f"Quiz load failed ({status}): {quiz_data}"
    questions = quiz_data.get("questions", [])
    assert len(questions) > 0, "No questions found for topic"
    print(f"[PASS] 6. Quiz Engine OK ({len(questions)} questions loaded)")

    # 7. Quiz Submission (POST /api/quiz/submit)
    answers = [
        {"question_id": q["id"], "selected_option": list(q["options"].keys())[0]}
        for q in questions
    ]
    status, submit_resp = make_request(
        f"{BASE_URL}/api/quiz/submit",
        data={"user_id": user_id, "answers": answers, "quiz_type": "diagnostic"},
        headers=auth_headers,
    )
    assert status == 200, f"Quiz submit failed ({status}): {submit_resp}"
    mastery_map = submit_resp.get("mastery", {})
    post_mastery = float(mastery_map.get(str(topic_id), mastery_map.get(topic_id, 0.5)))
    pre_mastery = float(next_topic.get("mastery_score", 0.0))
    print(f"[PASS] 7. Quiz Submission OK (Pre-Mastery: {pre_mastery:.2f} -> Post-Mastery: {post_mastery:.2f})")

    # 8. LinUCB Bandit Feedback (POST /api/recommendations/feedback)
    status, feedback_resp = make_request(
        f"{BASE_URL}/api/recommendations/feedback",
        data={
            "user_id": user_id,
            "topic_id": topic_id,
            "selected_arm": selected_arm,
            "pre_mastery": pre_mastery,
            "post_mastery": post_mastery,
        },
        headers=auth_headers,
    )
    assert status == 200, f"Bandit feedback failed ({status}): {feedback_resp}"
    reward = feedback_resp.get("reward", 0.0)
    print(f"[PASS] 8. LinUCB Bandit Feedback OK (Reward: {reward:+.3f}, Message: {feedback_resp.get('message')})")

    # 9. Security: Cross-User Authorization Gating (HTTP 403)
    fake_user_id = user_id + 9999
    status, forbidden_resp = make_request(
        f"{BASE_URL}/api/path-planning/roadmap/{fake_user_id}",
        headers=auth_headers,
    )
    assert status == 403, f"Expected 403 Forbidden on cross-user access, got: {status}"
    print(f"[PASS] 9. Cross-User Security OK (HTTP {status} Forbidden on mismatched user ID)")

    print("=" * 60)
    print("ALL LIVE INTEGRATION CHECKS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_live_integration()
