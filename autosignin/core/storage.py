"""
存储适配器
抽象数据访问层，支持多种后端
"""

import sqlite3
import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from autosignin.models.signin import SignInRecord


class StorageAdapter(ABC):
    """存储适配器基类"""
    
    @abstractmethod
    async def async_save_sign_in_result(self, record: SignInRecord) -> int:
        """保存签到结果"""
        pass
    
    @abstractmethod
    async def async_get_sign_in_records(
        self,
        platform: str = None,
        account: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[SignInRecord]:
        """获取签到记录"""
        pass
    
    @abstractmethod
    async def async_is_already_signed_today(
        self,
        platform: str,
        account: str,
        check_time: datetime = None
    ) -> bool:
        """检查是否已签到"""
        pass
    
    @abstractmethod
    async def async_get_last_sign_in(
        self,
        platform: str,
        account: str
    ) -> Optional[SignInRecord]:
        """获取上次签到记录"""
        pass
    
    @abstractmethod
    async def async_get_sign_in_stats(
        self,
        platform: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取签到统计"""
        pass


class SQLiteStorageAdapter(StorageAdapter):
    """SQLite 存储实现"""
    
    def __init__(self, db_path: str = "data/signin.db"):
        self.db_path = db_path
        self._conn: sqlite3.Connection = None
        self._lock = asyncio.Lock()
        
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sign_in_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                account TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 0,
                status_code INTEGER,
                message TEXT,
                error_type TEXT,
                duration_ms INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_platform_account 
            ON sign_in_records(platform, account)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON sign_in_records(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _close_conn(self):
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _row_to_record(self, row: sqlite3.Row) -> SignInRecord:
        metadata = {}
        if row['metadata']:
            try:
                metadata = json.loads(row['metadata'])
            except:
                metadata = {}
        
        return SignInRecord(
            id=row['id'],
            request_id=row['request_id'],
            platform=row['platform'],
            account=row['account'],
            success=bool(row['success']),
            status_code=row['status_code'],
            message=row['message'] or "",
            error_type=row['error_type'],
            duration_ms=row['duration_ms'],
            retry_count=row['retry_count'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            metadata=metadata
        )
    
    async def async_save_sign_in_result(self, record: SignInRecord) -> int:
        """保存签到结果"""
        async with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            metadata_json = json.dumps(record.metadata, ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO sign_in_records 
                (request_id, platform, account, success, status_code, 
                message, error_type, duration_ms, retry_count, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.request_id,
                record.platform,
                record.account,
                int(record.success),
                record.status_code,
                record.message,
                record.error_type,
                record.duration_ms,
                record.retry_count,
                record.timestamp.isoformat() if isinstance(record.timestamp, datetime) else record.timestamp,
                metadata_json
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    async def async_get_sign_in_records(
        self,
        platform: str = None,
        account: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[SignInRecord]:
        """获取签到记录"""
        async with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            query = "SELECT * FROM sign_in_records WHERE 1=1"
            params = []
            
            if platform:
                query += " AND platform = ?"
                params.append(platform)
            
            if account:
                query += " AND account = ?"
                params.append(account)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    async def async_is_already_signed_today(
        self,
        platform: str,
        account: str,
        check_time: datetime = None
    ) -> bool:
        """检查是否已签到"""
        if check_time is None:
            check_time = datetime.now()
        
        start_of_day = check_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        async with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM sign_in_records
                WHERE platform = ? AND account = ?
                AND success = 1
                AND timestamp >= ? AND timestamp < ?
            """, (
                platform,
                account,
                start_of_day.isoformat(),
                end_of_day.isoformat()
            ))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    async def async_get_last_sign_in(
        self,
        platform: str,
        account: str
    ) -> Optional[SignInRecord]:
        """获取上次签到记录"""
        async with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sign_in_records
                WHERE platform = ? AND account = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (platform, account))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
            return None
    
    async def async_get_sign_in_stats(
        self,
        platform: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取签到统计"""
        async with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT 
                    platform,
                    account,
                    COUNT(*) as total,
                    SUM(success) as success_count,
                    AVG(duration_ms) as avg_duration,
                    MAX(timestamp) as last_sign_in
                FROM sign_in_records
                WHERE timestamp >= ?
            """
            params = [start_date.isoformat()]
            
            if platform:
                query += " AND platform = ?"
                params.append(platform)
            
            query += " GROUP BY platform, account"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            stats = []
            for row in rows:
                stats.append({
                    "platform": row['platform'],
                    "account": row['account'],
                    "total": row['total'],
                    "success_count": row['success_count'],
                    "avg_duration_ms": round(row['avg_duration'] or 0, 2),
                    "last_sign_in": row['last_sign_in']
                })
            
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "platform": platform,
                "stats": stats
            }
    
    def close(self):
        """关闭连接"""
        self._close_conn()


__all__ = ["StorageAdapter", "SQLiteStorageAdapter"]
