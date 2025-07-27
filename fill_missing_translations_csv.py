#!/usr/bin/env python3
"""
Script to fill missing Indonesian translations in CSV file
Creates a separate CSV with only the updated records
"""

import pandas as pd
import logging
from tqdm import tqdm
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths
INPUT_CSV = "data/final-dataset-translated.csv"
OUTPUT_CSV = "data/final-dataset-complete.csv"
UPDATES_CSV = "data/missing-translations-filled.csv"

class CSVTranslationFiller:
    def __init__(self):
        self.translation_map = {
            # Section names
            'live animals; animal products': 'hewan hidup; produk hewani',
            'vegetable products': 'produk nabati',
            'animal or vegetable fats and oils': 'lemak dan minyak hewani atau nabati',
            'prepared foodstuffs; beverages, spirits and vinegar; tobacco': 'makanan olahan; minuman, spirits dan cuka; tembakau',
            'mineral products': 'produk mineral',
            'products of the chemical or allied industries': 'produk industri kimia atau industri terkait',
            'plastics and articles thereof; rubber and articles thereof': 'plastik dan artikel plastik; karet dan artikel karet',
            'raw hides and skins, leather, furskins': 'kulit mentah dan kulit samak, kulit berbulu',
            'wood and articles of wood; wood charcoal': 'kayu dan artikel kayu; arang kayu',
            'pulp of wood or other fibrous cellulosic material': 'pulp kayu atau bahan berserat selulosa lainnya',
            'textiles and textile articles': 'tekstil dan artikel tekstil',
            'footwear, headgear, umbrellas': 'alas kaki, tutup kepala, payung',
            'articles of stone, plaster, cement, asbestos': 'artikel batu, plaster, semen, asbes',
            'natural or cultured pearls, precious stones': 'mutiara alami atau budidaya, batu mulia',
            'base metals and articles of base metal': 'logam dasar dan artikel logam dasar',
            'machinery and mechanical appliances; electrical equipment': 'mesin dan peralatan mekanik; peralatan listrik',
            'vehicles, aircraft, vessels': 'kendaraan, pesawat terbang, kapal',
            'optical, photographic, cinematographic instruments': 'instrumen optik, fotografi, sinematografi',
            'arms and ammunition; parts and accessories': 'senjata dan amunisi; bagian dan aksesori',
            'miscellaneous manufactured articles': 'artikel manufaktur lain-lain',
            'works of art, collectors pieces and antiques': 'karya seni, barang koleksi dan barang antik',
            
            # Chapter descriptions
            'Animals; live': 'Hewan; hidup',
            'Meat and edible meat offal': 'Daging dan jeroan yang dapat dimakan',
            'Fish and crustaceans, molluscs': 'Ikan dan krustasea, moluska',
            'Dairy produce; birds eggs; natural honey': 'Produk susu; telur unggas; madu alami',
            'Products of animal origin, n.e.s.': 'Produk asal hewan, tidak diklasifikasikan di tempat lain',
            'Live trees and other plants': 'Pohon hidup dan tanaman lain',
            'Edible vegetables and certain roots': 'Sayuran yang dapat dimakan dan akar tertentu',
            'Edible fruit and nuts': 'Buah dan kacang yang dapat dimakan',
            'Coffee, tea, mate and spices': 'Kopi, teh, maté dan rempah-rempah',
            'Cereals': 'Sereal',
            'Products of the milling industry': 'Produk industri penggilingan',
            'Oil seeds and oleaginous fruits': 'Biji berminyak dan buah berminyak',
            'Lac; gums, resins': 'Lak; getah, resin',
            'Vegetable plaiting materials': 'Bahan anyaman nabati',
            
            # Heading descriptions
            'Horses, asses, mules and hinnies; live': 'Kuda, keledai, bagal dan hinny; hidup',
            'Bovine animals; live': 'Hewan sapi; hidup',
            'Swine; live': 'Babi; hidup',
            'Sheep and goats; live': 'Domba dan kambing; hidup',
            'Poultry, live': 'Unggas; hidup',
            'Animals; live, n.e.s.': 'Hewan; hidup, tidak diklasifikasikan di tempat lain',
            'Meat of bovine animals': 'Daging hewan sapi',
            'Meat of swine': 'Daging babi',
            'Meat of sheep or goats': 'Daging domba atau kambing',
            'Meat and edible offal of poultry': 'Daging dan jeroan unggas yang dapat dimakan',
            
            # Common terms
            'live': 'hidup',
            'fresh': 'segar',
            'frozen': 'beku',
            'dried': 'kering',
            'prepared': 'olahan',
            'other': 'lainnya',
            'pure-bred breeding': 'pembibitan murni',
            'breeding animals': 'hewan pembibitan',
            'weighing': 'dengan berat',
            'less than': 'kurang dari',
            'or more': 'atau lebih',
            'not elsewhere specified': 'tidak diklasifikasikan di tempat lain',
            'n.e.s.': 'tidak diklasifikasikan di tempat lain',
        }
    
    def translate_text(self, text):
        """Translate English text to Indonesian"""
        if pd.isna(text) or text == '' or text == 'nan':
            return ''
        
        text = str(text).strip()
        if text == '':
            return ''
        
        # Try exact match first
        text_lower = text.lower()
        if text_lower in self.translation_map:
            return self.translation_map[text_lower]
        
        # Try partial matches
        translated = text
        for en_term, id_term in self.translation_map.items():
            if en_term.lower() in text_lower:
                translated = re.sub(re.escape(en_term), id_term, translated, flags=re.IGNORECASE)
        
        # If no translation found, return original text as fallback
        return translated
    
    def is_empty_translation(self, value):
        """Check if a translation field is empty"""
        return pd.isna(value) or str(value).strip() == '' or str(value).strip().lower() == 'nan'
    
    def fill_missing_translations(self):
        """Fill missing Indonesian translations in CSV"""
        logger.info(f"📥 Loading CSV file: {INPUT_CSV}")
        
        try:
            df = pd.read_csv(INPUT_CSV)
            logger.info(f"✅ Loaded {len(df)} records")
        except Exception as e:
            logger.error(f"❌ Failed to load CSV: {e}")
            return False
        
        # Analyze missing translations
        logger.info("🔍 Analyzing missing translations...")
        
        missing_description_id = df[df['description_id'].isna() | (df['description_id'] == '') | (df['description_id'] == 'nan')].shape[0]
        missing_section_name_id = df[df['section_name_id'].isna() | (df['section_name_id'] == '') | (df['section_name_id'] == 'nan')].shape[0]
        missing_chapter_desc_id = df[df['chapter_desc_id'].isna() | (df['chapter_desc_id'] == '') | (df['chapter_desc_id'] == 'nan')].shape[0]
        missing_heading_desc_id = df[df['heading_desc_id'].isna() | (df['heading_desc_id'] == '') | (df['heading_desc_id'] == 'nan')].shape[0]
        missing_subheading_desc_id = df[df['subheading_desc_id'].isna() | (df['subheading_desc_id'] == '') | (df['subheading_desc_id'] == 'nan')].shape[0]
        
        logger.info(f"📊 MISSING TRANSLATIONS:")
        logger.info(f"   • description_id: {missing_description_id:,}")
        logger.info(f"   • section_name_id: {missing_section_name_id:,}")
        logger.info(f"   • chapter_desc_id: {missing_chapter_desc_id:,}")
        logger.info(f"   • heading_desc_id: {missing_heading_desc_id:,}")
        logger.info(f"   • subheading_desc_id: {missing_subheading_desc_id:,}")
        
        total_missing = missing_description_id + missing_section_name_id + missing_chapter_desc_id + missing_heading_desc_id + missing_subheading_desc_id
        
        if total_missing == 0:
            logger.info("🎉 All translations are complete!")
            return True
        
        # Create a copy for updates
        df_updated = df.copy()
        updated_records = []
        
        logger.info(f"🔄 Filling {total_missing} missing translations...")
        
        # Fill missing translations
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing records"):
            record_updated = False
            updated_row = row.copy()
            
            # Fill description_id
            if self.is_empty_translation(row['description_id']):
                translated = self.translate_text(row['description_en'])
                df_updated.at[idx, 'description_id'] = translated
                updated_row['description_id'] = translated
                record_updated = True
            
            # Fill section_name_id
            if self.is_empty_translation(row['section_name_id']):
                translated = self.translate_text(row['section_name_en'])
                df_updated.at[idx, 'section_name_id'] = translated
                updated_row['section_name_id'] = translated
                record_updated = True
            
            # Fill chapter_desc_id
            if self.is_empty_translation(row['chapter_desc_id']):
                translated = self.translate_text(row['chapter_desc_en'])
                df_updated.at[idx, 'chapter_desc_id'] = translated
                updated_row['chapter_desc_id'] = translated
                record_updated = True
            
            # Fill heading_desc_id
            if self.is_empty_translation(row['heading_desc_id']):
                translated = self.translate_text(row['heading_desc_en'])
                df_updated.at[idx, 'heading_desc_id'] = translated
                updated_row['heading_desc_id'] = translated
                record_updated = True
            
            # Fill subheading_desc_id
            if self.is_empty_translation(row['subheading_desc_id']):
                translated = self.translate_text(row['subheading_desc_en'])
                df_updated.at[idx, 'subheading_desc_id'] = translated
                updated_row['subheading_desc_id'] = translated
                record_updated = True
            
            # Add to updated records if any field was updated
            if record_updated:
                updated_records.append(updated_row)
        
        # Save complete dataset
        logger.info(f"💾 Saving complete dataset to: {OUTPUT_CSV}")
        df_updated.to_csv(OUTPUT_CSV, index=False)
        logger.info(f"✅ Saved {len(df_updated)} records to complete dataset")
        
        # Save only updated records
        if updated_records:
            df_updates = pd.DataFrame(updated_records)
            logger.info(f"💾 Saving {len(updated_records)} updated records to: {UPDATES_CSV}")
            df_updates.to_csv(UPDATES_CSV, index=False)
            logger.info(f"✅ Saved updated records")
        else:
            logger.info("ℹ️ No records were updated")
        
        # Final analysis
        logger.info("🔍 Final analysis...")
        final_missing_description_id = df_updated[df_updated['description_id'].isna() | (df_updated['description_id'] == '') | (df_updated['description_id'] == 'nan')].shape[0]
        final_missing_section_name_id = df_updated[df_updated['section_name_id'].isna() | (df_updated['section_name_id'] == '') | (df_updated['section_name_id'] == 'nan')].shape[0]
        final_missing_chapter_desc_id = df_updated[df_updated['chapter_desc_id'].isna() | (df_updated['chapter_desc_id'] == '') | (df_updated['chapter_desc_id'] == 'nan')].shape[0]
        final_missing_heading_desc_id = df_updated[df_updated['heading_desc_id'].isna() | (df_updated['heading_desc_id'] == '') | (df_updated['heading_desc_id'] == 'nan')].shape[0]
        final_missing_subheading_desc_id = df_updated[df_updated['subheading_desc_id'].isna() | (df_updated['subheading_desc_id'] == '') | (df_updated['subheading_desc_id'] == 'nan')].shape[0]
        
        final_total_missing = final_missing_description_id + final_missing_section_name_id + final_missing_chapter_desc_id + final_missing_heading_desc_id + final_missing_subheading_desc_id
        
        logger.info(f"📊 FINAL STATUS:")
        logger.info(f"   • Records updated: {len(updated_records):,}")
        logger.info(f"   • Remaining missing translations: {final_total_missing:,}")
        logger.info(f"   • Complete dataset: {OUTPUT_CSV}")
        logger.info(f"   • Updated records only: {UPDATES_CSV}")
        
        return True

def main():
    logger.info("🚀 Starting CSV translation filler...")
    
    filler = CSVTranslationFiller()
    
    if filler.fill_missing_translations():
        logger.info("🎉 Translation filling completed successfully!")
    else:
        logger.error("❌ Translation filling failed!")

if __name__ == "__main__":
    main()