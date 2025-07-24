import pandas as pd
import time
from googletrans import Translator

def translate_in_batches():
    """Translate dataset in smaller batches to avoid timeouts"""
    
    print("Loading dataset...")
    df = pd.read_csv('data/final-dataset.csv')
    print(f"Loaded {len(df)} records")
    
    translator = Translator()
    target_language = 'id'  # Indonesian
    
    # Columns to translate
    translate_columns = ['description', 'chapter_desc', 'heading_desc', 'subheading_desc', 'section_name']
    
    # Initialize Indonesian columns
    for col in translate_columns:
        if col in df.columns:
            df[f"{col}_id"] = ''
    
    # Process in batches of 100 records
    batch_size = 100
    total_batches = (len(df) - 1) // batch_size + 1
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(df))
        
        print(f"\nProcessing batch {batch_num + 1}/{total_batches} (rows {start_idx}-{end_idx-1})")
        
        # Process each column for this batch
        for col in translate_columns:
            if col not in df.columns:
                continue
                
            translated_col = f"{col}_id"
            
            for idx in range(start_idx, end_idx):
                text = df.at[idx, col]
                
                try:
                    if pd.isna(text) or str(text).strip() == '' or str(text) == 'nan':
                        df.at[idx, translated_col] = ''
                        continue
                    
                    # Translate
                    result = translator.translate(str(text), dest=target_language)
                    df.at[idx, translated_col] = result.text if result and result.text else str(text)
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Translation error for row {idx}, col {col}: {e}")
                    df.at[idx, translated_col] = str(text)  # Keep original
        
        # Save progress every 10 batches
        if (batch_num + 1) % 10 == 0:
            df.to_csv('data/final-dataset-translated-progress.csv', index=False)
            print(f"Progress saved after batch {batch_num + 1}")
    
    # Save final result
    df.to_csv('data/final-dataset-translated.csv', index=False)
    print(f"\nTranslation completed! Final dataset saved with {len(df)} rows")
    
    # Show sample translations
    print("\nSample translations:")
    for i in range(min(3, len(df))):
        if df.at[i, 'description_id']:
            print(f"EN: {df.at[i, 'description']}")
            print(f"ID: {df.at[i, 'description_id']}")
            print("---")
    
    return df

if __name__ == "__main__":
    translate_in_batches()