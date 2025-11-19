#!/bin/bash

# Öğrenci Takip Sistemi Başlatma Scripti

cd "$(dirname "$0")"

# Virtual environment'ı aktif et
source venv/bin/activate

# Uygulamayı başlat
python student_tracker.py

