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
                grammar_id INTEGER NOT NULL,
                quality_rating INTEGER NOT NULL,
                review_type TEXT,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grammar_id) REFERENCES grammar_points(id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_grammar_point(self, level, concept, meaning, structure, explanation, tags):
        """Add a grammar point and initialize its progress."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO grammar_points (jlpt_level, grammar_concept, meaning, structure, explanation, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (level, concept, meaning, structure, explanation, json.dumps(tags)))
        
        grammar_id = cursor.lastrowid
        if grammar_id:
            cursor.execute('''
                INSERT OR IGNORE INTO user_progress (grammar_id, status)
                VALUES (?, 'new')
            ''', (grammar_id,))
        
        conn.commit()
        conn.close()
        return grammar_id

    def seed_grammar_points(self, grammar_data_list):
        """Bulk insert grammar points from JSON data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        inserted_count = 0
        for item in grammar_data_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO grammar_points (jlpt_level, grammar_concept, meaning, structure, explanation, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('jlpt_level', 'N/A'),
                    item['grammar_concept'],
                    item.get('meaning', ''),
                    item.get('structure', ''),
                    item.get('explanation', ''),
                    json.dumps(item.get('tags', []))
                ))
                
                grammar_id = cursor.lastrowid
                if grammar_id:
                    cursor.execute('''
                        INSERT OR IGNORE INTO user_progress (grammar_id, status)
                        VALUES (?, 'new')
                    ''', (grammar_id,))
                    inserted_count += 1
            except Exception as e:
                print(f"Error inserting {item.get('grammar_concept')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        return inserted_count

    def get_due_reviews(self, limit=10):
        """Get due reviews + new items, sorted by level (N5-N1)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Due reviews
        cursor.execute('''
            SELECT g.id, g.grammar_concept, g.meaning, g.structure, g.explanation, g.jlpt_level,
                   u.id as progress_id, u.interval, u.efactor, u.repetition_streak
            FROM grammar_points g
            JOIN user_progress u ON g.id = u.grammar_id
            WHERE u.status = 'active' AND date(u.next_review_due) <= date(?)
            ORDER BY g.jlpt_level DESC
            LIMIT ?
        ''', (today, limit))
        due_items = cursor.fetchall()
        
        # New items
        cursor.execute('''
            SELECT g.id, g.grammar_concept, g.meaning, g.structure, g.explanation, g.jlpt_level,
                   u.id as progress_id, u.interval, u.efactor, u.repetition_streak
            FROM grammar_points g
            JOIN user_progress u ON g.id = u.grammar_id
            WHERE u.status = 'new'
            ORDER BY g.jlpt_level DESC
            LIMIT 10
        ''')
        new_items = cursor.fetchall()
        
        conn.close()
        
        return {
            "reviews": self._format_results(due_items),
            "new": self._format_results(new_items)
        }

    def _format_results(self, rows):
        """Format database rows into dictionaries."""
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
                "interval": row[7],
                "efactor": row[8],
                "repetition": row[9]
            })
        return results

    def update_progress(self, progress_id, grammar_id, quality, interval, efactor, repetition, next_date):
        """Update user progress after review."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_progress
            SET interval = ?, efactor = ?, repetition_streak = ?, 
                next_review_due = ?, status = 'active'
            WHERE id = ?
        ''', (interval, efactor, repetition, next_date, progress_id))
        
        cursor.execute('''
            INSERT INTO review_logs (grammar_id, quality_rating, review_type)
            VALUES (?, ?, ?)
        ''', (grammar_id, quality, 'review' if repetition > 1 else 'learn'))
        
        conn.commit()
        conn.close()

    def get_stats(self):
        """Get user learning statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) FILTER (WHERE status = 'new') as new_count,
                COUNT(*) FILTER (WHERE status = 'active') as active_count,
                AVG(repetition_streak) FILTER (WHERE status = 'active') as avg_streak
            FROM user_progress
        ''')
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) as total_reviews,
                   AVG(quality_rating) as avg_quality
            FROM review_logs
            LIMIT 100
        ''')
        recent_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "new": stats[0] or 0,
            "active": stats[1] or 0,
            "avg_streak": round(stats[2] or 0, 1),
            "recent_reviews": recent_stats[0] or 0,
            "avg_quality": round(recent_stats[1] or 0, 1)
        }

    def export_progress(self):
        """Export user progress and grammar points to JSON format."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all progress with grammar details
        cursor.execute('''
            SELECT g.grammar_concept, g.jlpt_level, g.meaning, g.structure, g.explanation,
                   u.status, u.interval, u.efactor, u.repetition_streak, u.next_review_due
            FROM grammar_points g
            JOIN user_progress u ON g.id = u.grammar_id
            WHERE u.status != 'new'
        ''')
        
        progress_data = []
        for row in cursor.fetchall():
            progress_data.append({
                "grammar_concept": row[0],
                "jlpt_level": row[1],
                "meaning": row[2],
                "structure": row[3],
                "explanation": row[4],
                "status": row[5],
                "interval": row[6],
                "efactor": row[7],
                "repetition_streak": row[8],
                "next_review_due": row[9]
            })
        
        conn.close()
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_items": len(progress_data),
            "progress": progress_data
        }
        
        return export_data

    def import_progress(self, import_data):
        """Import progress data from JSON format."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        added = 0
        updated = 0
        skipped = 0
        
        for item in import_data.get('progress', []):
            try:
                # Find grammar point
                cursor.execute('SELECT id FROM grammar_points WHERE grammar_concept = ?', 
                             (item['grammar_concept'],))
                result = cursor.fetchone()
                
                if not result:
                    skipped += 1
                    continue
                
                grammar_id = result[0]
                
                # Check if progress exists
                cursor.execute('SELECT id FROM user_progress WHERE grammar_id = ?', (grammar_id,))
                progress = cursor.fetchone()
                
                if progress:
                    # Update existing
                    cursor.execute('''
                        UPDATE user_progress
                        SET status = ?, interval = ?, efactor = ?, 
                            repetition_streak = ?, next_review_due = ?
                        WHERE grammar_id = ?
                    ''', (item['status'], item['interval'], item['efactor'], 
                          item['repetition_streak'], item['next_review_due'], grammar_id))
                    updated += 1
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO user_progress (grammar_id, status, interval, efactor, 
                                                   repetition_streak, next_review_due)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (grammar_id, item['status'], item['interval'], item['efactor'],
                          item['repetition_streak'], item['next_review_due']))
                    added += 1
                    
            except Exception as e:
                print(f"Error importing {item.get('grammar_concept')}: {e}")
                skipped += 1
                continue
        
        conn.commit()
        conn.close()
        
        return {
            "added": added,
            "updated": updated,
            "skipped": skipped
        }
