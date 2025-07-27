-- SQL script to fill missing Indonesian translations
-- This script only updates empty/null fields for efficiency

-- First, let's check what's missing
SELECT 
    'Missing analysis' as analysis_type,
    SUM(CASE WHEN description_id IS NULL OR description_id = '' OR description_id = 'nan' THEN 1 ELSE 0 END) as missing_description_id,
    SUM(CASE WHEN section_name_id IS NULL OR section_name_id = '' OR section_name_id = 'nan' THEN 1 ELSE 0 END) as missing_section_name_id,
    SUM(CASE WHEN chapter_desc_id IS NULL OR chapter_desc_id = '' OR chapter_desc_id = 'nan' THEN 1 ELSE 0 END) as missing_chapter_desc_id,
    SUM(CASE WHEN heading_desc_id IS NULL OR heading_desc_id = '' OR heading_desc_id = 'nan' THEN 1 ELSE 0 END) as missing_heading_desc_id,
    SUM(CASE WHEN subheading_desc_id IS NULL OR subheading_desc_id = '' OR subheading_desc_id = 'nan' THEN 1 ELSE 0 END) as missing_subheading_desc_id,
    COUNT(*) as total_records
FROM hs_codes;

-- Update missing section_name_id based on English section_name
UPDATE hs_codes 
SET section_name_id = CASE 
    WHEN section_name ILIKE '%live animals%' THEN 'hewan hidup; produk hewani'
    WHEN section_name ILIKE '%vegetable products%' THEN 'produk nabati'
    WHEN section_name ILIKE '%animal or vegetable fats%' THEN 'lemak hewani atau nabati dan minyak'
    WHEN section_name ILIKE '%prepared foodstuffs%' THEN 'makanan olahan; minuman, spirits dan cuka; tembakau'
    WHEN section_name ILIKE '%mineral products%' THEN 'produk mineral'
    WHEN section_name ILIKE '%products of the chemical%' THEN 'produk industri kimia atau industri terkait'
    WHEN section_name ILIKE '%plastics and articles%' THEN 'plastik dan artikel plastik; karet dan artikel karet'
    WHEN section_name ILIKE '%raw hides and skins%' THEN 'kulit mentah dan kulit samak'
    WHEN section_name ILIKE '%wood and articles%' THEN 'kayu dan artikel kayu; arang kayu'
    WHEN section_name ILIKE '%pulp of wood%' THEN 'pulp kayu atau bahan berserat selulosa lainnya'
    WHEN section_name ILIKE '%textiles and textile%' THEN 'tekstil dan artikel tekstil'
    WHEN section_name ILIKE '%footwear, headgear%' THEN 'alas kaki, tutup kepala, payung'
    WHEN section_name ILIKE '%articles of stone%' THEN 'artikel batu, plaster, semen, asbes'
    WHEN section_name ILIKE '%natural or cultured pearls%' THEN 'mutiara alami atau budidaya, batu mulia'
    WHEN section_name ILIKE '%base metals%' THEN 'logam dasar dan artikel logam dasar'
    WHEN section_name ILIKE '%machinery and mechanical%' THEN 'mesin dan peralatan mekanik; bagian elektrik'
    WHEN section_name ILIKE '%vehicles, aircraft%' THEN 'kendaraan, pesawat terbang, kapal'
    WHEN section_name ILIKE '%optical, photographic%' THEN 'instrumen optik, fotografi, sinematografi'
    WHEN section_name ILIKE '%arms and ammunition%' THEN 'senjata dan amunisi; bagian dan aksesori'
    WHEN section_name ILIKE '%miscellaneous%' THEN 'artikel manufaktur lain-lain'
    WHEN section_name ILIKE '%works of art%' THEN 'karya seni, barang koleksi dan barang antik'
    ELSE section_name
END,
updated_at = NOW()
WHERE (section_name_id IS NULL OR section_name_id = '' OR section_name_id = 'nan')
AND section_name IS NOT NULL AND section_name != '';

-- Update missing chapter_desc_id with common translations
UPDATE hs_codes 
SET chapter_desc_id = CASE 
    WHEN chapter_desc ILIKE '%animals; live%' THEN 'Hewan; hidup'
    WHEN chapter_desc ILIKE '%meat and edible%' THEN 'Daging dan jeroan yang dapat dimakan'
    WHEN chapter_desc ILIKE '%fish and crustaceans%' THEN 'Ikan dan krustasea, moluska dan invertebrata air lainnya'
    WHEN chapter_desc ILIKE '%dairy produce%' THEN 'Produk susu; telur unggas; madu alami'
    WHEN chapter_desc ILIKE '%products of animal origin%' THEN 'Produk asal hewan, tidak diklasifikasikan di tempat lain'
    WHEN chapter_desc ILIKE '%live trees%' THEN 'Pohon hidup dan tanaman lain; umbi, akar dan sejenisnya'
    WHEN chapter_desc ILIKE '%edible vegetables%' THEN 'Sayuran yang dapat dimakan dan akar dan umbi tertentu'
    WHEN chapter_desc ILIKE '%edible fruit%' THEN 'Buah dan kacang yang dapat dimakan; kulit jeruk atau melon'
    WHEN chapter_desc ILIKE '%coffee, tea%' THEN 'Kopi, teh, maté dan rempah-rempah'
    WHEN chapter_desc ILIKE '%cereals%' THEN 'Sereal'
    WHEN chapter_desc ILIKE '%products of the milling%' THEN 'Produk penggilingan; malt; pati; inulin; gluten gandum'
    WHEN chapter_desc ILIKE '%oil seeds%' THEN 'Biji berminyak dan buah berminyak; biji, benih dan buah lain-lain'
    WHEN chapter_desc ILIKE '%lac; gums, resins%' THEN 'Lak; getah, resin dan getah nabati lainnya'
    WHEN chapter_desc ILIKE '%vegetable plaiting%' THEN 'Bahan anyaman nabati; produk nabati lainnya'
    ELSE chapter_desc
