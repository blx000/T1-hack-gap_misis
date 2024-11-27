from fastapi import FastAPI, File, UploadFile, HTTPException
import pandas as pd
import os
import json
from collections import Counter
import PyPDF2
from base import User


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
async def create_user(username: str, password: str, db: SessionLocal = next(get_db())):
    # Проверка на существование пользователя
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Создание нового пользователя
    new_user = User(username=username, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "username": new_user.username}



@app.get("/users/{user_id}")
async def read_user(user_id: str, db: SessionLocal = next(get_db())):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user.id, "username": user.username}





OUTPUT_DIR = "output_json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_most_common_word_pdf(text):
    words = text.split()
    if not words:
        return None
    word_counts = Counter(words)
    most_common_elements = [word_counts.most_common()[0], word_counts.most_common()[1], word_counts.most_common()[2]]
    return most_common_elements


def get_most_common_word_csv(text):
    words = text.split(";")
    if not words:
        return None
    word_counts = Counter(words)
    most_common_elements = [word_counts.most_common()[1], word_counts.most_common()[2], word_counts.most_common()[3]]
    return most_common_elements

@app.post("/convert-csv-to-json/")
async def convert_csv_to_json(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        return {"error": "File must be a CSV."}

    # Чтение CSV файла в DataFrame
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return {"error": str(e)}

    # Получаем номер файла (например, количество файлов в папке + 1)
    file_count = len(os.listdir(OUTPUT_DIR)) + 1

    # Подготовка данных для сохранения в JSON формате
    json_data = {
        "id": file_count,
        "data": df.to_dict(orient='records')  # Конвертация DataFrame в список словарей
    }

    # Объединяем все текстовые данные для поиска самого частого слова
    all_text = ' '.join(df.astype(str).values.flatten())
    most_common_word = get_most_common_word_csv(all_text)
    
    json_data["connect"] = most_common_word

    # Сохранение JSON файла
    json_filename = f"file_{file_count}.json"
    json_filepath = os.path.join(OUTPUT_DIR, json_filename)

    try:
        with open(json_filepath, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
    except Exception as e:
        return {"error": str(e)}

    return {"filename": json_filename, "message": "CSV file converted successfully!"}

@app.post("/convert-pdf-to-json/")
async def convert_pdf_to_json(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        return {"error": "File must be a PDF."}

    # Чтение PDF файла
    try:
        pdf_reader = PyPDF2.PdfReader(file.file)
        all_text = ""
        for page in pdf_reader.pages:
            all_text += page.extract_text() + " "
    except Exception as e:
        return {"error": str(e)}

    # Получаем номер файла (например, количество файлов в папке + 1)
    file_count = len(os.listdir(OUTPUT_DIR)) + 1

    # Подготовка данных для сохранения в JSON формате
    json_data = {
        "id": file_count,
        "data": all_text.strip()  # Сохраняем текст как строку
    }

    # Поиск самого частого слова
    most_common_word = get_most_common_word_pdf(all_text)
    
    json_data["connect"] = most_common_word

    # Сохранение JSON файла
    json_filename = f"file_{file_count}.json"
    json_filepath = os.path.join(OUTPUT_DIR, json_filename)

    try:
        with open(json_filepath, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
    except Exception as e:
        return {"error": str(e)}

    return {"filename": json_filename, "message": "PDF file converted successfully!"}