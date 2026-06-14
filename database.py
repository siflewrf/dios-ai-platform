import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("DIOS")

DATABASE_FILE = "decisions.db"


class DecisionDatabase:
    """SQLite database for storing and retrieving decisions."""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize database schema if not exists."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create decisions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    situation TEXT NOT NULL,
                    sop TEXT,
                    output_json TEXT NOT NULL,
                    core_problem TEXT,
                    decision TEXT,
                    confidence INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index on timestamp for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON decisions(timestamp DESC)
            ''')
            
            # Create index on confidence for analytics
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_confidence 
                ON decisions(confidence)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized: {self.db_file}")
        
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def save_decision(self, 
                     situation: str, 
                     output_json: Dict[str, Any],
                     sop: str = "") -> Optional[int]:
        """
        Save decision to database.
        
        Args:
            situation: Operational situation description
            output_json: Parsed decision JSON from ai_engine
            sop: Optional SOP/rules context
        
        Returns:
            Decision ID if successful, None if failed
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Extract fields from output_json
            core_problem = output_json.get("core_problem", "")
            decision = output_json.get("decision", "")
            confidence = output_json.get("confidence", 75)
            
            # Serialize full JSON
            output_json_str = json.dumps(output_json, indent=2)
            
            cursor.execute('''
                INSERT INTO decisions 
                (situation, sop, output_json, core_problem, decision, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (situation, sop, output_json_str, core_problem, decision, confidence))
            
            decision_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Decision saved - ID: {decision_id}, Confidence: {confidence}%")
            return decision_id
        
        except sqlite3.Error as e:
            logger.error(f"Database save error: {e}")
            return None
    
    def get_decision(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single decision by ID.
        
        Args:
            decision_id: Decision ID
        
        Returns:
            Decision dict or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, situation, sop, output_json, core_problem, 
                       decision, confidence, timestamp
                FROM decisions
                WHERE id = ?
            ''', (decision_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "situation": row["situation"],
                "sop": row["sop"],
                "output": json.loads(row["output_json"]),
                "core_problem": row["core_problem"],
                "decision": row["decision"],
                "confidence": row["confidence"],
                "timestamp": row["timestamp"]
            }
        
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Database retrieval error: {e}")
            return None
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent decisions.
        
        Args:
            limit: Number of recent decisions to retrieve (default: 10)
        
        Returns:
            List of decision dicts
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, situation, sop, output_json, core_problem, 
                       decision, confidence, timestamp
                FROM decisions
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            decisions = []
            for row in rows:
                decisions.append({
                    "id": row["id"],
                    "situation": row["situation"],
                    "sop": row["sop"],
                    "output": json.loads(row["output_json"]),
                    "core_problem": row["core_problem"],
                    "decision": row["decision"],
                    "confidence": row["confidence"],
                    "timestamp": row["timestamp"]
                })
            
            logger.info(f"Retrieved {len(decisions)} recent decisions")
            return decisions
        
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def get_decisions_by_confidence(self, min_confidence: int = 0, 
                                    max_confidence: int = 100,
                                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve decisions filtered by confidence range.
        
        Args:
            min_confidence: Minimum confidence (0-100)
            max_confidence: Maximum confidence (0-100)
            limit: Number of results
        
        Returns:
            List of decision dicts
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, situation, sop, output_json, core_problem, 
                       decision, confidence, timestamp
                FROM decisions
                WHERE confidence BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (min_confidence, max_confidence, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            decisions = []
            for row in rows:
                decisions.append({
                    "id": row["id"],
                    "situation": row["situation"],
                    "sop": row["sop"],
                    "output": json.loads(row["output_json"]),
                    "core_problem": row["core_problem"],
                    "decision": row["decision"],
                    "confidence": row["confidence"],
                    "timestamp": row["timestamp"]
                })
            
            logger.info(f"Retrieved {len(decisions)} decisions in confidence range {min_confidence}-{max_confidence}%")
            return decisions
        
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            {
                "total_decisions": int,
                "avg_confidence": float,
                "min_confidence": int,
                "max_confidence": int
            }
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Total decisions
            cursor.execute("SELECT COUNT(*) FROM decisions")
            total = cursor.fetchone()[0]
            
            # Confidence statistics
            cursor.execute('''
                SELECT AVG(confidence), MIN(confidence), MAX(confidence)
                FROM decisions
                WHERE confidence IS NOT NULL
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                "total_decisions": total,
                "avg_confidence": round(result[0], 2) if result[0] else 0,
                "min_confidence": result[1] if result[1] else 0,
                "max_confidence": result[2] if result[2] else 0
            }
        
        except sqlite3.Error as e:
            logger.error(f"Statistics query error: {e}")
            return {
                "total_decisions": 0,
                "avg_confidence": 0,
                "min_confidence": 0,
                "max_confidence": 0
            }
    
    def delete_old_decisions(self, days: int = 30) -> int:
        """
        Delete decisions older than specified days.
        
        Args:
            days: Delete decisions older than this many days
        
        Returns:
            Number of decisions deleted
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM decisions
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted {deleted_count} decisions older than {days} days")
            return deleted_count
        
        except sqlite3.Error as e:
            logger.error(f"Deletion error: {e}")
            return 0


# Global database instance
db = DecisionDatabase()
