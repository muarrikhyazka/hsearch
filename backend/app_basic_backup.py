#!/usr/bin/env python3

import os
import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🚀 Starting HS Code Search API (No AI Version)...")

# Basic imports only
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import redis
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    logger.info("✅ All dependencies imported successfully")
except ImportError as e:
    logger.error(f"❌ Import failed: {e}")
    sys.exit(1)

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://hsearch_user:hsearch_secure_2024@postgres:5432/hsearch_db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

class HSSearchEngine:
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.setup_connections()
        
    def setup_connections(self):
        """Setup database and Redis connections (fast)"""
        # Database connection
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            
        # Redis connection
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            self.redis_client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None

    def search(self, query: str, category: str = 'all', limit: int = 20):
        """Database-only search (fast)"""
        if not self.db_conn:
            return {'error': 'Database not available', 'results': []}
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            if category == 'all':
                sql = """
                SELECT hscode, description_en, category, level, section
                FROM hs_codes 
                WHERE description_en ILIKE %s OR hscode ILIKE %s
                ORDER BY 
                    CASE 
                        WHEN hscode ILIKE %s THEN 1
                        WHEN description_en ILIKE %s THEN 2
                        ELSE 3
                    END,
                    hscode
                LIMIT %s
                """
                params = [f'%{query}%', f'%{query}%', f'{query}%', f'{query}%', limit]
            else:
                sql = """
                SELECT hscode, description_en, category, level, section
                FROM hs_codes 
                WHERE (description_en ILIKE %s OR hscode ILIKE %s) AND category = %s
                ORDER BY 
                    CASE 
                        WHEN hscode ILIKE %s THEN 1
                        WHEN description_en ILIKE %s THEN 2
                        ELSE 3
                    END,
                    hscode
                LIMIT %s
                """
                params = [f'%{query}%', f'%{query}%', category, f'{query}%', f'{query}%', limit]
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            return {
                'results': [dict(row) for row in results],
                'total_count': len(results),
                'query': query,
                'category': category,
                'ai_enabled': False,
                'search_type': 'database_only'
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'error': str(e), 'results': []}

# Initialize search engine (fast startup)
search_engine = HSSearchEngine()

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0-no-ai',
        'ai_models': 'disabled',
        'search_type': 'database_only'
    }
    
    if search_engine.db_conn:
        try:
            cursor = search_engine.db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hs_codes")
            count = cursor.fetchone()[0]
            status['database'] = 'connected'
            status['hs_codes_count'] = count
        except:
            status['database'] = 'error'
    else:
        status['database'] = 'disconnected'
    
    status['redis'] = 'connected' if search_engine.redis_client else 'disconnected'
    
    return jsonify(status)

@app.route('/api/search', methods=['POST'])
def api_search():
    """Search endpoint"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        start_time = time.time()
        results = search_engine.search(
            query=query,
            category=data.get('category', 'all'),
            limit=min(data.get('limit', 20), 50)
        )
        results['execution_time'] = round(time.time() - start_time, 3)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/categories')
def api_categories():
    """Get categories"""
    categories = [
        {'key': 'all', 'name': 'Semua'},
        {'key': 'electronics', 'name': 'Elektronik'},
        {'key': 'textiles', 'name': 'Tekstil'},
        {'key': 'machinery', 'name': 'Mesin'},
        {'key': 'chemicals', 'name': 'Kimia'},
        {'key': 'food', 'name': 'Makanan'},
        {'key': 'transport', 'name': 'Transport'},
        {'key': 'animals', 'name': 'Hewan'},
        {'key': 'plants', 'name': 'Tanaman'},
        {'key': 'metals', 'name': 'Logam'},
        {'key': 'others', 'name': 'Lainnya'}
    ]
    return jsonify({'categories': categories})

@app.route('/')
def index():
    """Basic info"""
    return jsonify({
        'name': 'HS Code Search API',
        'version': '1.0.0-no-ai',
        'status': 'running',
        'ai_models': 'disabled_for_fast_startup',
        'search_type': 'database_only'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    logger.info("🌐 Flask app ready for Gunicorn")

# For Gunicorn
application = app
