from fastmcp import FastMCP
import os
import sqlite3
import json
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), "time_tracker.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("Time Focus Tracker MCP")

def init_db():
    """Initialize the SQLite database with required tables."""
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity TEXT NOT NULL,
                minutes INTEGER NOT NULL CHECK (minutes > 0),
                category_id INTEGER,
                session_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Initialize default categories if none exist
        cur = c.execute("SELECT COUNT(*) FROM categories")
        if cur.fetchone()[0] == 0:
            default_categories = [
                ("Work", "#3B82F6"),
                ("Study", "#8B5CF6"),
                ("Exercise", "#10B981"),
                ("Reading", "#F59E0B"),
                ("Creative", "#EC4899"),
                ("Social", "#06B6D4"),
                ("Other", "#6B7280")
            ]
            c.executemany(
                "INSERT INTO categories (name, color) VALUES (?, ?)",
                default_categories
            )
        c.commit()

init_db()

@mcp.tool()
def add_category(name: str, color: str = "#6B7280"):
    """Add a new activity category.
    
    Args:
        name: Category name (e.g., "Work", "Study", "Exercise")
        color: Hex color code (default: #6B7280)
    
    Returns:
        Dictionary with status and category ID
    """
    try:
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                "INSERT INTO categories (name, color) VALUES (?, ?)",
                (name, color)
            )
            return {"status": "success", "id": cur.lastrowid, "message": f"Category '{name}' added"}
    except sqlite3.IntegrityError:
        return {"status": "error", "message": f"Category '{name}' already exists"}

