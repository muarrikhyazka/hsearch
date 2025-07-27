#!/usr/bin/env python3
"""
Script to fill missing Indonesian translations in HS codes database
Only translates and updates empty/null Indonesian fields for efficiency
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import logging
from tqdm import tqdm
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://hsearch_user:hsearch_secure_2024@localhost:5432/hsearch_db")

class IndonesianTranslationFiller:
    def __init__(self):
        self.db_conn = None
        self.translation_cache = {}
        
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def translate_text(self, text, target_lang='id', source_lang='en'):
        """
        Translate text using a simple translation approach
        In production, you might want to use Google Translate API or similar
        """
        if not text or text.strip() == '':
            return ''
            
        # Check cache first
        cache_key = f"{text}_{source_lang}_{target_lang}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # For now, we'll use a simple mapping for common terms
        # You can replace this with actual Google Translate API or similar service
        translation_map = {
            # Animals & Live Products
            'live animals; animal products': 'hewan hidup; produk hewani',
            'Animals; live': 'Hewan; hidup',
            'Horses, asses, mules and hinnies; live': 'Kuda, keledai, bagal dan hinny; hidup',
            'Horses; live, other than pure-bred breeding animals': 'Kuda; hidup, selain hewan pembibitan murni',
            
            # Vegetable Products
            'vegetable products': 'produk nabati',
            'Vegetables and certain roots and tubers; edible': 'Sayuran dan umbi-umbian tertentu; dapat dimakan',
            
            # Food Products
            'prepared foodstuffs; beverages, spirits and vinegar; tobacco': 'makanan olahan; minuman, spirits dan cuka; tembakau',
            
            # Textiles
            'textiles and textile articles': 'tekstil dan artikel tekstil',
            
            # Common terms
            'live': 'hidup',
            'fresh': 'segar',
            'frozen': 'beku',
            'dried': 'kering',
            'prepared': 'olahan',
            'other': 'lainnya',
            'not elsewhere specified': 'tidak diklasifikasikan di tempat lain',
            'n.e.s.': 'tidak diklasifikasikan di tempat lain',
        }
        
        # Try exact match first
        if text.lower() in translation_map:
            translated = translation_map[text.lower()]
        else:
            # Try partial matches for common terms
            translated = text
            for en_term, id_term in translation_map.items():
                if en_term.lower() in text.lower():
                    translated = translated.lower().replace(en_term.lower(), id_term)
                    break
            
            # If no translation found, keep original text as fallback
            if translated == text:
                logger.warning(f"⚠️ No translation found for: {text}")
        
        # Cache the translation
        self.translation_cache[cache_key] = translated
        return translated
    
    def analyze_missing_translations(self):
        """Analyze which Indonesian fields are missing"""
        if not self.db_conn:
            logger.error("❌ No database connection")
            return None
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            # Check missing Indonesian descriptions
            logger.info("🔍 Analyzing missing Indonesian translations...")
            
            # Count missing description_id
            cursor.execute("""
                SELECT COUNT(*) as missing_count 
                FROM hs_codes 
                WHERE description_id IS NULL OR description_id = '' OR description_id = 'nan'
            """)
            missing_desc_id = cursor.fetchone()['missing_count']
            
            # Count missing section_name_id
            cursor.execute("""
                SELECT COUNT(*) as missing_count 
                FROM hs_codes 
                WHERE section_name_id IS NULL OR section_name_id = '' OR section_name_id = 'nan'
            """)
            missing_section_id = cursor.fetchone()['missing_count']
            
            # Count missing chapter_desc_id
            cursor.execute("""
                SELECT COUNT(*) as missing_count 
                FROM hs_codes 
                WHERE chapter_desc_id IS NULL OR chapter_desc_id = '' OR chapter_desc_id = 'nan'
            """)
            missing_chapter_id = cursor.fetchone()['missing_count']
            
            # Count missing heading_desc_id
            cursor.execute("""
                SELECT COUNT(*) as missing_count 
                FROM hs_codes 
                WHERE heading_desc_id IS NULL OR heading_desc_id = '' OR heading_desc_id = 'nan'
            """)
            missing_heading_id = cursor.fetchone()['missing_count']
            
            # Count missing subheading_desc_id
            cursor.execute("""
                SELECT COUNT(*) as missing_count 
                FROM hs_codes 
                WHERE subheading_desc_id IS NULL OR subheading_desc_id = '' OR subheading_desc_id = 'nan'
            """)
            missing_subheading_id = cursor.fetchone()['missing_count']
            
            # Total records
            cursor.execute("SELECT COUNT(*) as total FROM hs_codes")
            total_records = cursor.fetchone()['total']
            
            analysis = {
                'total_records': total_records,
                'missing_description_id': missing_desc_id,
                'missing_section_name_id': missing_section_id,
                'missing_chapter_desc_id': missing_chapter_id,
                'missing_heading_desc_id': missing_heading_id,
                'missing_subheading_desc_id': missing_subheading_id
            }
            
            logger.info(f"📊 ANALYSIS RESULTS:")
            logger.info(f"   • Total records: {total_records:,}")
            logger.info(f"   • Missing description_id: {missing_desc_id:,}")
            logger.info(f"   • Missing section_name_id: {missing_section_id:,}")
            logger.info(f"   • Missing chapter_desc_id: {missing_chapter_id:,}")
            logger.info(f"   • Missing heading_desc_id: {missing_heading_id:,}")
            logger.info(f"   • Missing subheading_desc_id: {missing_subheading_id:,}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return None
    
    def fill_missing_descriptions(self):
        """Fill missing Indonesian description fields"""
        if not self.db_conn:
            logger.error("❌ No database connection")
            return False
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            # Get records with missing description_id
            logger.info("🔄 Fetching records with missing description_id...")
            cursor.execute("""
                SELECT hs_code, description_en 
                FROM hs_codes 
                WHERE description_id IS NULL OR description_id = '' OR description_id = 'nan'
                ORDER BY hs_code
            """)
            missing_desc_records = cursor.fetchall()
            
            if missing_desc_records:
                logger.info(f"📝 Translating {len(missing_desc_records)} missing descriptions...")
                
                for record in tqdm(missing_desc_records, desc="Translating descriptions"):
                    hs_code = record['hs_code']
                    description_en = record['description_en']
                    
                    # Translate to Indonesian
                    description_id = self.translate_text(description_en)
                    
                    # Update the record
                    cursor.execute("""
                        UPDATE hs_codes 
                        SET description_id = %s, updated_at = NOW()
                        WHERE hs_code = %s
                    """, (description_id, hs_code))
                
                self.db_conn.commit()
                logger.info(f"✅ Updated {len(missing_desc_records)} description_id fields")
            else:
                logger.info("✅ All description_id fields are already filled")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fill descriptions: {e}")
            self.db_conn.rollback()
            return False
    
    def fill_missing_hierarchy_translations(self):
        """Fill missing Indonesian hierarchy translations"""
        if not self.db_conn:
            logger.error("❌ No database connection")
            return False
            
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            # Fill missing section_name_id
            logger.info("🔄 Filling missing section_name_id...")
            cursor.execute("""
                UPDATE hs_codes 
                SET section_name_id = %s, updated_at = NOW()
                WHERE (section_name_id IS NULL OR section_name_id = '' OR section_name_id = 'nan')
                AND section_name IS NOT NULL AND section_name != ''
            """, (self.translate_text("live animals; animal products"),))
            
            section_updated = cursor.rowcount
            logger.info(f"✅ Updated {section_updated} section_name_id fields")
            
            # Fill missing chapter_desc_id
            logger.info("🔄 Filling missing chapter_desc_id...")
            cursor.execute("""
                SELECT DISTINCT chapter_desc 
                FROM hs_codes 
                WHERE (chapter_desc_id IS NULL OR chapter_desc_id = '' OR chapter_desc_id = 'nan')
                AND chapter_desc IS NOT NULL AND chapter_desc != ''
            """)
            unique_chapters = cursor.fetchall()
            
            chapter_updated = 0
            for chapter in tqdm(unique_chapters, desc="Translating chapters"):
                chapter_desc = chapter['chapter_desc']
                chapter_desc_id = self.translate_text(chapter_desc)
                
                cursor.execute("""
                    UPDATE hs_codes 
                    SET chapter_desc_id = %s, updated_at = NOW()
                    WHERE chapter_desc = %s 
                    AND (chapter_desc_id IS NULL OR chapter_desc_id = '' OR chapter_desc_id = 'nan')
                """, (chapter_desc_id, chapter_desc))
                
                chapter_updated += cursor.rowcount
            
            logger.info(f"✅ Updated {chapter_updated} chapter_desc_id fields")
            
            # Fill missing heading_desc_id
            logger.info("🔄 Filling missing heading_desc_id...")
            cursor.execute("""
                SELECT DISTINCT heading_desc 
                FROM hs_codes 
                WHERE (heading_desc_id IS NULL OR heading_desc_id = '' OR heading_desc_id = 'nan')
                AND heading_desc IS NOT NULL AND heading_desc != ''
                LIMIT 50
            """)
            unique_headings = cursor.fetchall()
            
            heading_updated = 0
            for heading in tqdm(unique_headings, desc="Translating headings"):
                heading_desc = heading['heading_desc']
                heading_desc_id = self.translate_text(heading_desc)
                
                cursor.execute("""
                    UPDATE hs_codes 
                    SET heading_desc_id = %s, updated_at = NOW()
                    WHERE heading_desc = %s 
                    AND (heading_desc_id IS NULL OR heading_desc_id = '' OR heading_desc_id = 'nan')
                """, (heading_desc_id, heading_desc))
                
                heading_updated += cursor.rowcount
            
            logger.info(f"✅ Updated {heading_updated} heading_desc_id fields")
            
            # Fill missing subheading_desc_id
            logger.info("🔄 Filling missing subheading_desc_id...")
            cursor.execute("""
                SELECT DISTINCT subheading_desc 
                FROM hs_codes 
                WHERE (subheading_desc_id IS NULL OR subheading_desc_id = '' OR subheading_desc_id = 'nan')
                AND subheading_desc IS NOT NULL AND subheading_desc != ''
                LIMIT 100
            """)
            unique_subheadings = cursor.fetchall()
            
            subheading_updated = 0
            for subheading in tqdm(unique_subheadings, desc="Translating subheadings"):
                subheading_desc = subheading['subheading_desc']
                subheading_desc_id = self.translate_text(subheading_desc)
                
                cursor.execute("""
                    UPDATE hs_codes 
                    SET subheading_desc_id = %s, updated_at = NOW()
                    WHERE subheading_desc = %s 
                    AND (subheading_desc_id IS NULL OR subheading_desc_id = '' OR subheading_desc_id = 'nan')
                """, (subheading_desc_id, subheading_desc))
                
                subheading_updated += cursor.rowcount
            
            logger.info(f"✅ Updated {subheading_updated} subheading_desc_id fields")
            
            self.db_conn.commit()
            
            logger.info(f"🎉 SUMMARY:")
            logger.info(f"   • Section names updated: {section_updated}")
            logger.info(f"   • Chapter descriptions updated: {chapter_updated}")
            logger.info(f"   • Heading descriptions updated: {heading_updated}")
            logger.info(f"   • Subheading descriptions updated: {subheading_updated}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fill hierarchy translations: {e}")
            self.db_conn.rollback()
            return False

def main():
    logger.info("🚀 Starting Indonesian translation filler...")
    
    filler = IndonesianTranslationFiller()
    
    # Connect to database
    if not filler.connect_database():
        sys.exit(1)
    
    # Analyze missing translations
    analysis = filler.analyze_missing_translations()
    if not analysis:
        sys.exit(1)
    
    # Ask user confirmation
    total_missing = (analysis['missing_description_id'] + 
                    analysis['missing_section_name_id'] + 
                    analysis['missing_chapter_desc_id'] + 
                    analysis['missing_heading_desc_id'] + 
                    analysis['missing_subheading_desc_id'])
    
    if total_missing == 0:
        logger.info("🎉 All Indonesian translations are complete!")
        return
    
    logger.info(f"⚠️ Found {total_missing} missing Indonesian translations")
    response = input("Do you want to fill missing translations? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        logger.info("❌ Translation filling cancelled")
        return
    
    # Fill missing descriptions
    if analysis['missing_description_id'] > 0:
        if not filler.fill_missing_descriptions():
            logger.error("❌ Failed to fill missing descriptions")
            sys.exit(1)
    
    # Fill missing hierarchy translations
    if (analysis['missing_section_name_id'] > 0 or 
        analysis['missing_chapter_desc_id'] > 0 or 
        analysis['missing_heading_desc_id'] > 0 or 
        analysis['missing_subheading_desc_id'] > 0):
        if not filler.fill_missing_hierarchy_translations():
            logger.error("❌ Failed to fill missing hierarchy translations")
            sys.exit(1)
    
    # Final analysis
    logger.info("🔍 Running final analysis...")
    final_analysis = filler.analyze_missing_translations()
    
    if final_analysis:
        final_missing = (final_analysis['missing_description_id'] + 
                        final_analysis['missing_section_name_id'] + 
                        final_analysis['missing_chapter_desc_id'] + 
                        final_analysis['missing_heading_desc_id'] + 
                        final_analysis['missing_subheading_desc_id'])
        
        logger.info(f"🎉 Translation filling completed!")
        logger.info(f"💾 Remaining missing translations: {final_missing}")
    
    filler.db_conn.close()
    logger.info("🔚 Database connection closed")

if __name__ == "__main__":
    main()