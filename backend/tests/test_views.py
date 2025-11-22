import os
import sys
# make project root (parent of 'backend') available on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if project_root not in sys.path:
    print(f"Adding {project_root} to sys.path")
    sys.path.insert(0, project_root)
else:
    print(f"{project_root} already in sys.path. Continuing...")

import requests
import re
import dotenv
dotenv.load_dotenv()

BASE_URL_TEST = os.getenv("BASE_URL_TEST", "http://localhost:5000")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD") 

def login(session, TEST_EMAIL, TEST_PASSWORD):
    login_url = f"{BASE_URL_TEST}/login"
    print(f"Logging in with: {TEST_EMAIL=}, {TEST_PASSWORD=}")
    resp = session.post(login_url, data={"email": TEST_EMAIL, "password": TEST_PASSWORD}, allow_redirects=True)
    print("Login response status:", resp.status_code)
    return resp

def test_register():
    session = requests.Session()
    register_url = f"{BASE_URL_TEST}/register"
    test_username = "testuser"
    test_email = "testuser@example.com"
    test_password = "TestPassword123!"
    test_confirm_password = "TestPassword123!"
    resp = session.post(register_url, data={
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "confirm_password": test_confirm_password
    }, allow_redirects=True)
    assert resp.status_code == 200
    assert "registration successful" in resp.text.lower() or "login" in resp.text.lower()
    print(f"✅ test_register: Registration successful.Status code: {resp.status_code}")

def test_dashboard_requires_login():
    session = requests.Session()
    resp = session.get(f"{BASE_URL_TEST}/app/dashboard", allow_redirects=False)
    assert resp.status_code in (302, 401, 403)
    print(f"✅ test_dashboard_requires_login: Got expected status {resp.status_code} for unauthenticated access.")

def test_dashboard_get_logged_in():
    with requests.Session() as session:
        login_resp = login(session, TEST_EMAIL, TEST_PASSWORD)
        assert login_resp.status_code == 200
        print("✅ Login OK: response of login endpoint was 200.")
        resp = session.get(f"{BASE_URL_TEST}/app/dashboard")
        assert resp.status_code == 200
        print("✅ Dashboard OK: /app/dashboard returned 200 after login.")
        assert "dashboard" in resp.text.lower()
        print("✅ Dashboard content check: 'dashboard' found in response.")

def test_dashboard_only_allows_get():
    with requests.Session() as session:
        login_resp = login(session, TEST_EMAIL, TEST_PASSWORD)
        assert login_resp.status_code == 200
        print("✅ Login OK for method checks.")
        for method in ["post", "put", "delete"]:
            req = getattr(session, method)
            resp = req(f"{BASE_URL_TEST}/app/dashboard")
            assert resp.status_code == 405
            print(f"✅ {method.upper()} not allowed on /app/dashboard (got 405).")

def test_dashboard_sets_conversation_id():
    with requests.Session() as session:
        login_resp = login(session, TEST_EMAIL, TEST_PASSWORD)
        assert login_resp.status_code == 200
        print("✅ Login OK for conversation ID check.")
        resp = session.get(f"{BASE_URL_TEST}/app/dashboard")
        html = resp.text

        pattern = re.compile(
            r'<div\b[^>]*\bclass\s*=\s*["\'][^"\']*conversation-info[^"\']*["\'][^>]*\bdata-conversation-id\s*=\s*["\'](?P<cid>[^"\']+)["\'][^>]*'
            r'|<div\b[^>]*\bdata-conversation-id\s*=\s*["\'](?P<cid2>[^"\']+)["\'][^>]*\bclass\s*=\s*["\'][^"\']*conversation-info[^"\']*["\'][^>]*',
            re.IGNORECASE,
        )
        m = pattern.search(html)
        assert m, "conversation-info div with data-conversation-id not found"
        print("✅ Found conversation-info div with data-conversation-id.")

        cid = m.group("cid") or m.group("cid2")
        assert cid, "data-conversation-id value empty"
        print(f"✅ data-conversation-id value is '{cid}'.")

        assert f"ID: {cid}" in html
        print(f"✅ ID '{cid}' found in dashboard HTML.")