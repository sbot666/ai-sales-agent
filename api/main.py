from fastapi import FastAPI

app = FastAPI(title="AI Sales Agent", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}
