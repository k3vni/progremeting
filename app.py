import os
import sqlite3
import hashlib
import logging
from flask import Flask, g, render_template_string, request, redirect, url_for, session, flash, current_app, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-key"
app.config['DATABASE'] = os.path.join(BASE_DIR, "workout.db")

def get_database_path():
    """Get the database file path from app config."""
    return current_app.config['DATABASE']

LOGIN_TEMPLATE = """
<!doctype html>
<title>Login</title>
<style>
 body {font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 24px;}
 .card {padding: 24px; border: 1px solid #ddd; border-radius: 12px; box-shadow: 0 0 16px rgba(0,0,0,0.05);}
 input, button {width:100%; padding:10px; margin:8px 0; border-radius:6px; border:1px solid #ccc;}
 button {background:#2c7be5; color:white; border:none; cursor:pointer;}
 button:hover {background:#1a5cc3;}
 .link {font-size:0.94rem;}
 .message {color:#d8000c;}
</style>
<div class="card">
  <h1>Login</h1>
  {% if message %}<p class="message">{{ message }}</p>{% endif %}
  <form method="post">
    <input name="username" placeholder="Username" autofocus required>
    <input name="password" placeholder="Password" type="password" required>
    <button type="submit">Login</button>
  </form>
  <p class="link">Don't have an account? <a href="{{ url_for('register') }}">Register</a></p>
</div>
"""

REGISTER_TEMPLATE = """
<!doctype html>
<title>Register</title>
<style>
 body {font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 24px;}
 .card {padding: 24px; border: 1px solid #ddd; border-radius: 12px; box-shadow: 0 0 16px rgba(0,0,0,0.05);}
 input, button {width:100%; padding:10px; margin:8px 0; border-radius:6px; border:1px solid #ccc;}
 button {background:#2c7be5; color:white; border:none; cursor:pointer;}
 button:hover {background:#1a5cc3;}
 .link {font-size:0.94rem;}
 .message {color:#d8000c;}
 .requirements {font-size: 0.9rem; color: #666; margin-top: 10px;}
 .requirements ul {margin: 5px 0; padding-left: 20px;}
 .requirements li {margin: 2px 0;}
</style>
<div class="card">
  <h1>Register</h1>
  {% if message %}<p class="message">{{ message }}</p>{% endif %}
  <form method="post">
    <input name="username" placeholder="Username" autofocus required>
    <input name="password" placeholder="Password" type="password" required>
    <button type="submit">Create account</button>
  </form>
  <div class="requirements">
    <strong>Password requirements:</strong>
    <ul>
      <li>At least 8 characters long</li>
      <li>At least one uppercase letter (A-Z)</li>
      <li>At least one lowercase letter (a-z)</li>
      <li>At least one number (0-9)</li>
      <li>At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?/~`)</li>
    </ul>
  </div>
  <p class="link">Already registered? <a href="{{ url_for('login') }}">Login</a></p>
</div>
"""

