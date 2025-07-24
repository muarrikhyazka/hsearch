import pandas as pd
import pypdf
import pdfplumber
import re
try:
    from googletrans import Translator
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False

def rearrange_harmonized_system():
    """
    Rearrange harmonized-system data by level structure:
    section|chapter|heading|subheading|chapter_desc|heading_desc|subheading_desc
    """
    df = pd.read_csv('data/harmonized-system.csv')
    
    # Create the reorganized structure
    result_data = []
    
    for _, row in df.iterrows():
        section = row['section']
        hscode = row['hscode']
        description = row['description']
        level = row['level']
        
        # Determine hierarchy based on level and hscode length
        if level == 2:  # Chapter level (01, 02, etc.)
            chapter = hscode
            heading = None
            subheading = None
            chapter_desc = description
            heading_desc = None
            subheading_desc = None
        elif level == 4:  # Heading level (0101, 0102, etc.)
            chapter = hscode[:2]
            heading = hscode
            subheading = None
            chapter_desc = None  # Will be filled from chapter data
            heading_desc = description
            subheading_desc = None
        elif level == 6:  # Subheading level (010121, 010129, etc.)
            chapter = hscode[:2]
            heading = hscode[:4]
            subheading = hscode
            chapter_desc = None  # Will be filled from chapter data
            heading_desc = None  # Will be filled from heading data
            subheading_desc = description
        
        result_data.append({
            'section': section,
            'chapter': chapter,
            'heading': heading,
            'subheading': subheading,
            'chapter_desc': chapter_desc,
            'heading_desc': heading_desc,
            'subheading_desc': subheading_desc
        })
    
    # Convert to DataFrame
    result_df = pd.DataFrame(result_data)
    
    # Fill missing descriptions by matching with parent levels
    chapter_descriptions = {}
    heading_descriptions = {}
    
    # First pass: collect chapter and heading descriptions
    for _, row in df.iterrows():
        if row['level'] == 2:
            chapter_descriptions[row['hscode']] = row['description']
        elif row['level'] == 4:
            heading_descriptions[row['hscode']] = row['description']
    
    # Second pass: fill missing descriptions
    for idx, row in result_df.iterrows():
        if pd.isna(row['chapter_desc']) and row['chapter'] in chapter_descriptions:
            result_df.at[idx, 'chapter_desc'] = chapter_descriptions[row['chapter']]
        if pd.isna(row['heading_desc']) and row['heading'] in heading_descriptions:
            result_df.at[idx, 'heading_desc'] = heading_descriptions[row['heading']]
    
    # Remove rows where all hierarchy fields are None (chapter level entries)
    result_df = result_df.dropna(subset=['subheading'])
    
    # Reorder columns as requested
    result_df = result_df[['section', 'chapter', 'heading', 'subheading', 'chapter_desc', 'heading_desc', 'subheading_desc']]
    
    # Save rearranged data
    result_df.to_csv('data/harmonized-system-rearranged.csv', index=False)
    print(f"Rearranged data saved with {len(result_df)} rows")
    
    return result_df

def merge_with_sections():
    """
    Merge rearranged harmonized-system data with sections.csv
    """
    # Load both datasets
    harmonized_df = pd.read_csv('data/harmonized-system-rearranged.csv')
    sections_df = pd.read_csv('data/sections.csv')
    
    # Clean BOM from sections.csv if present
    sections_df.columns = sections_df.columns.str.replace('﻿', '')
    
    # Ensure proper character formatting is maintained
    harmonized_df['chapter'] = harmonized_df['chapter'].astype(str).str.zfill(2)
    harmonized_df['heading'] = harmonized_df['heading'].astype(str).str.zfill(4) 
    harmonized_df['subheading'] = harmonized_df['subheading'].astype(str).str.zfill(6)
    
    # Merge on section
    merged_df = harmonized_df.merge(sections_df, on='section', how='left')
    
    # Rename the section name column for clarity
    merged_df = merged_df.rename(columns={'name': 'section_name'})
    
    # Save merged data
    merged_df.to_csv('data/harmonized-system-merged.csv', index=False)
    print(f"Merged data saved with {len(merged_df)} rows")
    
    return merged_df

