#!/usr/bin/env python3
"""
Simple SQLite migration for streak columns
"""
import sqlite3
import os

def migrate():
    # SQLite database path
    db_path = os.path.join(os.path.dirname(__file__), 'student_tracker.db')

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Creating new database...")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check existing columns
    c.execute("PRAGMA table_info(students)")
    columns = [col[1] for col in c.fetchall()]
    print(f"Existing columns: {columns}")

    # Add streak columns if they don't exist
    if 'current_streak' not in columns:
        print("Adding current_streak column...")
        c.execute('ALTER TABLE students ADD COLUMN current_streak INTEGER DEFAULT 0')
        print("✅ current_streak added")
    else:
        print("ℹ️  current_streak already exists")

    if 'longest_streak' not in columns:
        print("Adding longest_streak column...")
        c.execute('ALTER TABLE students ADD COLUMN longest_streak INTEGER DEFAULT 0')
        print("✅ longest_streak added")
    else:
        print("ℹ️  longest_streak already exists")

    if 'last_study_date' not in columns:
        print("Adding last_study_date column...")
        c.execute('ALTER TABLE students ADD COLUMN last_study_date DATE')
        print("✅ last_study_date added")
    else:
        print("ℹ️  last_study_date already exists")

    conn.commit()
    conn.close()
    print("\n🎉 Migration completed!")

if __name__ == '__main__':
    migrate()