DASHBOARD_TEMPLATE = """
<!doctype html>
<title>Workout Planner</title>
<style>
 body {font-family: Arial, sans-serif; margin: 0; padding: 0; background:#0d1b2a; color: #e2e8f0;}
 header {background: #1e40af; color: white; padding: 20px;}
 main {max-width: 1200px; margin: 0 auto; padding: 24px;}
 .topbar {display:flex; justify-content:space-between; gap:12px; align-items:center; flex-wrap:wrap;}
 .card {background:#1f2937; color: #e2e8f0; padding:22px; border-radius:14px; box-shadow:0 8px 24px rgba(0,0,0,0.3); margin-bottom:24px;}
 .grid {display:grid; gap:18px;}
 .form-grid {display:grid; grid-template-columns:1fr 1fr; gap:16px;}
 input, textarea, select, button {width:100%; padding:10px; border:1px solid #374151; border-radius:10px; font-size:1rem; background:#374151; color:#e2e8f0;}
 input::placeholder, textarea::placeholder {color:#9ca3af;}
 button {background:#3b82f6; color:white; border:none; cursor:pointer;}
 button:hover {background:#2563eb;}
 table {width:100%; border-collapse:collapse; margin-top:16px;}
 th, td {text-align:left; padding:10px; border-bottom:1px solid #374151;}
 th {background:#1f2937;}
 a {color:#3b82f6; text-decoration:none;}
 a:hover {text-decoration:underline;}
 .message {color:#ef4444; margin-bottom:16px;}
 .button-small {display:inline-block; padding:6px 12px; border-radius:8px; background:#3b82f6; color:white; text-decoration:none;}
 .button-small:hover {background:#2563eb;}
 .logout {background:#dc2626;}
 .logout:hover {background:#b91c1c;}
 .delete {background:#dc2626;}
 .delete:hover {background:#b91c1c;}
</style>
<header>
  <div class="topbar">
    <div>
      <h1>Workout Planner</h1>
      <p>Logged in as {{ username }}</p>
    </div>
    <a class="button-small logout" href="{{ url_for('logout') }}">Logout</a>
  </div>
</header>
<main>
  {% if message %}<p class="message">{{ message }}</p>{% endif %}
  <div class="card">
    <h2>Add Workout</h2>
    <form method="post" action="{{ url_for('add_workout') }}">
      <div class="form-grid">
        <input id="exercise" name="exercise" placeholder="Exercise name" required>
        <input name="weight" placeholder="Weight (kg)">
        <input name="reps" placeholder="Reps">
        <input name="sets" placeholder="Sets">
        <input name="date" placeholder="Date DD-MM-YYYY" value="{{ today }}" required>
        <input name="notes" placeholder="Notes">
      </div>
      <button type="submit">Save workout</button>
      <button type="button" onclick="previewVideo()">Preview Video</button>
    </form>
  </div>

  <div class="card">
    <h2>Add Plan</h2>
    <form method="post" action="{{ url_for('add_plan') }}">
      <div class="form-grid">
        <input name="exercise" placeholder="Planned exercise" required>
        <input name="weight" placeholder="Target weight (kg)">
        <input name="reps" placeholder="Target reps">
        <input name="sets" placeholder="Target sets">
        <input name="date" placeholder="Planned date DD-MM-YYYY" value="{{ today }}" required>
        <input name="notes" placeholder="Notes">
      </div>
      <button type="submit">Save plan</button>
    </form>
  </div>

  <div class="card">
    <h2>Planned Workouts</h2>
    {% if plans %}
      <table>
        <thead><tr><th>Exercise</th><th>Target</th><th>Date</th><th>Notes</th><th>Actions</th></tr></thead>
        <tbody>
          {% for plan in plans %}
            <tr>
              <td>{{ plan.exercise }}</td>
              <td>{{ plan.target_weight or '-' }} kg / {{ plan.target_reps or '-' }} reps / {{ plan.target_sets or '-' }} sets</td>
              <td>{{ plan.planned_date }}</td>
              <td>{{ plan.notes or '' }}</td>
              <td>
                <a class="button-small" href="{{ url_for('complete_plan', plan_id=plan.id) }}">Complete</a>
                <a class="button-small delete" href="{{ url_for('delete_plan', plan_id=plan.id) }}">Delete</a>
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No planned workouts yet.</p>
    {% endif %}
  </div>

  <div class="card">
    <h2>Workout History</h2>
    {% if workouts %}
      <table>
        <thead><tr><th>Exercise</th><th>Result</th><th>Date</th><th>Notes</th><th>Delete</th></tr></thead>
        <tbody>
          {% for workout in workouts %}
            <tr>
              <td>{{ workout.exercise }}</td>
              <td>{{ workout.weight or '-' }} kg / {{ workout.reps or '-' }} reps / {{ workout.sets or '-' }} sets</td>
              <td>{{ workout.date }}</td>
              <td>{{ workout.notes or '' }}</td>
              <td><a class="button-small delete" href="{{ url_for('delete_workout', workout_id=workout.id) }}">Delete</a></td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No workouts logged yet.</p>
    {% endif %}
  </div>

  <div class="card">
    <h2>Reminders</h2>
    <form method="post" action="{{ url_for('add_reminder') }}">
      <div class="form-grid">
        <input name="reminder" placeholder="Reminder text" required>
        <input name="date" placeholder="Date DD-MM-YYYY" value="{{ today }}" required>
      </div>
      <button type="submit">Add Reminder</button>
    </form>
    {% if reminders %}
      <table>
        <thead><tr><th>Reminder</th><th>Date</th><th>Delete</th></tr></thead>
        <tbody>
          {% for reminder in reminders %}
            <tr>
              <td>{{ reminder.reminder_text }}</td>
              <td>{{ reminder.date }}</td>
              <td><a class="button-small delete" href="{{ url_for('delete_reminder', reminder_id=reminder.id) }}">Delete</a></td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No reminders yet.</p>
    {% endif %}
  </div>
</main>
<script>
function previewVideo() {
  const exercise = document.getElementById('exercise').value.trim();
  if (exercise) {
    window.open('/video?exercise=' + encodeURIComponent(exercise), '_blank');
  } else {
    alert('Please enter an exercise name first.');
  }
}
</script>
</body>
</html>
"""




