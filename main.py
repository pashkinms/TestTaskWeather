from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import db

import uvicorn
import httpx

app = FastAPI()

@app.post('/reset_db')
async def reset_db():
    await db.setup_database()

search_history = {}  # user_id -> list of cities 
city_stats = {}  # city_name -> count

CITY_LIST = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Челябинск", "Омск", "Самара"]

CITY_COORDS = {
        "Москва": (55.7558, 37.6173),
        "Санкт-Петербург": (59.9343, 30.3351),
        "Новосибирск": (55.0084, 82.9357),
        "Екатеринбург": (56.8389, 60.6057),
        "Казань": (55.7887, 49.1221),
        "Челябинск": (55.1599, 61.4022),
        "Омск": (54.9885, 73.3242),
        "Самара": (53.1959, 50.1000),
    }


class WeatherForecast(BaseModel):
    temperature: float
    windspeed: float
    description: str

async def get_city_coordinates(city_name: str):
    coords = CITY_COORDS.get(city_name)
    if not coords:
        raise HTTPException(status_code=404, detail='Город не найден')
    return coords

async def fetch_weather(latitude, longitude):
    url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m,weather_code'
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        current_weather = data.get('current')
        if not current_weather:
            raise HTTPException(status_code=500, detail='Не удалось получить погоду') 
        return WeatherForecast(
            temperature=current_weather['temperature_2m'],
            windspeed=current_weather['wind_speed_10m'],
            description='Облачно' if current_weather['weather_code'] == 3 else 'Ясно'
        )       

@app.get('/', response_class=HTMLResponse, summary='Main Page', tags=['Open IndexPage'])
async def index():
    with open('static/index.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/autocomplete')
async def autocomplete(q: str):
    suggestions = [city for city in CITY_LIST if city.lower().startswith(q.lower())]
    return suggestions

@app.post("/weather")
async def get_weather(city: str = Form(...)):
    
    lat, lon = await get_city_coordinates(city)
       
    forecast = await fetch_weather(lat, lon)

    
    return {
        "city": city,
        "forecast": forecast.dict()
    }

@app.post("/getuser")
async def get_user(username: str = Form(...)):
    return {"username": username}

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)