import os
import time
import uuid

from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

INCOMING_DIR = os.path.join(os.getcwd(), "data", "incoming")
os.makedirs(INCOMING_DIR, exist_ok=True)

EXPECTED_EMBARKED_COLS = ["Embarked_C", "Embarked_Q", "Embarked_S"]
EXPECTED_PCLASS_COLS   = ["Pclass_1", "Pclass_2", "Pclass_3"]

def preprocess_titanic_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = df.drop(columns=["PassengerId", "Name", "Ticket", "Cabin"], errors="ignore")

    df["Age"] = df["Age"].fillna(df["Age"].median())
    df["Fare"] = df["Fare"].fillna(df["Fare"].median())
    df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])

    df["Sex"] = df["Sex"].map({"male": 1, "female": 0}).astype(int)

    embarked_dummies = pd.get_dummies(df["Embarked"], prefix="Embarked")
    for col in EXPECTED_EMBARKED_COLS:
        if col not in embarked_dummies.columns:
            embarked_dummies[col] = 0
    embarked_dummies = embarked_dummies[EXPECTED_EMBARKED_COLS]
    df = pd.concat([df.drop(columns=["Embarked"]), embarked_dummies], axis=1)

    pclass_dummies = pd.get_dummies(df["Pclass"].astype(str), prefix="Pclass")
    for col in EXPECTED_PCLASS_COLS:
        if col not in pclass_dummies.columns:
            pclass_dummies[col] = 0
    pclass_dummies = pclass_dummies[EXPECTED_PCLASS_COLS]
    df = pd.concat([df.drop(columns=["Pclass"]), pclass_dummies], axis=1)

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype("category").cat.codes

    return df

def save_preprocessed_csv(df: pd.DataFrame, batch_id: str) -> str:
    filename_tmp = f"batch_{batch_id}.csv.tmp"
    path_tmp = os.path.join(INCOMING_DIR, filename_tmp)
    df.to_csv(path_tmp, index=False)
    filename_final = f"batch_{batch_id}.csv"
    path_final = os.path.join(INCOMING_DIR, filename_final)
    os.replace(path_tmp, path_final)
    return path_final

@app.route("/preprocess", methods=["POST"])
def preprocess_endpoint():
    raw_data = request.get_json()
    if not isinstance(raw_data, list):
        return jsonify({"error": "Ожидается массив JSON-объектов"}), 400

    df = pd.DataFrame(raw_data)
    df_preprocessed = preprocess_titanic_dataframe(df)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:8]
    batch_id = f"{timestamp}_{unique_suffix}"

    saved_path = save_preprocessed_csv(df_preprocessed, batch_id)
    return jsonify({
        "status": "accepted",
        "batch_id": batch_id,
        "file_path": saved_path
    }), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
