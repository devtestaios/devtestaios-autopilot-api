"""
Advanced database connection pooling and optimization
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import os
import time
from typing import Optional

class DatabasePool:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.setup_connection_pool()
    
    def setup_connection_pool(self):
        """Setup optimized database connection pool"""
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Connection pool settings for scale
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,          # Base connections
            max_overflow=30,       # Additional connections under load
            pool_timeout=30,       # Timeout for getting connection
            pool_recycle=3600,     # Recycle connections after 1 hour
            pool_pre_ping=True,    # Validate connections before use
            echo=False,            # Set to True for SQL debugging
            pool_reset_on_return='commit'  # Reset connection state
        )
        
        # Setup session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Setup connection event listeners
        self._setup_connection_events()
    
    def _setup_connection_events(self):
        """Setup database connection event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Called when a new DB connection is created"""
            connection_record.info['connect_time'] = time.time()
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is retrieved from the pool"""
            connection_record.info['checkout_time'] = time.time()
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Called when a connection is returned to the pool"""
            checkout_time = connection_record.info.get('checkout_time')
            if checkout_time:
                usage_time = time.time() - checkout_time
                # Log if connection was held for too long
                if usage_time > 30:  # 30 seconds threshold
                    print(f"⚠️ Long-running connection detected: {usage_time:.2f}s")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def get_pool_stats(self):
        """Get connection pool statistics"""
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
            "total_connections": pool.size() + pool.overflow(),
            "pool_status": "healthy" if pool.checkedout() < pool.size() * 0.8 else "under_pressure"
        }
    
    def optimize_queries(self, session):
        """Run database optimization queries"""
        try:
            # Analyze and optimize frequently used tables
            optimization_queries = [
                "ANALYZE users",
                "ANALYZE audit_logs", 
                "ANALYZE tenant_configs",
                "ANALYZE user_permissions"
            ]
            
            for query in optimization_queries:
                session.execute(text(query))
            
            session.commit()
            return {"status": "success", "optimized_tables": len(optimization_queries)}
            
        except Exception as e:
            session.rollback()
            return {"status": "error", "message": str(e)}

# Global database pool instance
db_pool = DatabasePool()

def get_optimized_db():
    """Get optimized database session"""
    session = db_pool.get_session()
    try:
        yield session
    finally:
        session.close()
