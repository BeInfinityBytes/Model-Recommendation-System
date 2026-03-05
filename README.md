# ModelIQ – Model Selection & Recommendation Backend

## Overview

ModelIQ is a backend system that helps users select suitable AI/ML models based on their use case. It works by:

1. Accepting a natural language use case from the user
2. Analyzing ambiguity using an LLM (Gemini)
3. Asking clarification questions when required
4. Storing use case sessions in MongoDB
5. Matching the finalized parameters against a dataset of pre-scraped Hugging Face models
6. Returning recommended models via two strategies:

   * Parameter-based matching (all relevant models)
   * Score-based Top-K ranking

The system is built using FastAPI, MongoDB Atlas, Gemini LLM, and follows a clean service-oriented architecture.

---

## Tech Stack

* Python 3.11+
* FastAPI
* MongoDB Atlas (PyMongo)
* Gemini (Google Generative AI)
* Pydantic / Pydantic Settings
* uv (package & environment manager)

---

## Environment Setup

### 1. Create `.env` from `.env.example`

Copy the example file:

```
cp .env.example .env
```

Update it with your own credentials.

### Example `.env`

```
# LLM
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=models/gemini-flash-lite-latest

# -------------------------
# USECASE SESSIONS STORAGE
# -------------------------
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/
MONGODB_DB=modeliq
MONGODB_COLLECTION=usecase_sessions

# -------------------
# MODEL DATA DATABASE (HuggingFace scraped data)
# -------------------
MODEL_DATA_MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/
MODEL_DATA_DB=modeliq
MODEL_DATA_COLLECTION=model-data

# -------------------
# Logging
# -------------------
LOG_LEVEL=DEBUG
```

Notes:

* `usecase_sessions` is used only for user sessions
* `model-data` contains pre-scraped Hugging Face models and must not be modified

---

## Package Installation (uv)

Install dependencies from `pyproject.toml`:

```
uv sync
```

---

## Running the Project

Start the FastAPI server using:

```
uv run uvicorn src.model_selection.api.main:app --reload --port 8000
```

The API will be available at:

```
http://127.0.0.1:8000
```

---

## API Endpoints

### 1. Analyze Use Case

**Endpoint**

```
POST /usecase/analyze
```

**Purpose**

* Accepts a user use case
* Determines ambiguity
* Generates clarification questions if required
* Creates a new session

**PowerShell Test Command**

```
Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/usecase/analyze" `
  -Method POST `
  -Body '{"usecase_text":"model for customer interaction bot"}' `
  -Headers @{"Content-Type"="application/json"} |
  Select-Object -Expand Content
```

---

### 2. Submit Clarification Answers

**Endpoint**

```
POST /usecase/answer
```

#### a) Accept all suggested answers

```
Invoke-WebRequest -Uri "http://127.0.0.1:8000/usecase/answer" `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{
    "session_id": "THE_SESSION_ID",
    "answers": []
  }'
```

#### b) Modify specific answers

```
Invoke-WebRequest -Uri "http://127.0.0.1:8000/usecase/answer" `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{
    "session_id": "THE_SESSION_ID",
    "answers": [
      { "question_id": "q2", "answer": "Pre-processed Text" }
    ]
  }'
```

---

### 3. Get All Matching Models (Parameter-Based)

**Endpoint**

```
GET /recommend/session/{session_id}/all
```

**Purpose**

* Returns all models that match the finalized parameters

**PowerShell Test Command**

```
Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/recommend/session/YOUR_SESSION_ID/all" `
  -Method GET
```

---

### 4. Get Top-K Recommended Models (Score-Based)

**Endpoint**

```
GET /recommend/session/{session_id}/top?top_k=5
```

**Purpose**

* Ranks models based on extracted features
* Returns top K models

**PowerShell Test Command**

```
Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/recommend/session/YOUR_SESSION_ID/top?top_k=5" `
  -Method GET
```

---

## Database Usage

* **usecase_sessions**

  * Stores session_id, usecase text, questions, answers, and final parameters

* **model-data**

  * Read-only dataset of scraped Hugging Face models
  * Used only for recommendations

---

## Health Check

```
GET /health
```

Returns API status.

---

## Notes

* MongoDB Atlas is used for both session data and model data with strict collection separation
* The system is safe to run concurrently and supports async FastAPI execution
* The backend is designed to be extended with UI, analytics, or additional ranking strategies
