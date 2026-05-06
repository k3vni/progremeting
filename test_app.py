import pytest
import sqlite3
import os
import tempfile
from unittest.mock import patch, MagicMock
from app import app, init_db, get_db, hash_password


@pytest.fixture
def test_app():
    # Use temporary database file for tests
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True
    with app.app_context():
        init_db()  # Create tables
        yield app
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()


def setup_user(client, username='testuser', password='TestPass123!'):
    """Helper to register and login a user."""
    # Register
    client.post('/register', data={'username': username, 'password': password})
    # Login
    client.post('/login', data={'username': username, 'password': password})


# Authentication Tests
def test_register_success(client):
    response = client.post('/register', data={'username': 'newuser', 'password': 'NewPass123!'})
    assert response.status_code == 302  # Redirect to login
    assert b'Account created' in response.data or response.status_code == 302


def test_register_duplicate_username(client):
    client.post('/register', data={'username': 'user1', 'password': 'Pass123!@#'})
    response = client.post('/register', data={'username': 'user1', 'password': 'Pass456!@#'})
    assert b'Username already exists' in response.data


def test_register_missing_fields(client):
    response = client.post('/register', data={'username': '', 'password': 'pass'})
    assert b'Username and password are required' in response.data


def test_login_success(client):
    setup_user(client)
    response = client.post('/login', data={'username': 'testuser', 'password': 'TestPass123!'})
    assert response.status_code == 302  # Redirect to dashboard


def test_login_invalid_credentials(client):
    response = client.post('/login', data={'username': 'wrong', 'password': 'wrong'})
    assert b'Invalid username or password' in response.data


def test_logout(client):
    setup_user(client)
    response = client.get('/logout')
    assert response.status_code == 302  # Redirect to login


def test_unauthorized_access(client):
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login


# Workout Tests
def test_add_workout_success(client):
    setup_user(client)
    response = client.post('/add_workout', data={
        'exercise': 'Push-ups',
        'weight': '0',
        'reps': '10',
        'sets': '3',
        'date': '15-04-2026',
        'notes': 'Morning workout'
    }, follow_redirects=True)
    assert b'Workout added successfully' in response.data


def test_add_workout_missing_exercise(client):
    setup_user(client)
    response = client.post('/add_workout', data={
        'exercise': '',
        'date': '15-04-2026'
    }, follow_redirects=True)
    assert b'Exercise and date are required' in response.data


def test_add_workout_invalid_date(client):
    setup_user(client)
    response = client.post('/add_workout', data={
        'exercise': 'Push-ups',
        'date': 'invalid-date'
    }, follow_redirects=True)
    assert b'Workout added successfully' in response.data  # Date validation not implemented


def test_delete_workout(client):
    setup_user(client)
    # Add a workout first
    client.post('/add_workout', data={
        'exercise': 'Push-ups',
        'date': '15-04-2026'
    })
    # Get workout id (assuming first one)
    with app.app_context():
        db = get_db()
        workout = db.execute("SELECT id FROM workouts WHERE user_id = 1").fetchone()
        workout_id = workout['id']
    response = client.get(f'/delete_workout/{workout_id}', follow_redirects=True)
    assert b'Workout deleted' in response.data


def test_delete_workout_unauthorized(client):
    # Setup two users
    client.post('/register', data={'username': 'user1', 'password': 'Pass123!@#'})
    client.post('/register', data={'username': 'user2', 'password': 'Pass456!@#'})
    
    # Login as user2 and add workout
    client.post('/login', data={'username': 'user2', 'password': 'Pass456!@#'})
    client.post('/add_workout', data={
        'exercise': 'Push-ups',
        'date': '15-04-2026'
    })
    
    with app.app_context():
        db = get_db()
        workout = db.execute("SELECT id FROM workouts WHERE user_id = 2").fetchone()
        workout_id = workout['id']
    
    # Login as user1
    client.post('/login', data={'username': 'user1', 'password': 'Pass123!@#'})
    
    # Try to delete as user1 (should fail)
    response = client.get(f'/delete_workout/{workout_id}', follow_redirects=True)
    assert b'Workout not found or already deleted' in response.data


# Plan Tests
def test_add_plan_success(client):
    setup_user(client)
    response = client.post('/add_plan', data={
        'exercise': 'Bench Press',
        'weight': '50',
        'reps': '8',
        'sets': '4',
        'date': '16-04-2026',
        'notes': 'Plan for tomorrow'
    }, follow_redirects=True)
    assert b'Workout plan added successfully' in response.data


