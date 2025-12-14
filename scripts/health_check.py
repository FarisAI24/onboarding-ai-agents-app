#!/usr/bin/env python3
"""Health check script to validate all system components."""
import sys
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_endpoint(name, method, endpoint, headers=None, data=None, expected_status=200):
    """Check if an endpoint is working."""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=5)
        else:
            print(f"  ⚠️  {name}: Unknown method {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"  ✅ {name}: OK")
            return True
        else:
            print(f"  ❌ {name}: Status {response.status_code} (expected {expected_status})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ {name}: Connection failed")
        return False
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("Enterprise Onboarding Copilot - Health Check")
    print("=" * 60)
    
    results = []
    
    # Public endpoints
    print("\n📡 Public Endpoints:")
    results.append(check_endpoint("Health Check", "GET", "/health"))
    results.append(check_endpoint("FAQs (Public)", "GET", "/faqs"))
    results.append(check_endpoint("i18n - English", "GET", "/i18n/en"))
    results.append(check_endpoint("i18n - Arabic", "GET", "/i18n/ar"))
    
    # Login to get token
    print("\n🔐 Authentication:")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@company.com", "password": "admin123"},
            timeout=5
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print("  ✅ Login: OK")
            results.append(True)
        else:
            print(f"  ❌ Login: Status {login_response.status_code}")
            print("     Make sure admin account exists with password 'admin123'")
            results.append(False)
            token = None
    except Exception as e:
        print(f"  ❌ Login: {e}")
        results.append(False)
        token = None
    
    if not token:
        print("\n⚠️  Skipping authenticated endpoints (login failed)")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Authenticated endpoints
        print("\n🔒 Authenticated Endpoints:")
        results.append(check_endpoint("Current User", "GET", "/auth/me", headers))
        results.append(check_endpoint("Tasks", "GET", "/tasks?user_id=9", headers))
        
        # Feature endpoints
        print("\n✨ Feature Endpoints:")
        results.append(check_endpoint("Achievements", "GET", "/achievements", headers))
        results.append(check_endpoint("Achievement Points", "GET", "/achievements/points", headers))
        results.append(check_endpoint("Leaderboard", "GET", "/achievements/leaderboard", headers))
        results.append(check_endpoint("Training Modules", "GET", "/training/modules", headers))
        results.append(check_endpoint("Training Progress", "GET", "/training/progress", headers))
        results.append(check_endpoint("Training Summary", "GET", "/training/summary", headers))
        results.append(check_endpoint("Calendar Events", "GET", "/calendar/events", headers))
        results.append(check_endpoint("Calendar Week", "GET", "/calendar/week", headers))
        results.append(check_endpoint("Feedback Stats", "GET", "/feedback/stats", headers))
        
        # Admin endpoints
        print("\n👤 Admin Endpoints:")
        results.append(check_endpoint("All Users", "GET", "/admin/users", headers))
        results.append(check_endpoint("Metrics", "GET", "/admin/metrics", headers))
        results.append(check_endpoint("Churn At-Risk", "GET", "/churn/at-risk", headers))
        results.append(check_endpoint("Audit Logs", "GET", "/audit/logs?limit=5", headers))
        results.append(check_endpoint("Audit Summary", "GET", "/audit/summary", headers))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"✅ All {total} checks passed!")
    else:
        print(f"⚠️  {passed}/{total} checks passed ({total - passed} failed)")
    print("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

