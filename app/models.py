import datetime
import uuid
from typing import List, Type

from config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, String, create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

engine = create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(70), nullable=False)
    date_of_creation: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    tokens: Mapped[List["Token"]] = relationship(
        "Token", back_populates="user", cascade="all, delete-orphan"
    ) 
    advertisements: Mapped[List["Advertisement"]] = relationship(
        "Advertisement", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date_of_creation": self.date_of_creation,
            "advertisements": [advertisement.id for advertisement in self.advertisements],
        }


class Token(Base):
    __tablename__ = "token"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[uuid.UUID] = mapped_column(
        UUID, server_default=func.gen_random_uuid(), unique=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(User, back_populates="tokens")
    date_of_creation: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    @property
    def dict(self):
        return {"id": self.id, "token": self.token, "user_id": self.user_id, 'date_of_creation': self.date_of_creation}
    

class Advertisement(Base):
    __tablename__ = "advertisement"

    id: Mapped[int] = mapped_column(primary_key=True)
    header: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(User, back_populates="advertisements")
    date_of_creation: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def dict(self):
        return {
            "id": self.id,
            "header": self.header,
            "description": self.description,
            "date_of_creation": self.date_of_creation,
            "user_id": self.user_id,
        }


MODEL_TYPE = Type[User | Token | Advertisement]
MODEL = User | Token | Advertisement

Base.metadata.create_all(bind=engine)
