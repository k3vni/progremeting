# Workout Planner API

This Flask application provides both a web interface and REST API endpoints for managing workout plans, logged workouts, and reminders.

## API Endpoints

All API endpoints require authentication. Users must be logged in to access them.

### GET /api/workouts
Returns a list of the user's logged workouts.

**Response:**
```json
[
  {
    "id": 1,
    "exercise": "Push-ups",
    "weight": 0,
    "reps": 10,
    "sets": 3,
    "date": "15-04-2026",
    "notes": "Morning workout"
  }
]
```

### POST /api/workouts
Adds a new workout.

**Request Body:**
```json
{
  "exercise": "Squats",
  "weight": 100,
  "reps": 10,
  "sets": 3,
  "date": "16-04-2026",
  "notes": "API test"
}
```

**Response:**
```json
{
  "message": "Workout added successfully",
  "id": 123
}
```

### GET /api/plans
Returns a list of the user's planned workouts.

**Response:**
```json
[
  {
    "id": 1,
    "exercise": "Bench Press",
    "target_weight": 80,
    "target_reps": 8,
    "target_sets": 4,
    "planned_date": "17-04-2026",
    "notes": "Strength training"
  }
]
```

### POST /api/plans
Adds a new workout plan.

**Request Body:**
```json
{
  "exercise": "Deadlift",
  "weight": 150,
  "reps": 5,
  "sets": 3,
  "date": "18-04-2026",
  "notes": "Heavy day"
}
```

**Response:**
```json
{
  "message": "Plan added successfully",
  "id": 124
}
```

### GET /api/reminders
Returns a list of the user's reminders.

**Response:**
```json
[
  {
    "id": 1,
    "reminder_text": "Stretch after workout",
    "date": "19-04-2026"
  }
]
```

### POST /api/reminders
Adds a new reminder.

**Request Body:**
```json
{
  "reminder_text": "Drink water",
  "date": "20-04-2026"
}
```

**Response:**
```json
{
  "message": "Reminder added successfully",
  "id": 125
}
```

## Authentication

The API uses session-based authentication. Users must log in through the web interface at `/login` before accessing API endpoints.

## Error Responses

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `201` - Created
- `302` - Redirect (unauthenticated)
- `400` - Bad Request
- `500` - Internal Server Error

Error responses include a JSON object with an "error" field describing the issue.