# ⚽ Football AI

Football AI — веб-приложение для прогнозирования результатов матчей английской Премьер-лиги (EPL) с использованием машинного обучения.

## Возможности

- прогноз исхода матча (HOME / DRAW / AWAY);
- вероятности каждого исхода;
- рейтинг Elo;
- форма команд за последние 5 матчей;
- статистические признаки;
- REST API на FastAPI;
- веб-интерфейс.

## Используемые технологии

- Python
- FastAPI
- XGBoost
- Scikit-learn
- Pandas
- Supabase

## Установка

```bash
git clone <repository-url>
cd football-ai

pip install -r requirements.txt
```

Создайте файл `.env`:

```text
SUPABASE_URL=...
SUPABASE_KEY=...
```

## Запуск

```bash
uvicorn api:app --reload
```

После запуска откройте:

```
http://127.0.0.1:8000
```

Swagger API:

```
http://127.0.0.1:8000/docs
```

## Структура проекта

```
api.py
predict_match.py
model_utils.py
feature_engineering.py
train_model_xgboost_elo.py
teams.py
static/
```

## Модель

Используемые признаки:

- коэффициенты букмекеров;
- Elo;
- форма последних 5 матчей;
- забитые и пропущенные мячи;
- удары;
- удары в створ.

