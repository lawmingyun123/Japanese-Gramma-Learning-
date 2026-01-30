import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.db")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        """Initialize the database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Table: Grammar Points (The Content)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grammar_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jlpt_level TEXT NOT NULL,
                grammar_concept TEXT NOT NULL,
                meaning TEXT,
                structure TEXT,
                explanation TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table: User Progress (The State)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grammar_id INTEGER NOT NULL,
                next_review_due TIMESTAMP,
                interval INTEGER DEFAULT 0,
                efactor REAL DEFAULT 2.5,
                repetition_streak INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                FOREIGN KEY (grammar_id) REFERENCES grammar_points(id)
            )
        ''')

        # Table: Logs (The History)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grammar_id INTEGER,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quality_rating INTEGER,
                review_type TEXT,
                FOREIGN KEY (grammar_id) REFERENCES grammar_points(id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_grammar_point(self, level, concept, meaning, structure, explanation, tags=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check for duplicates
        cursor.execute("SELECT id FROM grammar_points WHERE grammar_concept = ?", (concept,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return existing[0] # Return existing ID

        cursor.execute('''
            INSERT INTO grammar_points (jlpt_level, grammar_concept, meaning, structure, explanation, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (level, concept, meaning, structure, explanation, tags))
        
        grammar_id = cursor.lastrowid
        # Initialize progress for this point
        cursor.execute('''
            INSERT INTO user_progress (grammar_id, status)
            VALUES (?, 'new')
        ''', (grammar_id,))
        
        conn.commit()
        conn.close()
        return grammar_id

    def get_due_reviews(self):
        """Get items that are due for review (next_review_due < now) or new items."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Select Active Reviews
        cursor.execute('''
            SELECT g.id, g.grammar_concept, g.meaning, g.structure, g.explanation, 
                   u.id, u.interval, u.efactor, u.repetition_streak
            FROM grammar_points g
            JOIN user_progress u ON g.id = u.grammar_id
            WHERE u.status = 'active' AND u.next_review_due <= ?
            ORDER BY u.next_review_due ASC
        ''', (now,))
        due_items = cursor.fetchall()

        # Select New Items (Limit 5 per session for example, but here just fetching)
        cursor.execute('''
            SELECT g.id, g.grammar_concept, g.meaning, g.structure, g.explanation, g.jlpt_level,
                   u.id, u.interval, u.efactor, u.repetition_streak
            FROM grammar_points g
            JOIN user_progress u ON g.id = u.grammar_id
            WHERE u.status = 'new'
            LIMIT 10
        ''')
        new_items = cursor.fetchall()
        
        conn.close()
        
        # Combine/Process in higher level logic, or return separate
        return {
            "reviews": sorted(self._format_results(due_items), key=lambda x: x.get('level', 'N5'), reverse=True),
            "new": sorted(self._format_results(new_items), key=lambda x: x.get('level', 'N5'), reverse=True)
        }
    
    def update_progress(self, progress_id, grammar_id, quality, interval, efactor, repetition, next_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_progress
            SET interval = ?, efactor = ?, repetition_streak = ?, next_review_due = ?, status = 'active'
            WHERE id = ?
        ''', (interval, efactor, repetition, next_date, progress_id))
        
        cursor.execute('''
            INSERT INTO review_logs (grammar_id, quality_rating, review_type)
            VALUES (?, ?, ?)
        ''', (grammar_id, quality, 'review' if repetition > 1 else 'learn'))
        
        conn.commit()
        conn.close()

    def _format_results(self, rows):
        results = []
        for row in rows:
            results.append({
                "grammar_id": row[0],
                "grammar_concept": row[1],
                "meaning": row[2],
                "structure": row[3],
                "explanation": row[4],
                "level": row[5],
                "progress_id": row[6],
                "interval": row[6],
                "efactor": row[7],
                "repetition": row[8]
            })
        return results

    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM user_progress GROUP BY status")
        stats = dict(cursor.fetchall())
        conn.close()
        return stats

    def seed_data_check(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM grammar_points")
        count = cursor.fetchone()[0]
        conn.close()
        return count

if __name__ == "__main__":
    db = DatabaseManager()
    print("Database Initialized.")
