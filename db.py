from typing import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase,Mapped, mapped_column
from sqlalchemy import JSON, Column, Integer, String, select
from pydantic import BaseModel
from fastapi import Depends
import json

engine = create_async_engine('sqlite+aiosqlite:///searchstat.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    #history: Mapped[list] = mapped_column(MutableList.as_mutable(JSON))
    history: Mapped[str]
    
class CityModel(Base):
    __tablename__ = "citystats"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    counter: Mapped[int]
    
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {'Status' : 'DB created'}

#Операции с БД:

class UserAddSchema(BaseModel):
    name: str

class UserSchema(UserAddSchema):
    id: int
    history: dict

class CityAddSchema(BaseModel):
    name: str
    
class CitySchema(CityAddSchema):
    id: int
    counter: int

async def add_user(data: UserAddSchema, session: SessionDep):
    new_user = UserModel(
         name=data.name,
         history=':'        
        )
    session.add(new_user)
    await session.commit()
    return {'user added': True}
        

async def add_city(data: CityAddSchema, session: SessionDep):
    new_city = CityModel(
        name=data.name,
        counter=1        
    )
    session.add(new_city)
    await session.commit()
    return {'user added': True}

async def get_all_users(session: SessionDep):
    query = select(UserModel)
    result = await session.execute(query)
    return result.scalars().all()

async def get_all_city(session: SessionDep):
    query = select(CityModel)
    result = await session.execute(query)
    return result.scalars().all()

async def modify_user_history(username: str, city: str, session: SessionDep):
    result = await session.execute(select(UserModel).where(UserModel.name == username))
    user = result.scalars().first()
    if user:
        user.history += f', {city}' # добавляем город в список
        
        await session.commit()

async def implement_city_counter(cityname: str, session: SessionDep):
    result = await session.execute(select(CityModel).where(CityModel.name == cityname))
    city = result.scalars().first()
    if city: 
        city.counter += 1
        await session.commit()
    return {'Implemented': True}

async def get_history_by_username(username: str, session: SessionDep):
    result = await session.execute(select(UserModel).where(UserModel.name == username))
    user = result.scalars().first()
    if user:
        return {'История поиска для {user.name} :': user.history}

