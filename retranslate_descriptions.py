#!/usr/bin/env python3
"""
Re-translate all description_id entries from description_en to ensure
complete and consistent Indonesian translations.
"""

import pandas as pd
import sys

def create_comprehensive_translation_dict():
    """Create comprehensive English to Indonesian translation dictionary for HS codes"""
    return {
        # Animals and livestock
        "live": "hidup",
        "animals": "hewan",
        "cattle": "sapi",
        "buffalo": "kerbau", 
        "horses": "kuda",
        "horse": "kuda",
        "asses": "keledai",
        "mules": "bagal",
        "hinnies": "hinnies",
        "swine": "babi",
        "sheep": "domba",
        "goats": "kambing",
        "goat": "kambing",
        "bovine": "sapi",
        "pigs": "babi",
        "pig": "babi",
        "oxen": "lembu",
        "male": "jantan",
        "female": "betina",
        "insects": "serangga",
        "bees": "lebah",
        
        # Breeding and characteristics
        "pure-bred": "ras murni",
        "breeding": "pembiakan",
        "animals": "hewan",
        "weighing": "dengan berat",
        "less than": "kurang dari",
        "more than": "lebih dari",
        "other than": "selain",
        "including": "termasuk",
        "excluding": "tidak termasuk",
        
        # Meat and food products
        "meat": "daging",
        "carcasses": "karkas",
        "half carcasses": "setengah karkas",
        "cuts": "potongan",
        "bone": "tulang",
        "boneless": "tanpa tulang",
        "with bone in": "dengan tulang",
        "bone in": "dengan tulang",
        "offal": "jeroan",
        "edible offal": "jeroan yang dapat dimakan",
        "edible": "dapat dimakan",
        "tongues": "lidah",
        "livers": "hati",
        "liver": "hati",
        "shoulders": "bahu",
        "hams": "ham",
        "cuts thereof": "potongan darinya",
        "thereof": "darinya",
        
        # States and conditions
        "fresh": "segar",
        "chilled": "dingin",
        "frozen": "beku",
        "dried": "kering",
        "salted": "asin",
        "smoked": "asap",
        "cooked": "matang",
        "raw": "mentah",
        
        # Conjunctions and prepositions
        "and": "dan",
        "or": "atau",
        "of": "dari",
        "in": "dalam",
        "with": "dengan",
        "without": "tanpa",
        "than": "dari",
        "but": "tetapi",
        "except": "kecuali",
        "for": "untuk",
        "to": "ke",
        "from": "dari",
        "by": "oleh",
        "at": "di",
        "on": "pada",
        
        # Quantities and measures
        "kg": "kg",
        "gram": "gram",
        "kilogram": "kilogram",
        "ton": "ton",
        "piece": "potong",
        "pieces": "potongan",
        "each": "setiap",
        "per": "per",
        "unit": "unit",
        
        # Technical terms
        "chapter": "bab",
        "subheading": "sub judul",
        "heading": "judul",
        "section": "bagian",
        "item": "item",
        "number": "nomor",
        "code": "kode",
        "n.e.c.": "t.d.k.",  # tidak dijelaskan klasifikasi
        "not elsewhere classified": "tidak diklasifikasikan di tempat lain",
        "not elsewhere specified": "tidak dijelaskan di tempat lain",
        "nes": "lainnya",
        "nos": "tidak disebutkan secara khusus",
        
        # Common phrases
        "live animals": "hewan hidup",
        "animal products": "produk hewani",
        "meat products": "produk daging",
        "dairy products": "produk susu",
        "food products": "produk makanan",
        "fresh or chilled": "segar atau dingin",
        "chilled or frozen": "dingin atau beku",
        "fresh, chilled or frozen": "segar, dingin atau beku",
        "other than": "selain",
    }

