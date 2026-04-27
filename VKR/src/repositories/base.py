from typing import Generic, TypeVar, Type, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from src.database import Base

# TypeVars для аннотаций: Модель Алхимии, Схема создания, Схема обновления
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        """Получить одну запись по ID."""
        query = select(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Получить список всех записей с пагинацией."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: CreateSchemaType | dict[str, Any]) -> ModelType:
        """Создать новую запись."""
        obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in # Если пришла Pydantic схема, превращаем её в словарь

        db_obj = self.model(**obj_in_data)
        self.session.add(db_obj)
        await self.session.flush() # Делаем flush, а не commit. Коммит делает сервисный слой
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]) -> ModelType:
        """Обновить существующую запись."""
        obj_data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, BaseModel) else obj_in

        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, obj_id: int) -> None:
        """Удалить запись по ID."""
        query = delete(self.model).where(self.model.id == obj_id)
        await self.session.execute(query)
        await self.session.flush()