import pandas as pd
from googletrans import Translator
from tqdm import tqdm
import time
import json
import os
from datetime import datetime

class ChunkedTranslator:
    def __init__(self, chunk_size=10, delay=0.2, max_retries=3):
        self.translator = Translator()
        self.chunk_size = chunk_size
        self.delay = delay
        self.max_retries = max_retries
        self.progress_file = "translation_progress.json"
        
    def save_progress(self, progress_data):
        """Save translation progress to file"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def load_progress(self):
        """Load existing translation progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                print("Warning: Could not load progress file, starting fresh")
        return {}
    
    def translate_text_with_retry(self, text, target_lang='id'):
        """Translate text with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay)
                result = self.translator.translate(str(text), dest=target_lang)
                return result.text
            except Exception as e:
                print(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * 2)  # Longer delay on retry
                else:
                    print(f"Failed to translate after {self.max_retries} attempts: {text}")
                    return str(text)  # Return original text if all attempts fail
        return str(text)
    
    def translate_unique_values_chunked(self, unique_values, column_name):
        """Translate unique values in chunks with progress saving"""
        progress_data = self.load_progress()
        
        # Initialize progress for this column if not exists
        if column_name not in progress_data:
            progress_data[column_name] = {
                'completed': {},
                'last_chunk': 0,
                'total_values': len(unique_values)
            }
        
        completed_translations = progress_data[column_name]['completed']
        last_chunk = progress_data[column_name]['last_chunk']
        
        print(f"Translating {column_name}: {len(unique_values)} unique values")
        print(f"Resuming from chunk {last_chunk}, {len(completed_translations)} already completed")
        
        # Process in chunks
        chunks = [unique_values[i:i + self.chunk_size] for i in range(0, len(unique_values), self.chunk_size)]
        
        for chunk_idx, chunk in enumerate(tqdm(chunks[last_chunk:], 
                                              desc=f"Translating {column_name} chunks", 
                                              initial=last_chunk)):
            
            actual_chunk_idx = last_chunk + chunk_idx
            
            for value in tqdm(chunk, desc=f"Chunk {actual_chunk_idx + 1}", leave=False):
                # Skip if already translated
                if str(value) in completed_translations:
                    continue
                
                # Translate the value
                translated = self.translate_text_with_retry(value)
                completed_translations[str(value)] = translated
            
            # Update progress after each chunk
            progress_data[column_name]['last_chunk'] = actual_chunk_idx + 1
            progress_data[column_name]['completed'] = completed_translations
            self.save_progress(progress_data)
            
            print(f"Completed chunk {actual_chunk_idx + 1}/{len(chunks)} for {column_name}")
        
        return completed_translations

def translate_full_dataset(input_file, output_file, chunk_size=10):
    """
    Translate the full dataset with chunking and error recovery
    """
    print(f"Starting translation of {input_file}...")
    print(f"Chunk size: {chunk_size}")
    print(f"Output will be saved to: {output_file}")
    print("-" * 60)
    
    # Read the dataset
    print("Reading dataset...")
    df = pd.read_csv(input_file)
    print(f"Dataset loaded: {len(df)} rows")
    
    # Initialize translator
    translator = ChunkedTranslator(chunk_size=chunk_size)
    
    # Columns to translate
    columns_to_translate = [
        "section_name_en",
        "chapter_desc_en", 
        "heading_desc_en",
        "subheading_desc_en"
    ]
    
    # Create a copy for translations
    df_translated = df.copy()
    
    # Translate each column
    for column in columns_to_translate:
        if column not in df.columns:
            print(f"Warning: Column '{column}' not found in dataset")
            continue
        
        print(f"\n{'='*60}")
        print(f"TRANSLATING COLUMN: {column}")
        print(f"{'='*60}")
        
        # Get unique non-empty values
        unique_values = df[column].dropna().unique()
        unique_values = [val for val in unique_values if str(val).strip() != '']
        
        if len(unique_values) == 0:
            print(f"No values to translate for {column}")
            continue
        
        print(f"Found {len(unique_values)} unique values to translate")
        
        # Translate unique values in chunks
        translation_map = translator.translate_unique_values_chunked(unique_values, column)
        
        print(f"Translation completed for {column}")
        print(f"Successfully translated {len(translation_map)} values")
        
        # Apply translations to the dataframe
        target_col = f"{column}_id"
        df_translated[target_col] = df_translated[column].map(translation_map)
        
        # Fill any missing mappings with original value
        mask = df_translated[target_col].isna() & df_translated[column].notna()
        df_translated.loc[mask, target_col] = df_translated.loc[mask, column]
    
    # Save intermediate result
    intermediate_file = output_file.replace('.csv', '_translated_only.csv')
    print(f"\nSaving intermediate translated result to {intermediate_file}...")
    df_translated.to_csv(intermediate_file, index=False)
    
    # Apply upward filling to all hierarchy columns
    print("\nApplying upward filling to all hierarchy columns...")
    
    all_columns_to_fill = [
        'section', 'chapter', 'heading', 'subheading',
        'section_name_en', 'chapter_desc_en', 'heading_desc_en', 'subheading_desc_en',
        'section_name_id', 'chapter_desc_id', 'heading_desc_id', 'subheading_desc_id'
    ]
    
    for col in all_columns_to_fill:
        if col not in df_translated.columns:
            continue
            
        filled_count = 0
        for idx in tqdm(range(len(df_translated)), desc=f"Filling {col}"):
            current_value = df_translated.at[idx, col]
            
            is_empty = (pd.isna(current_value) or 
                       str(current_value).strip() == '' or 
                       current_value == '' or
                       str(current_value).lower() == 'nan')
            
            if is_empty:
                for look_idx in range(idx - 1, -1, -1):
                    upward_value = df_translated.at[look_idx, col]
                    
                    upward_is_valid = (not pd.isna(upward_value) and 
                                     str(upward_value).strip() != '' and
                                     str(upward_value).lower() != 'nan')
                    
                    if upward_is_valid:
                        df_translated.at[idx, col] = upward_value
                        filled_count += 1
                        break
        
        print(f"  Filled {filled_count} empty cells in {col}")
    
    # Fix digit formatting for heading and subheading
    print("\nFixing digit formatting...")
    
    if 'heading' in df_translated.columns:
        print("Formatting heading to 4 digits...")
        for idx in tqdm(range(len(df_translated)), desc="Formatting heading"):
            if not pd.isna(df_translated.at[idx, 'heading']):
                heading_str = str(int(float(df_translated.at[idx, 'heading'])))
                df_translated.at[idx, 'heading'] = heading_str.zfill(4)
    
    if 'subheading' in df_translated.columns:
        print("Formatting subheading to 6 digits...")
        for idx in tqdm(range(len(df_translated)), desc="Formatting subheading"):
            if not pd.isna(df_translated.at[idx, 'subheading']):
                subheading_str = str(int(float(df_translated.at[idx, 'subheading'])))
                df_translated.at[idx, 'subheading'] = subheading_str.zfill(6)
    
    # Save final result
    print(f"\nSaving final result to {output_file}...")
    df_translated.to_csv(output_file, index=False)
    
    # Clean up progress file
    if os.path.exists(translator.progress_file):
        os.remove(translator.progress_file)
        print("Cleaned up progress file")
    
    print(f"\n{'='*60}")
    print("TRANSLATION COMPLETED SUCCESSFULLY!")
    print(f"Final dataset saved to: {output_file}")
    print(f"Total rows processed: {len(df_translated)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    return df_translated

if __name__ == "__main__":
    input_file = "data/final-dataset.csv"
    output_file = "data/final-dataset-translated-complete.csv"
    chunk_size = 10  # Adjust based on API rate limits
    
    translate_full_dataset(input_file, output_file, chunk_size)