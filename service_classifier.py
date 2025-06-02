import os
import time
import json
import shutil
import joblib
import pandas as pd

BASE_DIR = os.path.join(os.getcwd(), "data")
INCOMING_DIR = os.path.join(BASE_DIR, "incoming")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

MODEL_FILE = os.path.join(os.getcwd(), "model.pkl")

POLL_INTERVAL = 5

def load_model(path: str):
    """
    Загрузка сохранённой модели из файла model.pkl
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Модель не найдена по пути {path}")
    model = joblib.load(path)
    return model

def predict_batch(csv_path: str, model):
    """
    Читает CSV в DataFrame, запускает модель, возвращает список предсказаний.
    """
    df = pd.read_csv(csv_path)
    if "Survived" in df.columns:
        df = df.drop(columns=["Survived"], errors="ignore")
    predictions = model.predict(df)
    return predictions.tolist()

def process_file(filename: str, model):
    """
    Обрабатывает один CSV-файл, сохраняет результат в JSON и перемещает файл.
    """
    incoming_path = os.path.join(INCOMING_DIR, filename)
    processing_path = os.path.join(PROCESSING_DIR, filename)

    try:
        os.replace(incoming_path, processing_path)
        predictions = predict_batch(processing_path, model)

        batch_id = filename.replace(".csv", "")
        result = {
            "batch_id": batch_id,
            "predictions": predictions
        }

        result_filename = f"result_{batch_id}.json"
        result_path = os.path.join(RESULTS_DIR, result_filename)
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        final_processed_path = os.path.join(PROCESSED_DIR, filename)
        os.replace(processing_path, final_processed_path)

        print(f"Успешно обработан: {filename} → {result_filename}")

    except Exception as ex:
        error_path = os.path.join(ERRORS_DIR, filename)
        if os.path.exists(processing_path):
            os.replace(processing_path, error_path)
        elif os.path.exists(incoming_path):
            os.replace(incoming_path, error_path)

        print(f"Ошибка при обработке {filename}: {ex}")

def main():
    for directory in [INCOMING_DIR, PROCESSING_DIR, PROCESSED_DIR, ERRORS_DIR, RESULTS_DIR]:
        os.makedirs(directory, exist_ok=True)

    try:
        model = load_model(MODEL_FILE)
        print("Модель загружена из", MODEL_FILE)
    except Exception as e:
        print("Не удалось загрузить модель:", e)
        return

    print("Сервис классификации запущен. Ожидание файлов в папке:", INCOMING_DIR)
    while True:
        try:
            files = [f for f in os.listdir(INCOMING_DIR) if f.lower().endswith(".csv")]
            for filename in files:
                process_file(filename, model)
        except Exception as general_ex:
            print("Ошибка при сканировании incoming:", general_ex)

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
