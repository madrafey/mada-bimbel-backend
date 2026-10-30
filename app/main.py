from enum import Enum
import json
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from pydantic import BaseModel, Field
from pypdf import PdfReader
import google.generativeai as genai

app = FastAPI(
    title="AI Dual-Mode Quiz Generator Engine",
    description="Sistem Generator Soal Otomatis (Objektif & Essai) dari File PDF",
    version="1.0.0"
)

class ModeKuis(str, Enum):
    OBJEKTIF = "objektif"
    ESSAI = "essai"

# --- Skema Data Soal Objektif (Pilihan Ganda A-E) ---
class OpsiJawaban(BaseModel):
    A: str
    B: str
    C: str
    D: str
    E: str

class SoalObjektifItem(BaseModel):
    no: int
    pertanyaan: str
    opsi: OpsiJawaban
    kunci_jawaban: str = Field(description="Huruf opsi jawaban yang benar (A/B/C/D/E)")
    pembahasan: str

class QuizObjektifResponse(BaseModel):
    judul_kuis: str
    mode: ModeKuis = ModeKuis.OBJEKTIF
    total_soal: int
    durasi_menit: int
    daftar_soal: List[SoalObjektifItem]

# --- Skema Data Soal Essai ---
class SoalEssaiItem(BaseModel):
    no: int
    pertanyaan: str
    kata_kunci: List[str] = Field(description="Kata kunci utama yang wajib ada dalam jawaban mahasiswa")
    jawaban_ideal: str = Field(description="Contoh jawaban/pembahasan lengkap yang ideal")
    bobot_nilai: int = Field(description="Bobot poin maksimal untuk soal ini (misal: 10 atau 20)")

class QuizEssaiResponse(BaseModel):
    judul_kuis: str
    mode: ModeKuis = ModeKuis.ESSAI
    total_soal: int
    durasi_menit: int
    daftar_soal: List[SoalEssaiItem]

# --- Helper Reader PDF ---
def extract_text_from_pdf(pdf_file) -> str:
    try:
        reader = PdfReader(pdf_file)
        text = "".join([page.extract_text() or "" for page in reader.pages])
        return text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal membaca PDF: {str(e)}"
        )

# --- Endpoint Utama ---
@app.post("/api/v1/generate-quiz")
async def generate_quiz(
    file: UploadFile = File(...),
    api_key: str = Form(..., description="Gemini API Key"),
    judul_kuis: str = Form("Kuis Evaluasi Modul"),
    mode: ModeKuis = Form(ModeKuis.OBJEKTIF, description="Pilih 'objektif' atau 'essai'"),
    jumlah_soal: int = Form(10, description="Maksimal 50 soal"),
    durasi_menit: int = Form(90, description="Maksimal 90 menit")
):
    # Setup API Key
    genai.configure(api_key=api_key)

    # Validasi input
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File harus berformat PDF.")
    if not (1 <= jumlah_soal <= 50):
        raise HTTPException(status_code=400, detail="Jumlah soal harus berada pada rentang 1 hingga 50.")
    if not (5 <= durasi_menit <= 90):
        raise HTTPException(status_code=400, detail="Durasi pengerjaan harus 5 hingga 90 menit.")

    pdf_text = extract_text_from_pdf(file.file)
    if len(pdf_text) < 100:
        raise HTTPException(status_code=400, detail="Isi PDF terlalu singkat atau tidak terbaca.")

    # Pengkondisian Prompt & Schema berdasarkan Mode
    if mode == ModeKuis.OBJEKTIF:
        target_schema = QuizObjektifResponse
        prompt = f"""
        Buatkan {jumlah_soal} soal pilihan ganda (A, B, C, D, E) dari materi berikut.
        Setiap soal wajib memiliki 5 opsi, 1 kunci jawaban benar, dan pembahasan singkat.
        Materi: """{pdf_text[:15000]}"""
        """
    else:  # Mode Essai
        target_schema = QuizEssaiResponse
        prompt = f"""
        Buatkan {jumlah_soal} soal essai/uraian mendalam dari materi berikut.
        Untuk setiap soal, sertakan daftar 'kata_kunci' penting yang harus ada pada jawaban mahasiswa,
        'jawaban_ideal' sebagai acuan penilaian, dan tentukan 'bobot_nilai' proporsional (total bobot seluruh soal = 100).
        Materi: """{pdf_text[:15000]}"""
        """

    # Eksekusi AI Gemini
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=target_schema,
                temperature=0.3
            )
        )
        
        quiz_data = json.loads(response.text)
        quiz_data["judul_kuis"] = judul_kuis
        quiz_data["total_soal"] = len(quiz_data["daftar_soal"])
        quiz_data["durasi_menit"] = durasi_menit
        quiz_data["mode"] = mode.value
        
        return quiz_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses AI: {str(e)}")
