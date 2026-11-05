# Hey AI, who am I?

Public personality quiz — same UI as the local Ollama lab, powered by **Groq** so it stays online without your PC.

Deploy name / URL slug: **hey-ai-who-am-i**

## Run locally

```bash
cd personality-quiz-groq
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` → `.env` and set `GROQ_API_KEY` from [console.groq.com/keys](https://console.groq.com/keys).

```bash
python app.py
```

## Deploy on Render

This repo includes `render.yaml`. On [render.com](https://render.com): **New → Blueprint** → connect this GitHub repo → set `GROQ_API_KEY` when prompted.

## Security

Never commit `.env`. If a key was pasted in chat, revoke it and create a new one.