def translate_text(text, translation_dict):
    """Translate English text to Indonesian using dictionary with proper word order"""
    if pd.isna(text) or text.strip() == '':
        return text
    
    import re
    
    # Convert to string and clean
    original = str(text).strip().lower()
    translated = original
    
    # Handle specific patterns with correct Indonesian word order
    patterns = [
        # Fix "live + animal" to "animal + hidup" - more comprehensive
        (r'\blive\s+(horses?|cattle|buffalo|asses?|mules?|hinnies|swine|sheep|goats?|oxen)', 
         lambda m: f"{translation_dict.get(m.group(1), m.group(1))} hidup"),
        
        # Fix "live bovine animals" specifically
        (r'\blive\s+bovine\s+animals?',
         "hewan sapi hidup"),
        
        # Fix "live animals" generally
        (r'\blive\s+animals?',
         "hewan hidup"),
        
        # Fix "adjective + noun" to "noun + adjective" for common patterns
        (r'\b(male|female)\s+(cattle|buffalo|horses?|goats?|sheep|swine|animals?)',
         lambda m: f"{translation_dict.get(m.group(2), m.group(2))} {translation_dict.get(m.group(1), m.group(1))}"),
        
        # Fix "pure-bred breeding animals" 
        (r'\bpure-bred\s+breeding\s+animals?',
         "hewan pembiakan ras murni"),
        
        # Fix weight descriptions
        (r'\bweighing\s+(less\s+than|more\s+than|\d+\s*kg)',
         lambda m: f"dengan berat {m.group(1)}"),
        
        # Fix "live" at the beginning when not caught by other patterns
        (r'^\blive\s+',
         ""),
    ]
    
    # Apply pattern-based translations first
    for pattern, replacement in patterns:
        if callable(replacement):
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
        else:
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_translations = sorted(translation_dict.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Apply remaining word-by-word translations
    for english, indonesian in sorted_translations:
        # Skip if already handled by patterns above
        if english in ['live', 'male', 'female', 'pure-bred', 'breeding', 'weighing']:
            continue
            
        # Case insensitive replacement with word boundaries
        pattern = r'\b' + re.escape(english) + r'\b'
        translated = re.sub(pattern, indonesian, translated, flags=re.IGNORECASE)
    
    # Clean up extra spaces and formatting
    translated = re.sub(r'\s+', ' ', translated).strip()
    translated = translated.replace(' ,', ',').replace(' ;', ';')
    
    # Fix common Indonesian grammar issues
    translated = re.sub(r'\bhidup\s+(kuda|sapi|kerbau|keledai|bagal|babi|domba|kambing)', r'\1 hidup', translated)
    translated = re.sub(r'\bjantan\s+(sapi|kerbau|kuda|kambing|domba)', r'\1 jantan', translated)
    translated = re.sub(r'\bbetina\s+(sapi|kerbau|kuda|kambing|domba)', r'\1 betina', translated)
    
    return translated

def main():
    input_file = "data/final-dataset-retranslated.csv"
    output_file = "data/final-dataset-retranslated.csv"
    
    print("HS Code Description Re-translation Tool")
    print("=" * 45)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()
    
    # Load data
    print("Loading dataset...")
    try:
        df = pd.read_csv(input_file, dtype={
            'hs_code': str,
            'section': str, 
            'chapter': str,
            'heading': str,
            'subheading': str
        })
        print(f"Loaded {len(df)} records")
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    # Show sample before translation
    print("\nSample before re-translation:")
    for i in range(min(5, len(df))):
        print(f"  {i+1}. EN: {df.iloc[i]['description_en']}")
        print(f"     ID: {df.iloc[i]['description_id']}")
        print()
    
    # Create translation dictionary
    print("Creating translation dictionary...")
    translation_dict = create_comprehensive_translation_dict()
    print(f"Loaded {len(translation_dict)} translation mappings")
    
    # Re-translate all description_id based on description_en
    print("\nRe-translating all descriptions...")
    retranslated_count = 0
    
    for idx, row in df.iterrows():
        original_en = row['description_en']
        original_id = row['description_id']
        
        # Translate from English
        new_translation = translate_text(original_en, translation_dict)
        
        # Update the description_id
        df.at[idx, 'description_id'] = new_translation
        retranslated_count += 1
        
        # Show progress every 1000 records
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1} records...")
    
    print(f"Re-translated {retranslated_count} descriptions")
    
    # Show sample after translation
    print("\nSample after re-translation:")
    for i in range(min(5, len(df))):
        print(f"  {i+1}. EN: {df.iloc[i]['description_en']}")
        print(f"     ID: {df.iloc[i]['description_id']}")
        print()
    
    # Save re-translated data
    print(f"Saving re-translated dataset to {output_file}...")
    try:
        df.to_csv(output_file, index=False)
        print("File saved successfully!")
        
        print(f"\nRe-translation completed!")
        print(f"Re-translated dataset: {output_file}")
        print("\nNext steps:")
        print("1. Review the output file")
        print("2. Replace the standardized file if satisfied")  
        print("3. Reimport data to update database")
        
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    main()