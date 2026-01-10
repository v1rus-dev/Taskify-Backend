from fastapi import FastAPI

app = FastAPI(title="Tasky - Mini Todo API")

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка статуса сервиса.
    Возвращает JSON с информацией о работе API.
    """
    return {"status": "ok", "service": "Tasky Backend"}