def get_db():
    """Get database connection, creating it if it doesn't exist."""
    db = getattr(g, '_database', None)
    if db is None:
        db_path = get_database_path()
        logger.info(f"Connecting to database: {db_path}")
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        # Enable foreign key constraints
        db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    """Initialize database and create tables if they don't exist."""
    db_path = get_database_path()
    logger.info(f"Initializing database at: {db_path}")

    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create workouts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    weight REAL,
                    reps INTEGER,
                    sets INTEGER,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    target_weight REAL,
                    target_reps INTEGER,
                    target_sets INTEGER,
                    planned_date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create reminders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reminder_text TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
            logger.info("Database tables created successfully")

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise


@app.teardown_appcontext
def close_connection(exception):
    """Close database connection at the end of each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        logger.debug("Closing database connection")
        db.close()
        g._database = None


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    row = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    return row


def login_required(view):
    def wrapped_view(**kwargs):
        if current_user() is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view


@app.route('/')
def index():
    if current_user():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_hash = hash_password(password)
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, password_hash)).fetchone()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        message = 'Invalid username or password.'
    return render_template_string(LOGIN_TEMPLATE, message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            message = 'Username and password are required.'
        else:
            # Password strength validation
            if len(password) < 8:
                message = 'Password must be at least 8 characters long.'
            elif not any(c.isupper() for c in password):
                message = 'Password must contain at least one uppercase letter.'
            elif not any(c.islower() for c in password):
                message = 'Password must contain at least one lowercase letter.'
            elif not any(c.isdigit() for c in password):
                message = 'Password must contain at least one number.'
            elif not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in password):
                message = 'Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?/~`).'
            else:
                try:
                    db = get_db()
                    db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, hash_password(password)),
                    )
                    db.commit()
                    logger.info(f"User registered successfully: {username}")
                    flash('Account created. Please login.')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    message = 'Username already exists.'
                except sqlite3.Error as e:
                    logger.error(f"Error registering user {username}: {e}")
                    message = 'Error creating account. Please try again.'
                    db.rollback()

    return render_template_string(REGISTER_TEMPLATE, message=message)

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    today = request.args.get('today') or ''

    try:
        db = get_db()
        workouts = db.execute(
            "SELECT * FROM workouts WHERE user_id = ? ORDER BY date DESC",
            (user['id'],),
        ).fetchall()
        plans = db.execute(
            "SELECT * FROM plans WHERE user_id = ? ORDER BY planned_date DESC",
            (user['id'],),
        ).fetchall()
        reminders = db.execute(
            "SELECT * FROM reminders WHERE user_id = ? ORDER BY date DESC",
            (user['id'],),
        ).fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error retrieving data for user {user['id']}: {e}")
        workouts = []
        plans = []
        reminders = []
        session['message'] = 'Error loading data. Please refresh the page.'

    message = session.pop('message', None)
    if not today:
        from datetime import datetime
        today = datetime.now().strftime('%d-%m-%Y')

    return render_template_string(
        DASHBOARD_TEMPLATE,
        username=user['username'],
        workouts=workouts,
        plans=plans,
        reminders=reminders,
        today=today,
        message=message,
    )


@app.route('/add_workout', methods=['POST'])
@login_required
def add_workout():
    user = current_user()
    form = request.form
    exercise = form.get('exercise', '').strip()
    date = form.get('date', '').strip()
    try:
        weight = float(form.get('weight', '')) if form.get('weight', '').strip() else None
    except ValueError:
        weight = None
    try:
        reps = int(form.get('reps', '')) if form.get('reps', '').strip() else None
    except ValueError:
        reps = None
    try:
        sets = int(form.get('sets', '')) if form.get('sets', '').strip() else None
    except ValueError:
        sets = None
    notes = form.get('notes', '').strip() or None

    if not exercise or not date:
        session['message'] = 'Exercise and date are required.'
        return redirect(url_for('dashboard'))

    try:
        db = get_db()
        db.execute(
            "INSERT INTO workouts (user_id, exercise, weight, reps, sets, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user['id'], exercise, weight, reps, sets, date, notes),
        )
        db.commit()
        logger.info(f"Workout added successfully for user {user['id']}: {exercise}")
        session['message'] = 'Workout added successfully.'
    except sqlite3.Error as e:
        logger.error(f"Error adding workout for user {user['id']}: {e}")
        session['message'] = 'Error saving workout. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/add_plan', methods=['POST'])
@login_required
def add_plan():
    user = current_user()
    form = request.form
    exercise = form.get('exercise', '').strip()
    date = form.get('date', '').strip()
    try:
        weight = float(form.get('weight', '')) if form.get('weight', '').strip() else None
    except ValueError:
        weight = None
    try:
        reps = int(form.get('reps', '')) if form.get('reps', '').strip() else None
    except ValueError:
        reps = None
    try:
        sets = int(form.get('sets', '')) if form.get('sets', '').strip() else None
    except ValueError:
        sets = None
    notes = form.get('notes', '').strip() or None

    if not exercise or not date:
        session['message'] = 'Exercise and date are required.'
        return redirect(url_for('dashboard'))

    try:
        db = get_db()
        db.execute(
            "INSERT INTO plans (user_id, exercise, target_weight, target_reps, target_sets, planned_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user['id'], exercise, weight, reps, sets, date, notes),
        )
        db.commit()
        logger.info(f"Plan added successfully for user {user['id']}: {exercise}")
        session['message'] = 'Workout plan added successfully.'
    except sqlite3.Error as e:
        logger.error(f"Error adding plan for user {user['id']}: {e}")
        session['message'] = 'Error saving plan. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/delete_workout/<int:workout_id>')
@login_required
def delete_workout(workout_id):
    user = current_user()
    try:
        db = get_db()
        result = db.execute(
            "DELETE FROM workouts WHERE id = ? AND user_id = ?",
            (workout_id, user['id']),
        )
        db.commit()
        if result.rowcount > 0:
            logger.info(f"Workout {workout_id} deleted successfully for user {user['id']}")
            session['message'] = 'Workout deleted.'
        else:
            session['message'] = 'Workout not found or already deleted.'
    except sqlite3.Error as e:
        logger.error(f"Error deleting workout {workout_id} for user {user['id']}: {e}")
        session['message'] = 'Error deleting workout. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/delete_plan/<int:plan_id>')
@login_required
def delete_plan(plan_id):
    user = current_user()
    try:
        db = get_db()
        result = db.execute(
            "DELETE FROM plans WHERE id = ? AND user_id = ?",
            (plan_id, user['id']),
        )
        db.commit()
        if result.rowcount > 0:
            logger.info(f"Plan {plan_id} deleted successfully for user {user['id']}")
            session['message'] = 'Plan deleted.'
        else:
            session['message'] = 'Plan not found or already deleted.'
    except sqlite3.Error as e:
        logger.error(f"Error deleting plan {plan_id} for user {user['id']}: {e}")
        session['message'] = 'Error deleting plan. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/complete_plan/<int:plan_id>')
@login_required
def complete_plan(plan_id):
    user = current_user()
    try:
        db = get_db()
        plan = db.execute(
            "SELECT exercise, target_weight, target_reps, target_sets, planned_date, notes FROM plans WHERE id = ? AND user_id = ?",
            (plan_id, user['id']),
        ).fetchone()

        if plan:
            db.execute(
                "INSERT INTO workouts (user_id, exercise, weight, reps, sets, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user['id'], plan['exercise'], plan['target_weight'], plan['target_reps'], plan['target_sets'], plan['planned_date'], plan['notes']),
            )
            db.execute("DELETE FROM plans WHERE id = ? AND user_id = ?", (plan_id, user['id']))
            db.commit()
            logger.info(f"Plan {plan_id} completed successfully for user {user['id']}")
            session['message'] = 'Plan completed and saved as workout.'
        else:
            session['message'] = 'Plan not found.'
    except sqlite3.Error as e:
        logger.error(f"Error completing plan {plan_id} for user {user['id']}: {e}")
        session['message'] = 'Error completing plan. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/add_reminder', methods=['POST'])
@login_required
def add_reminder():
    user = current_user()
    text = request.form.get('reminder', '').strip()
    date = request.form.get('date', '').strip()

    if not text or not date:
        session['message'] = 'Reminder text and date are required.'
        return redirect(url_for('dashboard'))

    try:
        db = get_db()
        db.execute(
            "INSERT INTO reminders (user_id, reminder_text, date) VALUES (?, ?, ?)",
            (user['id'], text, date),
        )
        db.commit()
        logger.info(f"Reminder added successfully for user {user['id']}: {text}")
        session['message'] = 'Reminder added.'
    except sqlite3.Error as e:
        logger.error(f"Error adding reminder for user {user['id']}: {e}")
        session['message'] = 'Error saving reminder. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/delete_reminder/<int:reminder_id>')
@login_required
def delete_reminder(reminder_id):
    user = current_user()
    try:
        db = get_db()
        result = db.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ?",
            (reminder_id, user['id']),
        )
        db.commit()
        if result.rowcount > 0:
            logger.info(f"Reminder {reminder_id} deleted successfully for user {user['id']}")
            session['message'] = 'Reminder deleted.'
        else:
            session['message'] = 'Reminder not found or already deleted.'
    except sqlite3.Error as e:
        logger.error(f"Error deleting reminder {reminder_id} for user {user['id']}: {e}")
        session['message'] = 'Error deleting reminder. Please try again.'
        db.rollback()

    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# API Routes
@app.route('/api/workouts')
@login_required
def api_workouts():
    user = current_user()
    try:
        db = get_db()
        workouts = db.execute(
            "SELECT id, exercise, weight, reps, sets, date, notes FROM workouts WHERE user_id = ? ORDER BY date DESC",
            (user['id'],),
        ).fetchall()
        return jsonify([dict(workout) for workout in workouts])
    except sqlite3.Error as e:
        logger.error(f"Error retrieving workouts for user {user['id']}: {e}")
        return jsonify({'error': 'Error retrieving workouts'}), 500


@app.route('/api/plans')
@login_required
def api_plans():
    user = current_user()
    try:
        db = get_db()
        plans = db.execute(
            "SELECT id, exercise, target_weight, target_reps, target_sets, planned_date, notes FROM plans WHERE user_id = ? ORDER BY planned_date DESC",
            (user['id'],),
        ).fetchall()
        return jsonify([dict(plan) for plan in plans])
    except sqlite3.Error as e:
        logger.error(f"Error retrieving plans for user {user['id']}: {e}")
        return jsonify({'error': 'Error retrieving plans'}), 500


@app.route('/api/reminders')
@login_required
def api_reminders():
    user = current_user()
    try:
        db = get_db()
        reminders = db.execute(
            "SELECT id, reminder_text, date FROM reminders WHERE user_id = ? ORDER BY date DESC",
            (user['id'],),
        ).fetchall()
        return jsonify([dict(reminder) for reminder in reminders])
    except sqlite3.Error as e:
        logger.error(f"Error retrieving reminders for user {user['id']}: {e}")
        return jsonify({'error': 'Error retrieving reminders'}), 500


@app.route('/api/workouts', methods=['POST'])
@login_required
def api_add_workout():
    user = current_user()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    exercise = data.get('exercise', '').strip()
    date = data.get('date', '').strip()
    weight = data.get('weight')
    reps = data.get('reps')
    sets = data.get('sets')
    notes = data.get('notes', '').strip() or None

    if not exercise or not date:
        return jsonify({'error': 'Exercise and date are required'}), 400

    try:
        db = get_db()
        db.execute(
            "INSERT INTO workouts (user_id, exercise, weight, reps, sets, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user['id'], exercise, weight, reps, sets, date, notes),
        )
        db.commit()
        workout_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        logger.info(f"Workout added via API for user {user['id']}: {exercise}")
        return jsonify({'message': 'Workout added successfully', 'id': workout_id}), 201
    except sqlite3.Error as e:
        logger.error(f"Error adding workout via API for user {user['id']}: {e}")
        db.rollback()
        return jsonify({'error': 'Error saving workout'}), 500


@app.route('/api/plans', methods=['POST'])
@login_required
def api_add_plan():
    user = current_user()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    exercise = data.get('exercise', '').strip()
    date = data.get('date', '').strip()
    weight = data.get('weight')
    reps = data.get('reps')
    sets = data.get('sets')
    notes = data.get('notes', '').strip() or None

    if not exercise or not date:
        return jsonify({'error': 'Exercise and date are required'}), 400

    try:
        db = get_db()
        db.execute(
            "INSERT INTO plans (user_id, exercise, target_weight, target_reps, target_sets, planned_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user['id'], exercise, weight, reps, sets, date, notes),
        )
        db.commit()
        plan_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        logger.info(f"Plan added via API for user {user['id']}: {exercise}")
        return jsonify({'message': 'Plan added successfully', 'id': plan_id}), 201
    except sqlite3.Error as e:
        logger.error(f"Error adding plan via API for user {user['id']}: {e}")
        db.rollback()
        return jsonify({'error': 'Error saving plan'}), 500


@app.route('/api/reminders', methods=['POST'])
@login_required
def api_add_reminder():
    user = current_user()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    text = data.get('reminder_text', '').strip()
    date = data.get('date', '').strip()

    if not text or not date:
        return jsonify({'error': 'Reminder text and date are required'}), 400

    try:
        db = get_db()
        db.execute(
            "INSERT INTO reminders (user_id, reminder_text, date) VALUES (?, ?, ?)",
            (user['id'], text, date),
        )
        db.commit()
        reminder_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        logger.info(f"Reminder added via API for user {user['id']}: {text}")
        return jsonify({'message': 'Reminder added successfully', 'id': reminder_id}), 201
    except sqlite3.Error as e:
        logger.error(f"Error adding reminder via API for user {user['id']}: {e}")
        db.rollback()
        return jsonify({'error': 'Error saving reminder'}), 500


@app.route('/video')
@login_required
def video():
    exercise = request.args.get('exercise', '').strip()
    if exercise:
        # Redirect to YouTube search for the exercise
        from urllib.parse import quote
        youtube_url = f"https://www.youtube.com/results?search_query={quote(exercise + ' exercise tutorial')}"
        return redirect(youtube_url)
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    logger.info("Starting Workout Planner application")

    # Ensure database is initialized before starting the app
    with app.app_context():
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    logger.info("Starting Flask development server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