def extract_pdf_data():
    """
    Extract tabular data from PDF with structure: no|hs_code|description
    """
    try:
        all_data = []
        
        with pdfplumber.open('data/output_selected_pages.pdf') as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text from the page
                text = page.extract_text()
                if not text:
                    continue
                
                # Split text into lines
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for lines that match the pattern: number + hs_code + description
                    # Pattern: starts with number, then 8-digit HS code, then description
                    match = re.match(r'^(\d+)\s+(\d{8})\s+(.+)$', line)
                    if match:
                        no = match.group(1)
                        hs_code = match.group(2)
                        description = match.group(3).strip()
                        
                        all_data.append({
                            'no': no,
                            'hs_code': hs_code,
                            'description': description
                        })
                    else:
                        # Try alternative pattern: number + 6-digit HS code + description
                        match = re.match(r'^(\d+)\s+(\d{6})\s+(.+)$', line)
                        if match:
                            no = match.group(1)
                            hs_code = match.group(2)
                            description = match.group(3).strip()
                            
                            all_data.append({
                                'no': no,
                                'hs_code': hs_code,
                                'description': description
                            })
        
        if all_data:
            # Convert to DataFrame
            pdf_df = pd.DataFrame(all_data)
            
            # Remove duplicates based on hs_code
            pdf_df = pdf_df.drop_duplicates(subset=['hs_code'])
            
            # Save extracted data
            pdf_df.to_csv('data/pdf-extracted.csv', index=False)
            print(f"PDF data extracted: {len(pdf_df)} HS codes from {len(pdf.pages)} pages")
            
            return pdf_df
        else:
            print("No tabular data found in PDF")
            return None
            
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def merge_with_pdf_data():
    """
    LEFT JOIN: PDF data on left, harmonized system data on right
    Match using first 6 chars of PDF hs_code with 6-char subheading
    """
    try:
        harmonized_df = pd.read_csv('data/harmonized-system-merged.csv')
        pdf_df = pd.read_csv('data/pdf-extracted.csv')
        
        if pdf_df is not None and len(pdf_df) > 0:
            # Prepare PDF data - remove trailing zeros and get meaningful part
            pdf_df['hs_code_clean'] = pdf_df['hs_code'].astype(str).str.rstrip('0')
            
            # Ensure subheading in harmonized data is string
            harmonized_df['subheading_str'] = harmonized_df['subheading'].astype(str)
            
            # LEFT JOIN: PDF data on LEFT, harmonized data on RIGHT
            merged_df = pdf_df.merge(
                harmonized_df,
                left_on='hs_code_clean',
                right_on='subheading_str', 
                how='left'
            )
            
            # Keep hs_code from PDF and clean up temporary columns
            merged_df = merged_df.drop(['hs_code_clean', 'subheading_str'], axis=1)
            
            # Fix formatting for chapter, heading, subheading columns
            for col in ['chapter', 'heading', 'subheading']:
                if col in merged_df.columns:
                    merged_df[col] = merged_df[col].fillna('').astype(str)
                    if col == 'chapter':
                        merged_df[col] = merged_df[col].apply(lambda x: x.zfill(2) if x and x != '' and x != 'nan' else '')
                    elif col == 'heading':
                        merged_df[col] = merged_df[col].apply(lambda x: x.zfill(4) if x and x != '' and x != 'nan' else '')
                    elif col == 'subheading':
                        merged_df[col] = merged_df[col].apply(lambda x: x.zfill(6) if x and x != '' and x != 'nan' else '')
            
            # Reorder columns to put PDF data first, then harmonized data
            column_order = [
                'no', 'hs_code', 'description',  # PDF columns
                'section', 'chapter', 'heading', 'subheading',  # Harmonized structure
                'chapter_desc', 'heading_desc', 'subheading_desc', 'section_name'  # Descriptions
            ]
            
            # Only include columns that exist
            available_columns = [col for col in column_order if col in merged_df.columns]
            merged_df = merged_df[available_columns]
            
            matches = merged_df['section'].notna().sum()
            print(f"PDF-led merge completed: {matches} matches found out of {len(pdf_df)} PDF records")
        else:
            print("No PDF data available for merge")
            return None
        
        # Save the result
        merged_df.to_csv('data/final-dataset.csv', index=False)
        print(f"Final dataset saved with {len(merged_df)} rows")
        
        return merged_df
    except Exception as e:
        print(f"Error merging with PDF data: {e}")
        return None

def translate_data():
    """
    Translate the final dataset using Google Translate API
    """
    if not TRANSLATE_AVAILABLE:
        print("Translation step skipped - Google Translate API not available")
        print("To enable translation, install googletrans: pip install googletrans==4.0.0rc1")
        return None
    
    try:
        translator = Translator()
        df = pd.read_csv('data/final-dataset.csv')
        
        # Translate description columns to Indonesian
        target_language = 'id'  # Indonesian language code
        
        # Add Indonesian translated columns
        translate_columns = ['description', 'chapter_desc', 'heading_desc', 'subheading_desc', 'section_name']
        for col in translate_columns:
            if col in df.columns:
                translated_col = f"{col}_id"  # Indonesian translation
                print(f"Translating {col} to Indonesian... ({df[col].notna().sum()} records)")
                
                def safe_translate(text):
                    try:
                        if pd.isna(text) or str(text).strip() == '' or str(text) == 'nan':
                            return ''
                        result = translator.translate(str(text), dest=target_language)
                        return result.text if result and result.text else str(text)
                    except Exception as e:
                        print(f"Translation error for '{text}': {e}")
                        return str(text)  # Return original text if translation fails
                
                df[translated_col] = df[col].apply(safe_translate)
        
        # Save translated data
        df.to_csv('data/final-dataset-translated.csv', index=False)
        print(f"Translated dataset saved with {len(df)} rows")
        
        return df
    except Exception as e:
        print(f"Error translating data: {e}")
        return None

if __name__ == "__main__":
    print("Step 1: Rearranging harmonized-system data...")
    rearrange_harmonized_system()
    
    print("\nStep 2: Merging with sections.csv...")
    merge_with_sections()
    
    print("\nStep 3: Extracting PDF data...")
    extract_pdf_data()
    
    print("\nStep 4: Merging with PDF data...")
    merge_with_pdf_data()
    
    print("\nStep 5: Translating data...")
    translate_data()
    
    print("\nData processing complete!")