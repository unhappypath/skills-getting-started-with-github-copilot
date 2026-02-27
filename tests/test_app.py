from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Ensure the in-memory activities dict is returned to its original state.

    The application mutates the shared ``activities`` object; tests run under AAA
    pattern rely on a fresh starting point.  This fixture makes a deep copy
    before the test and restores it after the test completes.
    """
    original = deepcopy(activities)
    yield
    # restore by clearing/updating so the object identity stays the same
    activities.clear()
    activities.update(original)


def test_root_redirect():
    # Arrange: none

    # Act
    # disable automatic following of redirects so we can inspect the status code
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Arrange: nothing additional

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "new_student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    # verify side effect
    assert email in client.get("/activities").json()[activity]["participants"]


def test_signup_nonexistent_activity():
    # Arrange
    activity = "Nonexistent"
    email = "foo@bar.com"

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_already_registered():
    # Arrange
    activity = "Chess Club"
    # use an existing participant from the initial data
    email = activities[activity]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_remove_participant_success():
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert "Removed" in response.json()["message"]
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_remove_participant_not_registered():
    # Arrange
    activity = "Chess Club"
    email = "not_in_list@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert "not registered" in response.json()["detail"]


def test_remove_activity_not_exists():
    # Arrange
    activity = "Ghost Club"
    email = "foo@bar.com"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
