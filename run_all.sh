docker-compose down

docker-compose build

mkdir -p data/incoming data/processing data/processed data/errors data/results

docker-compose up -d

sleep 5

docker-compose ps

curl -X POST "http://localhost:5000/preprocess" \
     -H "Content-Type: application/json" \
     --data @- << 'EOF'
[
  {
    "PassengerId": 999,
    "Survived": 0,
    "Pclass": 3,
    "Name": "Test, Mr. Example",
    "Sex": "male",
    "Age": 30,
    "SibSp": 0,
    "Parch": 0,
    "Ticket": "TEST123",
    "Fare": 10.0,
    "Cabin": "",
    "Embarked": "S"
  }
]
EOF

sleep 8

echo "=== data/results ==="
ls -l data/results

RESULT_JSON=$(ls data/results/*.json 2>/dev/null | head -n 1)
if [ -n "$RESULT_JSON" ]; then
  echo "=== Содержимое $RESULT_JSON ==="
  cat "$RESULT_JSON"
else
  echo "=== В data/results нет JSON-файлов ==="
fi

echo "=== data/incoming ==="
ls -l data/incoming
echo "=== data/processed ==="
ls -l data/processed
echo "=== data/errors ==="
ls -l data/errors

echo "Завершено."