def test_complete_plan(client):
    setup_user(client)
    # Add a plan
    client.post('/add_plan', data={
        'exercise': 'Bench Press',
        'date': '16-04-2026'
    })
    with app.app_context():
        db = get_db()
        plan = db.execute("SELECT id FROM plans WHERE user_id = 1").fetchone()
        plan_id = plan['id']
    response = client.get(f'/complete_plan/{plan_id}', follow_redirects=True)
    assert b'Plan completed and saved as workout' in response.data


def test_delete_plan(client):
    setup_user(client)
    # Add a plan
    client.post('/add_plan', data={
        'exercise': 'Bench Press',
        'date': '16-04-2026'
    })
    with app.app_context():
        db = get_db()
        plan = db.execute("SELECT id FROM plans WHERE user_id = 1").fetchone()
        plan_id = plan['id']
    response = client.get(f'/delete_plan/{plan_id}', follow_redirects=True)
    assert b'Plan deleted' in response.data


# Reminder Tests
def test_add_reminder_success(client):
    setup_user(client)
    response = client.post('/add_reminder', data={
        'reminder': 'Remember to stretch',
        'date': '15-04-2026'
    }, follow_redirects=True)
    assert b'Reminder added' in response.data


def test_add_reminder_missing_fields(client):
    setup_user(client)
    response = client.post('/add_reminder', data={
        'reminder': '',
        'date': '15-04-2026'
    }, follow_redirects=True)
    assert b'Reminder text and date are required' in response.data


def test_delete_reminder(client):
    setup_user(client)
    client.post('/add_reminder', data={
        'reminder': 'Test reminder',
        'date': '15-04-2026'
    })
    with app.app_context():
        db = get_db()
        reminder = db.execute("SELECT id FROM reminders WHERE user_id = 1").fetchone()
        reminder_id = reminder['id']
    response = client.get(f'/delete_reminder/{reminder_id}', follow_redirects=True)
    assert b'Reminder deleted' in response.data


# Video Tests
def test_video_redirect(client):
    setup_user(client)
    response = client.get('/video?exercise=push-ups')
    assert response.status_code == 302  # Redirect to YouTube


# Dashboard Tests
def test_dashboard_access(client):
    setup_user(client)
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Workout Planner' in response.data


# Index Tests
def test_index_redirect_to_login(client):
    response = client.get('/')
    assert response.status_code == 302


def test_index_redirect_to_dashboard_when_logged_in(client):
    setup_user(client)
    response = client.get('/')
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']


# API Tests
def test_api_workouts(client):
    setup_user(client)
    # Add a workout
    client.post('/add_workout', data={
        'exercise': 'Push-ups',
        'date': '15-04-2026'
    })
    response = client.get('/api/workouts')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['exercise'] == 'Push-ups'


def test_api_add_workout(client):
    setup_user(client)
    response = client.post('/api/workouts', 
                          json={
                              'exercise': 'Squats',
                              'weight': 100,
                              'reps': 10,
                              'sets': 3,
                              'date': '16-04-2026',
                              'notes': 'API test'
                          })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['message'] == 'Workout added successfully'


def test_api_plans(client):
    setup_user(client)
    # Add a plan
    client.post('/add_plan', data={
        'exercise': 'Bench Press',
        'date': '17-04-2026'
    })
    response = client.get('/api/plans')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['exercise'] == 'Bench Press'


def test_api_add_plan(client):
    setup_user(client)
    response = client.post('/api/plans', 
                          json={
                              'exercise': 'Deadlift',
                              'weight': 150,
                              'reps': 5,
                              'sets': 3,
                              'date': '18-04-2026',
                              'notes': 'API test plan'
                          })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['message'] == 'Plan added successfully'


def test_api_reminders(client):
    setup_user(client)
    # Add a reminder
    client.post('/add_reminder', data={
        'reminder': 'Stretch after workout',
        'date': '19-04-2026'
    })
    response = client.get('/api/reminders')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['reminder_text'] == 'Stretch after workout'


def test_api_add_reminder(client):
    setup_user(client)
    response = client.post('/api/reminders', 
                          json={
                              'reminder_text': 'Drink water',
                              'date': '20-04-2026'
                          })
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['message'] == 'Reminder added successfully'


def test_api_unauthorized(client):
    response = client.get('/api/workouts')
    assert response.status_code == 302  # Redirect to login


# Edge Cases
def test_add_workout_invalid_weight(client):
    setup_user(client)
    response = client.post('/add_workout', data={
        'exercise': 'Push-ups',
        'weight': 'invalid',
        'date': '15-04-2026'
    }, follow_redirects=True)
    assert b'Workout added successfully' in response.data  # Should handle invalid as None


def test_add_plan_missing_date(client):
    setup_user(client)
    response = client.post('/add_plan', data={
        'exercise': 'Bench Press',
        'date': ''
    }, follow_redirects=True)
    assert b'Exercise and date are required' in response.data

        # pytest test_app.py -v