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

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://hsearch_user:hsearch_secure_2024@localhost:5432/hsearch_db")
DATA_FILE = "data/final-dataset.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection with retries"""
    max_retries = 5
    for attempt in range(max_retries):
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
        description = str(row['description']).strip() if pd.notna(row['description']) else ''
        section = str(row['section']).strip() if pd.notna(row['section']) else ''
        chapter = str(row['chapter']).strip() if pd.notna(row['chapter']) else ''
        heading = str(row['heading']).strip() if pd.notna(row['heading']) else ''
        subheading = str(row['subheading']).strip() if pd.notna(row['subheading']) else ''
        chapter_desc = str(row['chapter_desc_en']).strip() if pd.notna(row['chapter_desc_en']) else ''
        heading_desc = str(row['heading_desc_en']).strip() if pd.notna(row['heading_desc_en']) else ''
        subheading_desc = str(row['subheading_desc_en']).strip() if pd.notna(row['subheading_desc_en']) else ''
        section_name = str(row['section_name_en']).strip() if pd.notna(row['section_name_en']) else ''
        
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
        
        return {
            'no': no,
            'hs_code': hs_code,
            'description_en': description,
            'section': section,
            'chapter': chapter,
            'heading': heading,
            'subheading': subheading,
            'chapter_desc': chapter_desc,
            'heading_desc': heading_desc,
            'subheading_desc': subheading_desc,
            'section_name': section_name,
            'level': level,
            'category': category
        }, None
        
    except Exception as e:
        return None, f"Data validation error: {str(e)}"

def main():
    logger.info("🚀 Starting HS Code data import...")
    logger.info(f"📁 Source: {DATA_FILE}")
    
    # Test database connection first
    if not test_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Load local data file
    logger.info("📥 Loading HS code data...")
    try:
        df = pd.read_csv(DATA_FILE)
        logger.info(f"✅ Loaded {len(df)} records")
        logger.info(f"📊 Columns: {list(df.columns)}")
        
        # Verify expected columns for new structure
        expected_columns = ['no', 'hs_code', 'description', 'section', 'chapter', 'heading', 'subheading', 'section_name_en', 'chapter_desc_en', 'heading_desc_en', 'subheading_desc_en']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"❌ Missing expected columns: {missing_columns}")
            logger.error(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        # Show data sample
        logger.info("📋 Data sample:")
        for i, (idx, row) in enumerate(df.head(3).iterrows()):
            logger.info(f"  Row {i+1}: {row['hs_code']} - {row['description'][:60]}...")
            
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
    
    # Clear existing data
    logger.info("🧹 Clearing existing data...")
    try:
        cursor.execute("DELETE FROM hs_codes")
        conn.commit()
        logger.info("✅ Existing data cleared")
    except Exception as e:
        logger.warning(f"⚠️ Could not clear existing data: {e}")
        conn.rollback()
    
    # Process data
    batch_size = 100
    total_records = len(df)
    processed_count = 0
    error_count = 0
    
    logger.info(f"📊 Processing {total_records} records in batches of {batch_size}...")
    
    for i in range(0, total_records, batch_size):
        batch_end = min(i + batch_size, total_records)
        batch_df = df[i:batch_end].copy()
        
        logger.info(f"📦 Processing batch {i//batch_size + 1}/{(total_records-1)//batch_size + 1} (records {i+1}-{batch_end})")
        
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
                
                # Insert into database with new structure
                sql = """
                INSERT INTO hs_codes 
                (no, hs_code, description_en, description_id, section, chapter, heading, subheading,
                 chapter_desc, heading_desc, subheading_desc, section_name, level, category, 
                 search_vector_en, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, to_tsvector('english', %s), NOW(), NOW())
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
                    level = EXCLUDED.level,
                    category = EXCLUDED.category,
                    search_vector_en = to_tsvector('english', EXCLUDED.description_en),
                    updated_at = NOW()
                """
                
                cursor.execute(sql, (
                    data['no'],
                    data['hs_code'],
                    data['description_en'],
                    data['description_en'],  # Placeholder for Indonesian translation
                    data['section'],
                    data['chapter'],
                    data['heading'],
                    data['subheading'],
                    data['chapter_desc'],
                    data['heading_desc'],
                    data['subheading_desc'],
                    data['section_name'],
                    data['level'],
                    data['category'],
                    data['description_en']  # For search vector
                ))
                
                batch_processed += 1
                
            except psycopg2.Error as e:
                logger.error(f"❌ Database error for {hs_code}: {e}")
                batch_errors += 1
                conn.rollback()
                continue
            except Exception as e:
                logger.error(f"❌ Processing error for {hs_code}: {e}")
                batch_errors += 1
                continue
        
        # Commit batch
        try:
            conn.commit()
            processed_count += batch_processed
            error_count += batch_errors
            
            if batch_processed > 0:
                logger.info(f"✅ Batch completed: {batch_processed} processed, {batch_errors} errors")
            else:
                logger.warning(f"⚠️ Batch completed: 0 processed, {batch_errors} errors")
                
        except Exception as e:
            logger.error(f"❌ Failed to commit batch: {e}")
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
