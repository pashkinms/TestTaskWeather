from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase,Mapped, mapped_column
from sqlalchemy import JSON, Column, Integer, String

engine = create_async_engine('sqlite+aiosqlite:///searchstat.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    history = Column(JSON)

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

    