END,
updated_at = NOW()
WHERE (chapter_desc_id IS NULL OR chapter_desc_id = '' OR chapter_desc_id = 'nan')
AND chapter_desc IS NOT NULL AND chapter_desc != '';

-- Update missing heading_desc_id for common headings
UPDATE hs_codes 
SET heading_desc_id = CASE 
    WHEN heading_desc ILIKE '%horses, asses, mules%' THEN 'Kuda, keledai, bagal dan hinny; hidup'
    WHEN heading_desc ILIKE '%bovine animals; live%' THEN 'Hewan sapi; hidup'
    WHEN heading_desc ILIKE '%swine; live%' THEN 'Babi; hidup'
    WHEN heading_desc ILIKE '%sheep and goats; live%' THEN 'Domba dan kambing; hidup'
    WHEN heading_desc ILIKE '%poultry%' THEN 'Unggas, yaitu ayam domestik, bebek, angsa, kalkun dan guinea fowl; hidup'
    WHEN heading_desc ILIKE '%animals; live%' THEN 'Hewan lain; hidup'
    WHEN heading_desc ILIKE '%meat of bovine%' THEN 'Daging sapi, segar atau dingin'
    WHEN heading_desc ILIKE '%meat of swine%' THEN 'Daging babi, segar, dingin atau beku'
    WHEN heading_desc ILIKE '%meat of sheep%' THEN 'Daging domba atau kambing, segar, dingin atau beku'
    WHEN heading_desc ILIKE '%meat and edible offal%' THEN 'Daging dan jeroan yang dapat dimakan'
    ELSE heading_desc
END,
updated_at = NOW()
WHERE (heading_desc_id IS NULL OR heading_desc_id = '' OR heading_desc_id = 'nan')
AND heading_desc IS NOT NULL AND heading_desc != '';

-- Update missing subheading_desc_id for common subheadings
UPDATE hs_codes 
SET subheading_desc_id = CASE 
    WHEN subheading_desc ILIKE '%horses; live, pure-bred breeding%' THEN 'Kuda; hidup, pembibitan murni'
    WHEN subheading_desc ILIKE '%horses; live, other than pure-bred%' THEN 'Kuda; hidup, selain hewan pembibitan murni'
    WHEN subheading_desc ILIKE '%asses; live%' THEN 'Keledai; hidup'
    WHEN subheading_desc ILIKE '%mules and hinnies; live%' THEN 'Bagal dan hinny; hidup'
    WHEN subheading_desc ILIKE '%cattle; live, pure-bred breeding%' THEN 'Sapi; hidup, pembibitan murni'
    WHEN subheading_desc ILIKE '%cattle; live, other than pure-bred%' THEN 'Sapi; hidup, selain pembibitan murni'
    WHEN subheading_desc ILIKE '%buffalo; live%' THEN 'Kerbau; hidup'
    WHEN subheading_desc ILIKE '%swine; live, pure-bred breeding%' THEN 'Babi; hidup, pembibitan murni'
    WHEN subheading_desc ILIKE '%swine; live, weighing less than 50kg%' THEN 'Babi; hidup, berat kurang dari 50kg'
    WHEN subheading_desc ILIKE '%swine; live, weighing 50kg or more%' THEN 'Babi; hidup, berat 50kg atau lebih'
    ELSE subheading_desc
END,
updated_at = NOW()
WHERE (subheading_desc_id IS NULL OR subheading_desc_id = '' OR subheading_desc_id = 'nan')
AND subheading_desc IS NOT NULL AND subheading_desc != '';

-- Fill missing description_id by copying from description_en as fallback
-- This should be done with proper translation, but as a temporary measure
UPDATE hs_codes 
SET description_id = description_en,
    updated_at = NOW()
WHERE (description_id IS NULL OR description_id = '' OR description_id = 'nan')
AND description_en IS NOT NULL AND description_en != '';

-- Final check - show remaining missing translations
SELECT 
    'Final analysis' as analysis_type,
    SUM(CASE WHEN description_id IS NULL OR description_id = '' OR description_id = 'nan' THEN 1 ELSE 0 END) as missing_description_id,
    SUM(CASE WHEN section_name_id IS NULL OR section_name_id = '' OR section_name_id = 'nan' THEN 1 ELSE 0 END) as missing_section_name_id,
    SUM(CASE WHEN chapter_desc_id IS NULL OR chapter_desc_id = '' OR chapter_desc_id = 'nan' THEN 1 ELSE 0 END) as missing_chapter_desc_id,
    SUM(CASE WHEN heading_desc_id IS NULL OR heading_desc_id = '' OR heading_desc_id = 'nan' THEN 1 ELSE 0 END) as missing_heading_desc_id,
    SUM(CASE WHEN subheading_desc_id IS NULL OR subheading_desc_id = '' OR subheading_desc_id = 'nan' THEN 1 ELSE 0 END) as missing_subheading_desc_id,
    COUNT(*) as total_records
FROM hs_codes;