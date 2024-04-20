from datetime import datetime
from enum import Enum
from typing import Any, Optional

from asyncpg import UniqueViolationError
import sqlalchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

engine = create_async_engine('sqlite+aiosqlite:///db.sqlite3', echo=True)
async_session = async_sessionmaker(bind=engine)


class Base(AsyncAttrs, DeclarativeBase):
    id: Any
    __name__: str

    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower() + 's'

    async def save(self, db_session: AsyncSession):
        db_session.add(self)
        return await db_session.commit()

    async def delete(self, db_session: AsyncSession):
        await db_session.delete(self)
        await db_session.commit()
        return True

    async def update(self, db: AsyncSession, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return await db.commit()

    async def save_or_update(self, db: AsyncSession):
        try:
            db.add(self)
            return await db.commit()
        except IntegrityError as exception:
            if isinstance(exception.orig, UniqueViolationError):
                return await db.merge(self)
        finally:
            await db.close()


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[str] = mapped_column(sqlalchemy.String(30), unique=True)
    fullname: Mapped[Optional[str]]
    lang: Mapped[str] = mapped_column(sqlalchemy.String(20))
    created_at: Mapped[datetime] = mapped_column(sqlalchemy.DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(sqlalchemy.DateTime(), default=datetime.utcnow,
                                                 onupdate=datetime.utcnow)
    is_admin: Mapped[bool] = mapped_column(sqlalchemy.Boolean(), default=False)
    phone_number: Mapped[str] = mapped_column(sqlalchemy.String(20))


class Category(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sqlalchemy.String(55))

    books: Mapped['Book'] = relationship('Book', back_populates='category')


class Book(Base):
    # page, price, description

    class VolEnum(Enum):
        HARD = "hard"
        SOFT = "soft"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sqlalchemy.String(255))
    author: Mapped[str] = mapped_column(sqlalchemy.String(255))
    vol: Mapped[str] = mapped_column(sqlalchemy.Enum(VolEnum, values_callable=lambda i: [field.value for field in i]),
                                     default=VolEnum.SOFT)
    amount: Mapped[int] = mapped_column(sqlalchemy.Integer)
    category_id = mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey('categorys.id', ondelete="CASCADE"))

    category: Mapped['Category'] = relationship('Category', back_populates='books')
    photo: Mapped[str] = sqlalchemy.String(55)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
