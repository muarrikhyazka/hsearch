#!/usr/bin/env python3
"""
Data import script for HS codes - Updated for final-dataset.csv structure
CSV columns: no,hs_code,description,section,chapter,heading,subheading,chapter_desc,heading_desc,subheading_desc,section_name
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import logging
import os
import sys
import numpy as np
from tqdm import tqdm

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vector embedding imports
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
    logger.info("✅ Sentence transformers available for vector embeddings")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("⚠️ Sentence transformers not available, skipping vector embeddings")

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://hsearch_user:hsearch_secure_2024@localhost:5432/hsearch_db")
DATA_FILE = "/app/data/final-dataset-standardized.csv"

# Initialize embedding model
embedding_model = None
if EMBEDDINGS_AVAILABLE:
    try:
        logger.info("🤖 Loading multilingual embedding model...")
        # Use multilingual model for Indonesian + English support
        embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("✅ Embedding model loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not load embedding model: {e}")
        EMBEDDINGS_AVAILABLE = False

def test_database_connection():
    """Test database connection with retries"""
    max_retries = 5
    for attempt in tqdm(range(max_retries), desc="Testing DB connection", unit="attempt"):
        try:
            logger.info(f"Testing database connection (attempt {attempt + 1}/{max_retries})...")
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ Database connection successful")
            cursor.close()
            conn.close()
            return True
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Database connection failed: {e}")
            if attempt < max_retries - 1:
                logger.info("⏳ Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                logger.error("💥 Max retries reached. Database connection failed.")
                return False
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            return False

def generate_embeddings(text_en: str, text_id: str = None):
    """Generate vector embeddings for text"""
    if not EMBEDDINGS_AVAILABLE or not embedding_model:
        return None, None, None
    
    try:
        # Generate English embedding
        emb_en = embedding_model.encode(text_en, convert_to_tensor=False)
        emb_en = emb_en.astype(np.float32)  # Ensure float32 for pgvector
        
        # Generate Indonesian embedding if available
        emb_id = None
        if text_id and text_id.strip():
            emb_id = embedding_model.encode(text_id, convert_to_tensor=False)
            emb_id = emb_id.astype(np.float32)
        
        # Generate combined embedding
        if emb_id is not None:
            # Average the embeddings for combined representation
            emb_combined = (emb_en + emb_id) / 2
        else:
            emb_combined = emb_en
        
        return emb_en.tolist(), emb_id.tolist() if emb_id is not None else None, emb_combined.tolist()
        
    except Exception as e:
        logger.warning(f"⚠️ Error generating embeddings: {e}")
        return None, None, None

def categorize_hs_code(description):
    """Auto-categorize HS code based on description"""
    if not description or pd.isna(description):
        return 'others'
        
    desc_lower = str(description).lower()
    
    # Electronics & Technology
    if any(word in desc_lower for word in ['electronic', 'computer', 'telephone', 'digital', 'software', 'electric', 
                                           'mobile', 'phone', 'radio', 'television', 'camera', 'semiconductor']):
        return 'electronics'
    
    # Textiles & Clothing
    elif any(word in desc_lower for word in ['textile', 'clothing', 'cotton', 'wool', 'fabric', 'garment', 
                                             'apparel', 'shirt', 'trouser', 'dress', 'hat', 'shoe']):
        return 'textiles'
    
    # Machinery & Equipment
    elif any(word in desc_lower for word in ['machine', 'equipment', 'motor', 'engine', 'apparatus', 'tool', 
                                             'instrument', 'mechanical', 'pump', 'compressor']):
        return 'machinery'
    
    # Chemicals & Pharmaceuticals
    elif any(word in desc_lower for word in ['chemical', 'pharmaceutical', 'medicine', 'drug', 'acid', 'alcohol', 
                                             'organic', 'inorganic', 'compound', 'preparation']):
        return 'chemicals'
    
    # Food & Beverages
    elif any(word in desc_lower for word in ['food', 'beverage', 'grain', 'meat', 'fish', 'fruit', 'vegetable', 
                                             'milk', 'cheese', 'bread', 'sugar', 'coffee', 'tea']):
        return 'food'
    
    # Vehicles & Transport
    elif any(word in desc_lower for word in ['vehicle', 'car', 'truck', 'ship', 'aircraft', 'boat', 'motorcycle', 
                                             'bicycle', 'transport', 'railway']):
        return 'transport'
    
    # Animals & Live Products
    elif any(word in desc_lower for word in ['animal', 'live', 'cattle', 'horse', 'pig', 'sheep', 'poultry', 
                                             'fish; live', 'breeding']):
        return 'animals'
    
    # Plants & Agricultural
    elif any(word in desc_lower for word in ['plant', 'flower', 'tree', 'seed', 'vegetable', 'fruit', 'grain', 
                                             'agricultural', 'forestry']):
        return 'plants'
    
    # Metals & Minerals
    elif any(word in desc_lower for word in ['metal', 'iron', 'steel', 'aluminum', 'copper', 'zinc', 'mineral', 
                                             'stone', 'cement', 'ceramic']):
        return 'metals'
    
    # Energy & Fuels
    elif any(word in desc_lower for word in ['fuel', 'oil', 'gas', 'petroleum', 'energy', 'coal', 'electricity']):
        return 'energy'
    
    else:
        return 'others'

def validate_and_clean_data(row):
    """Validate and clean row data for new structure"""
    try:
        # Extract data from new CSV structure  
        no = int(row['no']) if pd.notna(row['no']) else None
        hs_code = str(row['hs_code']).strip() if pd.notna(row['hs_code']) else ''
        description = str(row['description_en']).strip() if pd.notna(row['description_en']) else ''
        section = str(row['section']).strip() if pd.notna(row['section']) else ''
        chapter = str(row['chapter']).strip() if pd.notna(row['chapter']) else ''
        heading = str(row['heading']).strip() if pd.notna(row['heading']) else ''
        subheading = str(row['subheading']).strip() if pd.notna(row['subheading']) else ''
        chapter_desc = str(row['chapter_desc_en']).strip() if pd.notna(row['chapter_desc_en']) else ''
        heading_desc = str(row['heading_desc_en']).strip() if pd.notna(row['heading_desc_en']) else ''
        subheading_desc = str(row['subheading_desc_en']).strip() if pd.notna(row['subheading_desc_en']) else ''
        section_name = str(row['section_name_en']).strip() if pd.notna(row['section_name_en']) else ''
        
        # Extract Indonesian descriptions
        chapter_desc_id = str(row['chapter_desc_id']).strip() if pd.notna(row['chapter_desc_id']) else ''
        heading_desc_id = str(row['heading_desc_id']).strip() if pd.notna(row['heading_desc_id']) else ''
        subheading_desc_id = str(row['subheading_desc_id']).strip() if pd.notna(row['subheading_desc_id']) else ''
        section_name_id = str(row['section_name_id']).strip() if pd.notna(row['section_name_id']) else ''
        
        # Validate required fields
        if not hs_code or hs_code == 'nan':
            return None, "Missing HS code"
        
        if not description or description == 'nan':
            return None, "Missing description"
        
        # Clean description - remove extra quotes and normalize
        description = description.strip('"').strip("'").strip()
        
        # Auto-categorize
        category = categorize_hs_code(description)
        
        # Determine level based on hierarchy presence
        level = 6  # Default subheading level
        if not subheading or subheading == '':
            level = 4 if heading and heading != '' else 2 if chapter and chapter != '' else 1
        
        # Extract Indonesian main description
        description_id = str(row['description_id']).strip() if pd.notna(row['description_id']) else ''
        
        return {
            'no': no,
            'hs_code': hs_code,
            'description_en': description,
            'description_id': description_id,
            'section': section,
            'chapter': chapter,
            'heading': heading,
            'subheading': subheading,
            'chapter_desc': chapter_desc,
            'heading_desc': heading_desc,
            'subheading_desc': subheading_desc,
            'section_name': section_name,
            'chapter_desc_id': chapter_desc_id,
            'heading_desc_id': heading_desc_id,
            'subheading_desc_id': subheading_desc_id,
            'section_name_id': section_name_id,
            'level': level,
            'category': category
        }, None
        
    except Exception as e:
        return None, f"Data validation error: {str(e)}"

def main():
    logger.info("🚀 Starting HS Code data import with complete Indonesian translations...")
    logger.info(f"📁 Source: {DATA_FILE}")
    
    # Test database connection first
    if not test_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Load local data file
    logger.info("📥 Loading HS code data...")
    try:
        # Force code columns to be read as strings to preserve leading zeros
        dtype_dict = {
            'hs_code': str,
            'section': str, 
            'chapter': str,
            'heading': str,
            'subheading': str
        }
        df = pd.read_csv(DATA_FILE, dtype=dtype_dict)
        logger.info(f"✅ Loaded {len(df)} records")
        logger.info(f"📊 Columns: {list(df.columns)}")
        
        # Log sample data to verify leading zeros are preserved
        sample_codes = df[['hs_code', 'chapter', 'heading', 'subheading']].head(3)
        logger.info(f"📋 Sample codes (checking leading zeros):\n{sample_codes}")
        
        # Verify expected columns for new structure
        expected_columns = ['no', 'hs_code', 'description_en', 'description_id', 'section', 'chapter', 'heading', 'subheading', 
                           'section_name_en', 'chapter_desc_en', 'heading_desc_en', 'subheading_desc_en',
                           'section_name_id', 'chapter_desc_id', 'heading_desc_id', 'subheading_desc_id']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"❌ Missing expected columns: {missing_columns}")
            logger.error(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        # Show data sample
        logger.info("📋 Data sample:")
        for i, (idx, row) in enumerate(df.head(3).iterrows()):
            logger.info(f"  Row {i+1}: {row['hs_code']} - {row['description_en'][:60]}...")
            
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        sys.exit(1)
    
    # Connect to database
    logger.info("🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Prepare table for data import (assumes table structure already exists from init.sql)
    logger.info("🧹 Preparing table for data import...")
    try:
        # Check if table exists
        logger.info("  🔍 Verifying table exists...")
        cursor.execute("""
            SELECT schemaname, tablename, tableowner 
            FROM pg_tables 
            WHERE tablename = 'hs_codes'
        """)
        existing_table = cursor.fetchone()
        
        if not existing_table:
            logger.error("  ❌ Table 'hs_codes' not found!")
            logger.error("💡 Please ensure the database is initialized with init.sql first:")
            logger.error("   docker compose exec hs_postgres psql -U hsearch_user -d hsearch_db -f /docker-entrypoint-initdb.d/init.sql")
            sys.exit(1)
        
        logger.info(f"  ✅ Table found: {existing_table}")
        
        # Check table size and clear if needed
        logger.info("  📊 Checking existing data...")
        cursor.execute("SELECT COUNT(*) FROM hs_codes")
        record_count = cursor.fetchone()[0]
        logger.info(f"  📊 Current records: {record_count:,}")
        
        if record_count > 0:
            logger.info("  ⏳ Clearing existing data...")
            start_time = time.time()
            cursor.execute("TRUNCATE TABLE hs_codes RESTART IDENTITY CASCADE")
            elapsed = time.time() - start_time
            logger.info(f"  ✅ Table cleared in {elapsed:.2f} seconds")
        else:
            logger.info("  ✅ Table is empty, ready for import")
        
        # Verify table structure
        logger.info("  🔍 Verifying table structure...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'hs_codes' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        logger.info(f"  ✅ Table has {len(columns)} columns")
        
        # Check for required columns
        required_columns = ['hs_code', 'description_en', 'level', 'category']
        existing_columns = [col[0] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            logger.error(f"  ❌ Missing required columns: {missing_columns}")
            sys.exit(1)
        
        logger.info("  ✅ Table structure verified")
        conn.commit()
        logger.info("✅ Table preparation completed")
        
    except Exception as e:
        logger.error(f"❌ Table preparation failed: {e}")
        conn.rollback()
        sys.exit(1)
    
    # Process data
    batch_size = 100
    total_records = len(df)
    processed_count = 0
    error_count = 0
    
    logger.info(f"📊 Processing {total_records} records in batches of {batch_size}...")
    
    # Create single progress bar for all records
    total_progress = tqdm(total=total_records, desc="Processing records", unit="record")
    
    for i in range(0, total_records, batch_size):
        batch_end = min(i + batch_size, total_records)
        batch_df = df[i:batch_end].copy()
        
        batch_num = i//batch_size + 1
        total_batches = (total_records-1)//batch_size + 1
        logger.info(f"📦 Processing batch {batch_num}/{total_batches} (records {i+1}-{batch_end})")
        
        batch_processed = 0
        batch_errors = 0
        
        for idx, row in batch_df.iterrows():
            hscode = "UNKNOWN"
            
            try:
                # Clean and validate data
                data, error_msg = validate_and_clean_data(row)
                
                if error_msg:
                    hscode = str(row.get('hscode', 'UNKNOWN'))
                    logger.debug(f"⚠️ Skipping record {idx} ({hscode}): {error_msg}")
                    batch_errors += 1
                    continue
                
                hs_code = data['hs_code']
                
                # Generate embeddings for vector search
                description_en = data['description_en']
                description_id = data['description_id']  # Indonesian description from CSV
                
                # Create combined text for embedding
                combined_text = description_en
                if description_id and description_id.strip():
                    combined_text = f"{description_en} {description_id}"
                
                emb_en, emb_id, emb_combined = generate_embeddings(description_en, description_id)
                
                # Insert into database with vector embeddings
                sql = """
                INSERT INTO hs_codes 
                (no, hs_code, description_en, description_id, section, chapter, heading, subheading,
                 chapter_desc, heading_desc, subheading_desc, section_name, 
                 chapter_desc_id, heading_desc_id, subheading_desc_id, section_name_id,
                 level, category, embedding_en, embedding_id, embedding_combined,
                 search_vector_en, search_vector_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        to_tsvector('english', %s), to_tsvector('simple', %s), NOW(), NOW())
                ON CONFLICT (hs_code) DO UPDATE SET
                    no = EXCLUDED.no,
                    description_en = EXCLUDED.description_en,
                    description_id = EXCLUDED.description_id,
                    section = EXCLUDED.section,
                    chapter = EXCLUDED.chapter,
                    heading = EXCLUDED.heading,
                    subheading = EXCLUDED.subheading,
                    chapter_desc = EXCLUDED.chapter_desc,
                    heading_desc = EXCLUDED.heading_desc,
                    subheading_desc = EXCLUDED.subheading_desc,
                    section_name = EXCLUDED.section_name,
                    chapter_desc_id = EXCLUDED.chapter_desc_id,
                    heading_desc_id = EXCLUDED.heading_desc_id,
                    subheading_desc_id = EXCLUDED.subheading_desc_id,
                    section_name_id = EXCLUDED.section_name_id,
                    level = EXCLUDED.level,
                    category = EXCLUDED.category,
                    embedding_en = EXCLUDED.embedding_en,
                    embedding_id = EXCLUDED.embedding_id,
                    embedding_combined = EXCLUDED.embedding_combined,
                    search_vector_en = to_tsvector('english', EXCLUDED.description_en),
                    search_vector_id = to_tsvector('simple', EXCLUDED.description_id),
                    updated_at = NOW()
                """
                
                cursor.execute(sql, (
                    data['no'],
                    data['hs_code'],
                    data['description_en'],
                    description_id,  # Indonesian description
                    data['section'],
                    data['chapter'],
                    data['heading'],
                    data['subheading'],
                    data['chapter_desc'],
                    data['heading_desc'],
                    data['subheading_desc'],
                    data['section_name'],
                    data['chapter_desc_id'],  # Indonesian chapter description
                    data['heading_desc_id'],  # Indonesian heading description
                    data['subheading_desc_id'],  # Indonesian subheading description
                    data['section_name_id'],  # Indonesian section name
                    data['level'],
                    data['category'],
                    emb_en,  # English embedding vector
                    emb_id,  # Indonesian embedding vector  
                    emb_combined,  # Combined embedding vector
                    data['description_en'],  # For English search vector
                    description_id or ''  # For Indonesian search vector
                ))
                
                batch_processed += 1
                
                # Update main progress bar
                total_progress.update(1)
                total_progress.set_postfix({"Batch": f"{batch_num}/{total_batches}", "HS Code": hs_code})
                
            except psycopg2.Error as e:
                logger.error(f"❌ Database error for {hs_code}: {e}")
                batch_errors += 1
                conn.rollback()
                continue
            except Exception as e:
                logger.error(f"❌ Processing error for {hs_code}: {e}")
                batch_errors += 1
                total_progress.update(1)
                continue
        
        # Commit batch
        try:
            conn.commit()
            processed_count += batch_processed
            error_count += batch_errors
            
            if batch_processed > 0:
                logger.info(f"✅ Batch {batch_num} completed: {batch_processed} processed, {batch_errors} errors")
            else:
                logger.warning(f"⚠️ Batch {batch_num} completed: 0 processed, {batch_errors} errors")
                
        except Exception as e:
            logger.error(f"❌ Failed to commit batch: {e}")
            conn.rollback()
    
    # Close progress bar
    total_progress.close()
    
    # Create vector indexes after data import (much faster with data present)
    logger.info("\n🔧 Creating vector indexes for optimal search performance...")
    logger.info("   ⏳ This may take a few minutes for large datasets...")
    try:
        # Define index creation tasks (these are the indexes removed from init.sql)
        index_tasks = [
            ("Full-text search (English)", "CREATE INDEX IF NOT EXISTS idx_hs_search_en ON hs_codes USING GIN (search_vector_en)"),
            ("Full-text search (Indonesian)", "CREATE INDEX IF NOT EXISTS idx_hs_search_id ON hs_codes USING GIN (search_vector_id)")
        ]
        
        # Add vector indexes only if embeddings are available
        if EMBEDDINGS_AVAILABLE:
            index_tasks.extend([
                ("Vector embedding (English)", """CREATE INDEX IF NOT EXISTS idx_hs_embedding_en ON hs_codes 
                USING ivfflat (embedding_en vector_cosine_ops) WITH (lists = 100)"""),
                ("Vector embedding (Indonesian)", """CREATE INDEX IF NOT EXISTS idx_hs_embedding_id ON hs_codes 
                USING ivfflat (embedding_id vector_cosine_ops) WITH (lists = 100)"""),
                ("Vector embedding (Combined)", """CREATE INDEX IF NOT EXISTS idx_hs_embedding_combined ON hs_codes 
                USING ivfflat (embedding_combined vector_cosine_ops) WITH (lists = 100)""")
            ])
        else:
            logger.info("   ⚠️ Skipping vector indexes - sentence-transformers not available")
        
        # Create indexes with progress bar
        for desc, sql in tqdm(index_tasks, desc="Creating indexes", unit="index"):
            logger.info(f"   • Creating {desc} index...")
            cursor.execute(sql)
            
        if not EMBEDDINGS_AVAILABLE:
            logger.info("   ⚠️ Skipped vector indexes - embeddings not available")
        else:
            logger.info("   ✅ All indexes created successfully")
        
        conn.commit()
        logger.info("✅ All indexes created successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not create some indexes: {e}")
        conn.rollback()
    
    # Final statistics
    logger.info(f"\n📊 IMPORT SUMMARY:")
    logger.info(f"   • Total records processed: {processed_count:,}")
    logger.info(f"   • Total errors: {error_count:,}")
    
    if processed_count + error_count > 0:
        success_rate = (processed_count / (processed_count + error_count)) * 100
        logger.info(f"   • Success rate: {success_rate:.1f}%")
    
    # Database verification
    try:
        cursor.execute("SELECT COUNT(*) FROM hs_codes")
        db_count = cursor.fetchone()[0]
        logger.info(f"   • Records in database: {db_count:,}")
        
        if db_count > 0:
            # Category breakdown
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM hs_codes 
                GROUP BY category 
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            
            logger.info(f"\n📂 CATEGORY BREAKDOWN:")
            for cat, count in categories:
                logger.info(f"   • {cat}: {count:,} records")
            
            # Level breakdown
            cursor.execute("""
                SELECT level, COUNT(*) as count 
                FROM hs_codes 
                GROUP BY level 
                ORDER BY level
            """)
            levels = cursor.fetchall()
            
            logger.info(f"\n📊 HIERARCHY LEVELS:")
            for level, count in levels:
                logger.info(f"   • Level {level}: {count:,} records")
            
            # Sample imported data
            cursor.execute("""
                SELECT hs_code, description_en, category, level 
                FROM hs_codes 
                ORDER BY hs_code 
                LIMIT 5
            """)
            samples = cursor.fetchall()
            
            logger.info(f"\n📋 SAMPLE IMPORTED DATA:")
            for code, desc, cat, level in samples:
                logger.info(f"   • {code} (L{level}): {desc[:50]}... [{cat}]")
                
    except Exception as e:
        logger.error(f"❌ Could not get database statistics: {e}")
    
    # Close connections
    cursor.close()
    conn.close()
    logger.info("\n🔚 Database connection closed")
    
    if processed_count > 0:
        logger.info("🎉 Data import completed successfully!")
        logger.info(f"💾 {processed_count:,} HS codes imported and ready for search!")
    else:
        logger.error("💥 Data import failed - no records were processed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
