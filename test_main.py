import pytest
from fastapi.testclient import TestClient
from routes import app

client = TestClient(app)

def test_upload_assignment():
    # Set cookies on the client itself
    client.cookies.set("user_id", "1")
    client.cookies.set("user_role", "student")

    # Simulate uploading a text file
    file_content = b"This is a sample assignment text."
    files = {"file": ("sample.txt", file_content, "text/plain")}

    # Simulate class name form field
    data = {"class_name": "EC530"}

    response = client.post("/upload", files=files, data=data)

    print(response.status_code)
    print(response.json())

    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "File received, grading in progress!"