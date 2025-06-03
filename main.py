from fastapi import FastAPI, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import db

import uvicorn
import httpx

app = FastAPI()

LOGIN = 'Anonimous'

@app.post('/reset_db', summary='Создать или очичтить БД', tags=['Администрирование'])
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
async def get_weather(city: str = Form(...), session: AsyncSession = Depends(db.get_session)):
    
    lat, lon = await get_city_coordinates(city)
       
    forecast = await fetch_weather(lat, lon)

    allcities = await db.get_all_city(session)
    flag = False
    for c in allcities:
        if city.lower() == c.name.lower():
            flag = True
    if flag:        
        await db.implement_city_counter(city, session)
    else:
        new_city = db.CityAddSchema
        new_city.name = city
        await db.add_city(new_city, session)
        await db.implement_city_counter(city, session)
    await db.modify_user_history(LOGIN, city, session)    
    return {
        "city": city,
        "forecast": forecast.dict()
    }

@app.post("/getuser")
async def get_user(username: str = Form(...), session: AsyncSession = Depends(db.get_session)):
    global LOGIN
    allusers = await db.get_all_users(session)
    flag = False
    for u in allusers:
        if username.lower() == u.name.lower():
            flag = True
    if flag:        
        LOGIN = username
    else:
        user = db.UserAddSchema
        user.name = username
        await db.add_user(user, session)
        LOGIN = username
    return {"username": username}


@app.get('/history/{username}')
async def get_history(username, session: AsyncSession = Depends(db.get_session) ):
    result = await db.get_history_by_username(username, session)
    return {'history': result}


# Сомнительное:
@app.post('/add_to_history')
async def add_to_history(data: dict, session: AsyncSession = Depends(db.get_session)):
    username = data.get('username')
    city = data.get('city')
    
    if not username or not city:
        raise HTTPException(status_code=400, detail="Missing username or city")
    await db.modify_user_history(username, city, session)
    # После добавления можно вернуть обновленный список
    history_list = await db.get_history_by_username(username, session)
    return {"history": history_list}

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)