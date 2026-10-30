# AI Dual-Mode Quiz Generator Engine

Sistem backend FastAPI untuk pembuatan kuis otomatis (Objektif A-E dan Essai) dari unggahan PDF.

## Struktur Project

```text
bimbel-mada-backend/
├── app/
│   ├── __init__.py
│   └── main.py              <-- File utama program FastAPI
├── requirements.txt         <-- Dependensi pustaka
└── README.md                <-- Petunjuk penggunaan
```

## Panduan Penempatan & Cara Menjalankan

1. **Ekstrak file ZIP** ke dalam direktori project backend Anda.
2. **Install dependency**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan server**:
   ```bash
   uvicorn app.main:app --reload
   ```
4. **Buka dokumentasi Swagger UI**:
   Buka browser ke `http://127.0.0.1:8000/docs`
