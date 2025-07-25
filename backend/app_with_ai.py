#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🧠 Starting HS Code Search API with AI Features...")

# Import dependencies with error handling
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import redis
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    logger.info("✅ Basic dependencies imported")
except ImportError as e:
    logger.error(f"❌ Basic import failed: {e}")
    sys.exit(1)

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    logger.info("✅ AI/ML dependencies imported")
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ AI dependencies not available: {e}")
    AI_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz
    from Levenshtein import distance as levenshtein_distance
    logger.info("✅ Fuzzy matching available")
    FUZZY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Fuzzy matching not available: {e}")
    FUZZY_AVAILABLE = False

try:
    import nltk
    # Download required NLTK data if available
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        NLTK_AVAILABLE = True
        logger.info("✅ NLTK available")
    except:
        NLTK_AVAILABLE = False
        logger.warning("⚠️ NLTK data not available")
except ImportError:
    NLTK_AVAILABLE = False

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://hsearch_user:hsearch_secure_2024@postgres:5432/hsearch_db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

class SmartHSSearchEngine:
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.tfidf_vectorizer = None
        self.hs_codes_cache = []
        self.suggestions_cache = defaultdict(list)
        
        # AI settings
        self.fuzzy_threshold = 75  # Minimum fuzzy match score
        self.similarity_threshold = 0.3  # Minimum cosine similarity
        
        # Enhanced synonym dictionary
        self.synonym_dict = self._load_comprehensive_synonyms()
        
        self.setup_connections()
        self.initialize_ai_components()
        
    def _load_comprehensive_synonyms(self) -> Dict[str, List[str]]:
        """Load comprehensive synonym dictionary for semantic search"""
        return {
            # Technology & Electronics
            "computer": ["komputer", "pc", "laptop", "notebook", "desktop", "workstation"],
            "laptop": ["notebook", "portable computer", "komputer portabel"],
            "phone": ["telephone", "telepon", "handphone", "hp", "smartphone", "mobile"],
            "smartphone": ["hp", "handphone", "telepon pintar", "mobile phone"],
            "printer": ["mesin cetak", "pencetak", "printing machine"],
            "monitor": ["layar", "display", "screen", "tampilan"],
            
            # Textiles & Clothing
            "textile": ["tekstil", "kain", "fabric", "cloth"],
            "clothing": ["pakaian", "garment", "apparel", "busana"],
            "shirt": ["kemeja", "baju", "kaos", "blouse"],
            "pants": ["celana", "trousers", "slacks"],
            "shoes": ["sepatu", "footwear", "alas kaki"],
            
            # Food & Agriculture
            "rice": ["beras", "padi", "gabah", "nasi"],
            "coffee": ["kopi", "beans", "biji kopi"],
            "sugar": ["gula", "sweetener", "pemanis"],
            "meat": ["daging", "flesh", "protein hewani"],
            "fish": ["ikan", "seafood", "hasil laut"],
            
            # Animals & Live Products
            "horse": ["kuda", "equine"],
            "cattle": ["sapi", "ternak", "livestock"],
            "pig": ["babi", "swine", "pork"],
            "chicken": ["ayam", "poultry", "unggas"],
            
            # Machinery & Industrial
            "machine": ["mesin", "machinery", "peralatan"],
            "engine": ["motor", "mesin penggerak"],
            "pump": ["pompa", "pemompa"],
            "tool": ["alat", "perkakas", "equipment"],
            
            # Chemicals & Materials
            "chemical": ["kimia", "bahan kimia", "zat kimia"],
            "plastic": ["plastik", "polymer", "polimer"],
            "metal": ["logam", "metallic", "besi"],
            "steel": ["baja", "iron", "besi"],
            
            # Common terms
            "live": ["hidup", "living", "vital"],
            "fresh": ["segar", "baru", "new"],
            "frozen": ["beku", "dingin", "cold"],
            "processed": ["olahan", "refined", "treated"]
        }
    
    def setup_connections(self):
        """Setup database and Redis connections"""
        # Database connection
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.db_conn = psycopg2.connect(DATABASE_URL)
                logger.info("✅ Database connected successfully")
                break
            except Exception as e:
                logger.error(f"❌ Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    
        # Redis connection
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            self.redis_client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None

    def initialize_ai_components(self):
        """Initialize AI components and cache data"""
        if not AI_AVAILABLE:
            logger.info("🤖 AI components not available, using basic search")
            return
            
        try:
            # Load HS codes for AI processing
            self._load_hs_codes_cache()
            
            # Initialize TF-IDF vectorizer if we have data
            if self.hs_codes_cache:
                self._initialize_tfidf()
                logger.info("🧠 AI components initialized successfully")
            else:
                logger.warning("⚠️ No HS codes data available for AI initialization")
                
        except Exception as e:
            logger.error(f"❌ AI initialization failed: {e}")

    def _load_hs_codes_cache(self):
        """Load HS codes into memory for AI processing"""
        if not self.db_conn:
            return
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT hscode, description_en, description_id, category, level, section
                FROM hs_codes 
                ORDER BY hscode
            """)
            
            self.hs_codes_cache = [dict(row) for row in cursor.fetchall()]
            logger.info(f"📊 Loaded {len(self.hs_codes_cache)} HS codes for AI processing")
            
        except Exception as e:
            logger.error(f"❌ Failed to load HS codes cache: {e}")

    def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer with HS codes data"""
        if not AI_AVAILABLE or not self.hs_codes_cache:
            return
            
        try:
            # Prepare text corpus
            texts = []
            for item in self.hs_codes_cache:
                # Combine description and keywords for better matching
                text_parts = [item['description_en']]
                if item.get('description_id'):
                    text_parts.append(item['description_id'])
                
                # Add synonyms for better semantic matching
                description_words = item['description_en'].lower().split()
                for word in description_words:
                    if word in self.synonym_dict:
                        text_parts.extend(self.synonym_dict[word])
                
                texts.append(' '.join(text_parts))
            
            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english',
                lowercase=True
            )
            
            # Fit vectorizer
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            logger.info("🔤 TF-IDF vectorizer initialized")
            
        except Exception as e:
            logger.error(f"❌ TF-IDF initialization failed: {e}")

    def expand_query_with_synonyms(self, query: str) -> List[str]:
        """Expand query with synonyms for better semantic matching"""
        words = query.lower().split()
        expanded_terms = set(words)
        
        for word in words:
            # Direct synonym lookup
            if word in self.synonym_dict:
                expanded_terms.update(self.synonym_dict[word])
            
            # Reverse synonym lookup
            for key, synonyms in self.synonym_dict.items():
                if word in synonyms:
                    expanded_terms.add(key)
                    expanded_terms.update(synonyms)
        
        return list(expanded_terms)

    def calculate_fuzzy_similarity(self, str1: str, str2: str) -> float:
        """Calculate fuzzy similarity between strings"""
        if not FUZZY_AVAILABLE:
            # Fallback to simple string similarity
            return 1.0 if str1.lower() == str2.lower() else 0.0
            
        # Use multiple fuzzy algorithms and take the best score
        ratio = fuzz.ratio(str1.lower(), str2.lower()) / 100.0
        partial_ratio = fuzz.partial_ratio(str1.lower(), str2.lower()) / 100.0
        token_sort = fuzz.token_sort_ratio(str1.lower(), str2.lower()) / 100.0
        
        return max(ratio, partial_ratio, token_sort)

    def detect_and_correct_typos(self, query: str) -> Tuple[str, List[str]]:
        """Detect typos and suggest corrections"""
        if not FUZZY_AVAILABLE or not self.hs_codes_cache:
            return query, []
        
        suggestions = []
        words = query.split()
        corrected_words = []
        
        for word in words:
            best_match = word
            best_score = 0
            
            # Check against HS code descriptions
            for item in self.hs_codes_cache:
                desc_words = item['description_en'].lower().split()
                for desc_word in desc_words:
                    if len(desc_word) > 3:  # Only check meaningful words
                        similarity = self.calculate_fuzzy_similarity(word, desc_word)
                        if similarity > best_score and similarity > 0.7:
                            best_score = similarity
                            best_match = desc_word
            
            corrected_words.append(best_match)
            
            # Add to suggestions if correction was made
            if best_match != word and best_score > 0.8:
                suggestions.append(f"{word} → {best_match}")
        
        corrected_query = ' '.join(corrected_words)
        return corrected_query, suggestions

    def ai_powered_search(self, query: str, category: str = 'all', ai_enabled: bool = True, limit: int = 20) -> Dict[str, Any]:
        """Advanced AI-powered search with multiple algorithms"""
        start_time = time.time()
        
        if not ai_enabled or not AI_AVAILABLE:
            return self._basic_database_search(query, category, limit)
        
        # Query preprocessing
        original_query = query
        expanded_terms = self.expand_query_with_synonyms(query)
        corrected_query, typo_suggestions = self.detect_and_correct_typos(query)
        
        # Multi-algorithm search
        results = []
        
        # 1. Exact and fuzzy database search
        db_results = self._enhanced_database_search(corrected_query, category, limit * 2)
        
        # 2. TF-IDF semantic search (if available)
        if self.tfidf_vectorizer is not None:
            semantic_results = self._tfidf_semantic_search(corrected_query, category, limit)
            db_results.extend(semantic_results)
        
        # 3. Fuzzy matching search
        fuzzy_results = self._fuzzy_matching_search(corrected_query, category, limit)
        db_results.extend(fuzzy_results)
        
        # Remove duplicates and score
        seen_codes = set()
        for result in db_results:
            if result['hscode'] not in seen_codes:
                # Calculate comprehensive AI score
                ai_score = self._calculate_ai_score(result, original_query, expanded_terms)
                result['ai_score'] = ai_score
                result['relevance_score'] = ai_score  # For compatibility
                results.append(result)
                seen_codes.add(result['hscode'])
        
        # Sort by AI score
        results.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        results = results[:limit]
        
        execution_time = time.time() - start_time
        
        return {
            'results': results,
            'total_count': len(results),
            'query': original_query,
            'corrected_query': corrected_query if corrected_query != original_query else None,
            'expanded_terms': expanded_terms if len(expanded_terms) > len(original_query.split()) else None,
            'typo_suggestions': typo_suggestions,
            'category': category,
            'ai_enabled': True,
            'ai_features_used': self._get_ai_features_used(),
            'execution_time': round(execution_time, 3),
            'search_type': 'ai_powered'
        }

    def _basic_database_search(self, query: str, category: str, limit: int) -> Dict[str, Any]:
        """Fallback basic database search"""
        if not self.db_conn:
            return {'error': 'Database not available', 'results': []}
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            if category == 'all':
                sql = """
                SELECT hscode, description_en, description_id, category, level, section
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
                SELECT hscode, description_en, description_id, category, level, section
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
            logger.error(f"Database search error: {e}")
            return {'error': str(e), 'results': []}

    def _enhanced_database_search(self, query: str, category: str, limit: int) -> List[Dict]:
        """Enhanced database search with better scoring"""
        if not self.db_conn:
            return []
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            # More sophisticated SQL query with scoring
            if category == 'all':
                sql = """
                SELECT 
                    hscode, description_en, description_id, category, level, section,
                    CASE 
                        WHEN hscode = %s THEN 100
                        WHEN hscode ILIKE %s THEN 90
                        WHEN description_en ILIKE %s THEN 80
                        WHEN description_en ILIKE %s THEN 70
                        WHEN description_en ILIKE %s THEN 60
                        ELSE 50
                    END as db_score
                FROM hs_codes 
                WHERE description_en ILIKE %s OR hscode ILIKE %s
                ORDER BY db_score DESC, hscode
                LIMIT %s
                """
                params = [query, f'{query}%', f'{query}%', f'%{query}%', f'%{query} %', f'%{query}%', f'%{query}%', limit]
            else:
                sql = """
                SELECT 
                    hscode, description_en, description_id, category, level, section,
                    CASE 
                        WHEN hscode = %s THEN 100
                        WHEN hscode ILIKE %s THEN 90
                        WHEN description_en ILIKE %s THEN 80
                        WHEN description_en ILIKE %s THEN 70
                        WHEN description_en ILIKE %s THEN 60
                        ELSE 50
                    END as db_score
                FROM hs_codes 
                WHERE (description_en ILIKE %s OR hscode ILIKE %s) AND category = %s
                ORDER BY db_score DESC, hscode
                LIMIT %s
                """
                params = [query, f'{query}%', f'{query}%', f'%{query}%', f'%{query} %', f'%{query}%', f'%{query}%', category, limit]
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Enhanced database search error: {e}")
            return []

    def _tfidf_semantic_search(self, query: str, category: str, limit: int) -> List[Dict]:
        """TF-IDF based semantic search"""
        if not self.tfidf_vectorizer or not self.hs_codes_cache:
            return []
            
        try:
            # Transform query to TF-IDF vector
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results above threshold
            results = []
            for idx, similarity in enumerate(similarities):
                if similarity > self.similarity_threshold:
                    item = self.hs_codes_cache[idx].copy()
                    if category == 'all' or item.get('category') == category:
                        item['semantic_score'] = float(similarity)
                        results.append(item)
            
            # Sort by similarity
            results.sort(key=lambda x: x['semantic_score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"TF-IDF search error: {e}")
            return []

    def _fuzzy_matching_search(self, query: str, category: str, limit: int) -> List[Dict]:
        """Fuzzy matching search for typo tolerance"""
        if not FUZZY_AVAILABLE or not self.hs_codes_cache:
            return []
            
        try:
            results = []
            
            for item in self.hs_codes_cache:
                if category != 'all' and item.get('category') != category:
                    continue
                
                # Calculate fuzzy similarity
                desc_similarity = self.calculate_fuzzy_similarity(query, item['description_en'])
                code_similarity = self.calculate_fuzzy_similarity(query, item['hscode'])
                
                max_similarity = max(desc_similarity, code_similarity)
                
                if max_similarity > 0.6:  # Fuzzy threshold
                    item_copy = item.copy()
                    item_copy['fuzzy_score'] = float(max_similarity)
                    results.append(item_copy)
            
            # Sort by fuzzy score
            results.sort(key=lambda x: x['fuzzy_score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return []

    def _calculate_ai_score(self, result: Dict, query: str, expanded_terms: List[str]) -> float:
        """Calculate comprehensive AI score for result ranking"""
        score = 0.0
        
        # Database score (if available)
        if 'db_score' in result:
            score += result['db_score'] * 0.4
        
        # Semantic score (if available)
        if 'semantic_score' in result:
            score += result['semantic_score'] * 100 * 0.3
        
        # Fuzzy score (if available)
        if 'fuzzy_score' in result:
            score += result['fuzzy_score'] * 100 * 0.2
        
        # Bonus for exact matches
        if query.lower() in result['hscode'].lower():
            score += 20
        
        if query.lower() in result['description_en'].lower():
            score += 15
        
        # Bonus for expanded term matches
        for term in expanded_terms:
            if term.lower() in result['description_en'].lower():
                score += 5
        
        return round(score, 2)

    def _get_ai_features_used(self) -> List[str]:
        """Get list of AI features that are currently active"""
        features = []
        
        if AI_AVAILABLE:
            features.append('tfidf_semantic_search')
        
        if FUZZY_AVAILABLE:
            features.append('fuzzy_matching')
            features.append('typo_correction')
        
        features.extend(['synonym_expansion', 'smart_scoring', 'multi_field_search'])
        
        return features

    def get_smart_suggestions(self, query: str, category: str = 'all', limit: int = 5) -> List[str]:
        """Generate smart suggestions based on query"""
        if not self.db_conn or len(query) < 2:
            return []
            
        try:
            # Get suggestions from cache if available
            cache_key = f"{query}:{category}"
            if cache_key in self.suggestions_cache:
                return self.suggestions_cache[cache_key][:limit]
            
            suggestions = set()
            
            # Database suggestions
            cursor = self.db_conn.cursor()
            
            if category == 'all':
                sql = """
                SELECT DISTINCT description_en 
                FROM hs_codes 
                WHERE description_en ILIKE %s 
                ORDER BY description_en 
                LIMIT %s
                """
                cursor.execute(sql, [f'{query}%', limit * 2])
            else:
                sql = """
                SELECT DISTINCT description_en 
                FROM hs_codes 
                WHERE description_en ILIKE %s AND category = %s 
                ORDER BY description_en 
                LIMIT %s
                """
                cursor.execute(sql, [f'{query}%', category, limit * 2])
            
            for row in cursor.fetchall():
                suggestions.add(row[0])
            
            # AI-enhanced suggestions
            if AI_AVAILABLE and self.hs_codes_cache:
                expanded_terms = self.expand_query_with_synonyms(query)
                for term in expanded_terms:
                    if term != query.lower():
                        for item in self.hs_codes_cache:
                            if category == 'all' or item.get('category') == category:
                                if term in item['description_en'].lower():
                                    suggestions.add(item['description_en'])
                                    if len(suggestions) >= limit * 2:
                                        break
            
            # Cache and return
            suggestion_list = list(suggestions)[:limit]
            self.suggestions_cache[cache_key] = suggestion_list
            return suggestion_list
            
        except Exception as e:
            logger.error(f"Suggestions error: {e}")
            return []

# Initialize search engine
search_engine = SmartHSSearchEngine()

@app.route('/api/health')
def health_check():
    """Enhanced health check with AI status"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-ai-enhanced',
        'ai_features': {
            'ai_available': AI_AVAILABLE,
            'fuzzy_matching': FUZZY_AVAILABLE,
            'nltk_available': NLTK_AVAILABLE,
            'tfidf_initialized': search_engine.tfidf_vectorizer is not None,
            'hs_codes_cached': len(search_engine.hs_codes_cache),
            'features_active': search_engine._get_ai_features_used()
        }
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
    """Enhanced AI-powered search endpoint"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if len(query) > 200:
            return jsonify({'error': 'Query too long (max 200 characters)'}), 400
        
        results = search_engine.ai_powered_search(
            query=query,
            category=data.get('category', 'all'),
            ai_enabled=data.get('ai_enabled', True),
            limit=min(data.get('limit', 20), 50)
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@app.route('/api/suggestions', methods=['POST'])
def api_suggestions():
    """Smart suggestions endpoint"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        
        if len(query) < 2:
            return jsonify({'suggestions': []})
        
        suggestions = search_engine.get_smart_suggestions(
            query=query,
            category=data.get('category', 'all'),
            limit=data.get('limit', 5)
        )
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return jsonify({'suggestions': []})

