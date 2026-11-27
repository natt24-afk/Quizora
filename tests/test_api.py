import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


# 1. System Health & Performance Latency Header
def test_system_health_and_latency_header():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    # Verify X-Process-Time header (Req #16)
    assert "X-Process-Time" in response.headers


# 2. Authentication, Argon2 Password Hashing & JWT
def test_auth_registration_and_jwt_login():
    # Registration (Req #18: Argon2)
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_teacher_1",
            "email": "teacher1@quizora.com",
            "full_name": "Test Teacher One",
            "password": "Password123!",
            "role": "teacher",
        },
    )
    assert reg_res.status_code in [201, 409]  # 201 Created or already exists

    # OAuth2 Login 
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test_teacher_1", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "teacher"

    # Protected /me endpoint with Bearer Token 
    token = data["access_token"]
    me_res = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "test_teacher_1"


# 3. Cookie Creation & Session Management in MariaDB
def test_cookie_and_session_management():
    # Login sets cookie 
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test_teacher_1", "password": "Password123!"},
    )
    assert "quizora_session" in login_res.cookies

    # Read session from Cookie 
    session_res = client.get("/api/v1/auth/session-info")
    assert session_res.status_code == 200
    session_data = session_res.json()
    assert session_data is not None
    assert "session_token" in session_data


# 4. API Key Protected Operation
def test_api_key_protection():
    # Without API Key -> 403 Forbidden
    res_no_key = client.get("/api/v1/auth/system-status")
    assert res_no_key.status_code == 403

    # With Valid API Key 
    res_valid_key = client.get(
        "/api/v1/auth/system-status", headers={"X-API-Key": settings.API_KEY}
    )
    assert res_valid_key.status_code == 200
    assert res_valid_key.json()["message"] == "System operational"


# 5. Role-Based Access Control (RBAC)
def test_role_based_access_control():
    # Register student
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_student_1",
            "email": "student1@quizora.com",
            "full_name": "Test Student One",
            "password": "Password123!",
            "role": "student",
        },
    )

    # Login as student
    s_login = client.post(
        "/api/v1/auth/login",
        data={"username": "test_student_1", "password": "Password123!"},
    )
    student_token = s_login.json()["access_token"]

    # Student attempting to create a quiz must be blocked with 403 
    block_res = client.post(
        "/api/v1/quizzes/",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Illegal Student Quiz", "category_id": 1},
    )
    assert block_res.status_code == 403


# 6. Category CRUD & Pagination
def test_category_crud_and_pagination():
    # Create (Req #5, #7, #15)
    create_res = client.post(
        "/api/v1/categories/",
        json={"name": "Automated Testing Cat", "description": "Automated Tests"},
    )
    assert create_res.status_code in [201, 409]
    cat_id = create_res.json().get("id")

    # List with pagination 
    list_res = client.get("/api/v1/categories/?page=1&size=10")
    assert list_res.status_code == 200
    assert "items" in list_res.json()
    assert "total" in list_res.json()

    # Get by ID
    if cat_id:
        get_res = client.get(f"/api/v1/categories/{cat_id}")
        assert get_res.status_code == 200


# 7. Quiz Taking & Automatic Grading Engine (End-to-End)
def test_quiz_participation_and_auto_grading():
    # 1. Login Teacher to create Quiz
    t_login = client.post(
        "/api/v1/auth/login",
        data={"username": "test_teacher_1", "password": "Password123!"},
    )
    t_token = t_login.json()["access_token"]

    # Ensure Category exists
    cat_res = client.post(
        "/api/v1/categories/",
        json={"name": "Science Exam", "description": "Physics and Chemistry"},
    )
    cat_id = cat_res.json().get("id") or 1

    # Create published Quiz with 50% passing score
    quiz_res = client.post(
        "/api/v1/quizzes/",
        headers={"Authorization": f"Bearer {t_token}"},
        json={
            "title": "Automated Chemistry Quiz",
            "description": "Auto grading test",
            "category_id": cat_id,
            "time_limit_minutes": 20,
            "passing_score": 50.0,
            "is_published": True,
        },
    )
    assert quiz_res.status_code == 201
    quiz_id = quiz_res.json()["id"]

    # 2. Add Question with Choices 
    q_res = client.post(
        "/api/v1/questions/",
        headers={"Authorization": f"Bearer {t_token}"},
        json={
            "quiz_id": quiz_id,
            "question_text": "What is the chemical symbol for Gold?",
            "points": 5.0,
            "order_num": 1,
            "choices": [
                {"choice_text": "Ag", "is_correct": False},
                {"choice_text": "Au", "is_correct": True},
                {"choice_text": "Fe", "is_correct": False},
            ],
        },
    )
    assert q_res.status_code == 201
    q_data = q_res.json()
    correct_choice_id = [c["id"] for c in q_data["choices"] if c["choice_text"] == "Au"][0]

    # 3. Student Starts Attempt (Security Check: No answer leaks!)
    student_res = client.get("/api/v1/users/?page=1&size=1&role=student").json()
    student_id = student_res["items"][0]["id"]

    start_res = client.post(
        "/api/v1/attempts/start",
        json={"quiz_id": quiz_id, "user_id": student_id},
    )
    assert start_res.status_code == 201
    start_data = start_res.json()
    attempt_id = start_data["attempt_id"]

    # VERIFY ZERO LEAKAGE: choices must NOT contain 'is_correct'
    first_choice = start_data["questions"][0]["choices"][0]
    assert "is_correct" not in first_choice

    # 4. Student Submits Correct Answer
    submit_res = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={
            "answers": [
                {"question_id": q_data["id"], "chosen_choice_id": correct_choice_id}
            ]
        },
    )
    assert submit_res.status_code == 200
    result = submit_res.json()
    assert result["score"] == 5.0
    assert result["max_possible_score"] == 5.0
    assert result["percentage"] == 100.0
    assert result["is_passed"] is True
    assert result["status"] == "completed"

    # 5. Clean up created quiz
    client.delete(
        f"/api/v1/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )