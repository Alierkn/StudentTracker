-- Supabase Migration: Streak Kolonları Ekleme
-- Bu SQL'i Supabase Dashboard → SQL Editor'dan çalıştırın

-- 1. current_streak kolonu ekle
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'students' 
        AND column_name = 'current_streak'
    ) THEN
        ALTER TABLE students ADD COLUMN current_streak INTEGER DEFAULT 0;
        RAISE NOTICE '✅ current_streak kolonu eklendi';
    ELSE
        RAISE NOTICE 'ℹ️  current_streak kolonu zaten var';
    END IF;
END $$;

-- 2. longest_streak kolonu ekle
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'students' 
        AND column_name = 'longest_streak'
    ) THEN
        ALTER TABLE students ADD COLUMN longest_streak INTEGER DEFAULT 0;
        RAISE NOTICE '✅ longest_streak kolonu eklendi';
    ELSE
        RAISE NOTICE 'ℹ️  longest_streak kolonu zaten var';
    END IF;
END $$;

-- 3. last_study_date kolonu ekle
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'students' 
        AND column_name = 'last_study_date'
    ) THEN
        ALTER TABLE students ADD COLUMN last_study_date DATE;
        RAISE NOTICE '✅ last_study_date kolonu eklendi';
    ELSE
        RAISE NOTICE 'ℹ️  last_study_date kolonu zaten var';
    END IF;
END $$;

-- Kontrol sorgusu
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'students'
AND column_name IN ('current_streak', 'longest_streak', 'last_study_date')
ORDER BY column_name;