@app.route('/api/categories')
def api_categories():
    """Get categories with AI-enhanced info"""
    categories = [
        {'key': 'all', 'name': 'Semua', 'ai_optimized': True},
        {'key': 'electronics', 'name': 'Elektronik', 'ai_optimized': True},
        {'key': 'textiles', 'name': 'Tekstil', 'ai_optimized': True},
        {'key': 'machinery', 'name': 'Mesin', 'ai_optimized': True},
        {'key': 'chemicals', 'name': 'Kimia', 'ai_optimized': True},
        {'key': 'food', 'name': 'Makanan', 'ai_optimized': True},
        {'key': 'transport', 'name': 'Transport', 'ai_optimized': True},
        {'key': 'animals', 'name': 'Hewan', 'ai_optimized': True},
        {'key': 'plants', 'name': 'Tanaman', 'ai_optimized': True},
        {'key': 'metals', 'name': 'Logam', 'ai_optimized': True},
        {'key': 'others', 'name': 'Lainnya', 'ai_optimized': True}
    ]
    return jsonify({
        'categories': categories,
        'ai_features': search_engine._get_ai_features_used()
    })

@app.route('/api/ai-status')
def ai_status():
   """Get detailed AI status information"""
   return jsonify({
       'ai_available': AI_AVAILABLE,
       'fuzzy_matching': FUZZY_AVAILABLE,
       'nltk_available': NLTK_AVAILABLE,
       'features': search_engine._get_ai_features_used(),
       'cache_size': len(search_engine.hs_codes_cache),
       'tfidf_initialized': search_engine.tfidf_vectorizer is not None,
       'synonyms_loaded': len(search_engine.synonym_dict),
       'suggestions_cached': len(search_engine.suggestions_cache)
   })

@app.route('/')
def index():
   """Enhanced API info with AI features"""
   return jsonify({
       'name': 'HS Code Search API with AI',
       'version': '2.0.0-ai-enhanced',
       'status': 'running',
       'ai_features': {
           'smart_search': AI_AVAILABLE,
           'fuzzy_matching': FUZZY_AVAILABLE,
           'typo_correction': FUZZY_AVAILABLE,
           'semantic_search': AI_AVAILABLE,
           'synonym_expansion': True,
           'smart_suggestions': True,
           'auto_categorization': True
       },
       'endpoints': {
           'health': '/api/health',
           'search': '/api/search',
           'suggestions': '/api/suggestions',
           'categories': '/api/categories',
           'ai_status': '/api/ai-status'
       }
   })

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=False)
else:
   logger.info("🌐 AI-Enhanced Flask app ready for Gunicorn")

# For Gunicorn
application = app
