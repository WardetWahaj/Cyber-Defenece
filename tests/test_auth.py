import pytest
from fastapi.testclient import TestClient
import os
import sys

# Set test environment
os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.backend.api import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_signup_success():
    response = client.post("/api/auth/signup", json={
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "organization": "Test Org"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"

def test_signup_duplicate_email():
    # First signup
    client.post("/api/auth/signup", json={
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "organization": "Test Org"
    })
    # Second signup with same email should fail
    response = client.post("/api/auth/signup", json={
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User 2",
        "organization": "Test Org"
    })
    assert response.status_code == 400

def test_login_success():
    # Create user first
    client.post("/api/auth/signup", json={
        "email": "logintest@example.com",
        "password": "TestPassword123!",
        "full_name": "Login Test",
        "organization": "Test Org"
    })
    # Login
    response = client.post("/api/auth/login", json={
        "email": "logintest@example.com",
        "password": "TestPassword123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_wrong_password():
    response = client.post("/api/auth/login", json={
        "email": "logintest@example.com",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401

def test_me_without_token():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_me_with_valid_token():
    # Create and login
    client.post("/api/auth/signup", json={
        "email": "metest@example.com",
        "password": "TestPassword123!",
        "full_name": "Me Test",
        "organization": "Test Org"
    })
    login = client.post("/api/auth/login", json={
        "email": "metest@example.com",
        "password": "TestPassword123!"
    })
    token = login.json()["access_token"]
    
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "metest@example.com"
