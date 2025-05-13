import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from ml_model import predict_value
import uvicorn

app = FastAPI()

# Получение ключа API Яндекс.Карт из переменной среды
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
if not YANDEX_API_KEY:
    print("Внимание: Переменная среды YANDEX_API_KEY не установлена!")

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "yandex_api_key": YANDEX_API_KEY})

@app.post("/calculate")
async def calculate(request: Request,
                    latitude: float = Form(...),
                    longitude: float = Form(...),
                    address: str = Form(...),
                    model: str = Form(...),
                    atm_group: str = Form(...)):
    # Вызов ML модели
    result = await predict_value(latitude, longitude, address, model, float(atm_group))
    
    # Отображение результата
    return templates.TemplateResponse(
        "result.html", 
        {
            "request": request, 
            "result": result,
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)