@mcp.tool()
def list_categories():
    """List all activity categories.
    
    Returns:
        List of category dictionaries with id, name, color, and created_at
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, name, color, created_at
            FROM categories
            ORDER BY name ASC
            """
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def add_session(activity: str, minutes: int, category: str, session_date: str = None, note: str = ""):
    """Add a new time tracking session.
    
    Args:
        activity: Description of the activity (e.g., "Math homework", "Team meeting")
        minutes: Duration in minutes (must be positive)
        category: Category name (e.g., "Work", "Study")
        session_date: Date in YYYY-MM-DD format (defaults to today)
        note: Optional note about the session
    
    Returns:
        Dictionary with status, session ID, and details
    """
    if minutes <= 0:
        return {"status": "error", "message": "Minutes must be positive"}
    
    if session_date is None:
        session_date = date.today().isoformat()
    
    try:
        with sqlite3.connect(DB_PATH) as c:
            # Get category ID
            cur = c.execute("SELECT id FROM categories WHERE name = ?", (category,))
            result = cur.fetchone()
            
            if result is None:
                return {"status": "error", "message": f"Category '{category}' not found. Use add_category() first."}
            
            category_id = result[0]
            
            # Insert session
            cur = c.execute(
                "INSERT INTO sessions (activity, minutes, category_id, session_date) VALUES (?, ?, ?, ?)",
                (activity, minutes, category_id, session_date)
            )
            session_id = cur.lastrowid
            
            # Add note if provided
            if note:
                c.execute(
                    "INSERT INTO notes (session_id, content) VALUES (?, ?)",
                    (session_id, note)
                )
            
            c.commit()
            return {
                "status": "success",
                "id": session_id,
                "activity": activity,
                "minutes": minutes,
                "hours": round(minutes / 60, 2),
                "category": category,
                "date": session_date
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def list_sessions(start_date: str, end_date: str, category: str = None):
    """List time tracking sessions within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        category: Optional category filter
    
    Returns:
        List of session dictionaries with all details
    """
    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT 
                s.id, s.activity, s.minutes, s.session_date,
                c.name as category, c.color,
                s.created_at
            FROM sessions s
            JOIN categories c ON s.category_id = c.id
            WHERE s.session_date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        
        if category:
            query += " AND c.name = ?"
            params.append(category)
        
        query += " ORDER BY s.session_date DESC, s.created_at DESC"
        
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        sessions = [dict(zip(cols, r)) for r in cur.fetchall()]
        
        # Add notes and hours to each session
        for session in sessions:
            session['hours'] = round(session['minutes'] / 60, 2)
            
            # Get notes
            note_cur = c.execute(
                "SELECT content FROM notes WHERE session_id = ?",
                (session['id'],)
            )
            notes = [row[0] for row in note_cur.fetchall()]
            session['notes'] = notes
        
        return sessions

@mcp.tool()
def update_session(session_id: int, activity: str = None, minutes: int = None, category: str = None, session_date: str = None):
    """Update an existing time tracking session.
    
    Args:
        session_id: ID of the session to update
        activity: New activity description (optional)
        minutes: New duration in minutes (optional)
        category: New category name (optional)
        session_date: New date in YYYY-MM-DD format (optional)
    
    Returns:
        Dictionary with status and updated session details
    """
    try:
        with sqlite3.connect(DB_PATH) as c:
            # Check if session exists
            cur = c.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if cur.fetchone() is None:
                return {"status": "error", "message": f"Session {session_id} not found"}
            
            updates = []
            params = []
            
            if activity is not None:
                updates.append("activity = ?")
                params.append(activity)
            
            if minutes is not None:
                if minutes <= 0:
                    return {"status": "error", "message": "Minutes must be positive"}
                updates.append("minutes = ?")
                params.append(minutes)
            
            if category is not None:
                # Get category ID
                cat_cur = c.execute("SELECT id FROM categories WHERE name = ?", (category,))
                result = cat_cur.fetchone()
                if result is None:
                    return {"status": "error", "message": f"Category '{category}' not found"}
                updates.append("category_id = ?")
                params.append(result[0])
            
            if session_date is not None:
                updates.append("session_date = ?")
                params.append(session_date)
            
            if not updates:
                return {"status": "error", "message": "No updates provided"}
            
            params.append(session_id)
            query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
            c.execute(query, params)
            c.commit()
            
            return {"status": "success", "id": session_id, "message": "Session updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def delete_session(session_id: int):
    """Delete a time tracking session.
    
    Args:
        session_id: ID of the session to delete
    
    Returns:
        Dictionary with status and message
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        if cur.rowcount == 0:
            return {"status": "error", "message": f"Session {session_id} not found"}
        c.commit()
        return {"status": "success", "message": f"Session {session_id} deleted"}

@mcp.tool()
def add_note(session_id: int, content: str):
    """Add a note to a time tracking session.
    
    Args:
        session_id: ID of the session
        content: Note content
    
    Returns:
        Dictionary with status and note ID
    """
    try:
        with sqlite3.connect(DB_PATH) as c:
            # Check if session exists
            cur = c.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if cur.fetchone() is None:
                return {"status": "error", "message": f"Session {session_id} not found"}
            
            cur = c.execute(
                "INSERT INTO notes (session_id, content) VALUES (?, ?)",
                (session_id, content)
            )
            c.commit()
            return {"status": "success", "id": cur.lastrowid, "message": "Note added"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def summarize_by_category(start_date: str, end_date: str):
    """Summarize time spent by category within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        List of category summaries with total time and session count
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT 
                c.name as category,
                c.color,
                COUNT(s.id) as session_count,
                SUM(s.minutes) as total_minutes,
                ROUND(SUM(s.minutes) / 60.0, 2) as total_hours
            FROM sessions s
            JOIN categories c ON s.category_id = c.id
            WHERE s.session_date BETWEEN ? AND ?
            GROUP BY c.id, c.name, c.color
            ORDER BY total_minutes DESC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def summarize_by_date(start_date: str, end_date: str):
    """Summarize time spent by date within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        List of daily summaries with total time and session count
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT 
                session_date as date,
                COUNT(id) as session_count,
                SUM(minutes) as total_minutes,
                ROUND(SUM(minutes) / 60.0, 2) as total_hours
            FROM sessions
            WHERE session_date BETWEEN ? AND ?
            GROUP BY session_date
            ORDER BY session_date DESC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def get_statistics(start_date: str, end_date: str):
    """Get comprehensive statistics for a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Dictionary with overall statistics
    """
    with sqlite3.connect(DB_PATH) as c:
        # Overall stats
        cur = c.execute(
            """
            SELECT 
                COUNT(id) as total_sessions,
                SUM(minutes) as total_minutes,
                ROUND(SUM(minutes) / 60.0, 2) as total_hours,
                ROUND(AVG(minutes), 2) as avg_session_minutes,
                MIN(minutes) as min_session_minutes,
                MAX(minutes) as max_session_minutes
            FROM sessions
            WHERE session_date BETWEEN ? AND ?
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        stats = dict(zip(cols, cur.fetchone()))
        
        # Most productive day
        cur = c.execute(
            """
            SELECT session_date, SUM(minutes) as total_minutes
            FROM sessions
            WHERE session_date BETWEEN ? AND ?
            GROUP BY session_date
            ORDER BY total_minutes DESC
            LIMIT 1
            """,
            (start_date, end_date)
        )
        result = cur.fetchone()
        if result:
            stats['most_productive_day'] = result[0]
            stats['most_productive_day_minutes'] = result[1]
        
        # Top category
        cur = c.execute(
            """
            SELECT c.name, SUM(s.minutes) as total_minutes
            FROM sessions s
            JOIN categories c ON s.category_id = c.id
            WHERE s.session_date BETWEEN ? AND ?
            GROUP BY c.name
            ORDER BY total_minutes DESC
            LIMIT 1
            """,
            (start_date, end_date)
        )
        result = cur.fetchone()
        if result:
            stats['top_category'] = result[0]
            stats['top_category_minutes'] = result[1]
        
        return stats

@mcp.resource("timefocus://categories", mime_type="application/json")
def categories_resource():
    """Get categories as a resource."""
    if os.path.exists(CATEGORIES_PATH):
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Return current categories from database
        categories = list_categories()
        return json.dumps(categories, indent=2)

@mcp.resource("timefocus://stats/today", mime_type="application/json")
def today_stats():
    """Get today's time tracking statistics."""
    today = date.today().isoformat()
    stats = get_statistics(today, today)
    return json.dumps(stats, indent=2)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)