import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

initial_activities = copy.deepcopy(activities)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))
    yield


def activity_url(activity_name: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}"


def participant_url(activity_name: str, email: str) -> str:
    return f"{activity_url(activity_name)}/participants/{quote(email, safe='')}"


def test_get_activities_returns_all_activities():
    # Arrange
    expected_names = set(initial_activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json().keys()) == expected_names
    assert response.json()["Chess Club"]["participants"] == initial_activities["Chess Club"]["participants"]


def test_signup_adds_participant_and_returns_message():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"{activity_url(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"{activity_url(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities[activity_name]["participants"].count(email) == 1


def test_remove_participant_deletes_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(participant_url(activity_name, email))

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "unknown@mergington.edu"

    # Act
    response = client.delete(participant_url(activity_name, email))

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"