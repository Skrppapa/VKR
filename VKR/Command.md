from sqlalchemy.util import deprecated

# Базовые команды для проекта

- `. venv/bin/activate` - Активация виртуального окружения
- `pip freeze > requirements.txt` - Фиксация текущих библиотек и их версий в файл
- `pip install -r requirements.txt` - Установка библиотек из файла с зависимостями
- `fastapi dev main.py` - Удобный запуск
- `python src/main.py` - Запуск с настроенным файлом main

# Alembic

- `alembic init src/migrations` - создание директории для миграций
- `alembic revision --autogenerate -m "Название миграции"` - Инициализация версии миграции
- `alembic upgrade 9812612dd2f6 (Уникальный номер миграции)` - Накатить определенную миграцию
- `alembic upgrade head` - Накатить последнюю миграцию

### В конфигурационном файле alembic.ini

- Определяем формат имени миграции: `file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d-%%(minute).2d-%%(second).2d_%%(rev)s_%%(slug)s`
- Указываем путь, где искать файлы: `prepend_sys_path = . src`
- Указываем драйвер: `sqlalchemy.url = driver://user:pass@localhost/dbname`
- Строка `hooks = black` и еще 3 ниже отвечают за форматирование кода в файле миграции

### В файле .env

Важно не забыть прописать target_metadata = Base.metadata
Так же выше импортировать Base + не забывать импортировать модели (будут светиться серым - так правильно)

# SQLAlchemy

После получения итератора, при GET запросе в БД, например запросом:

```python
query = select(HotelsOrm)
result = await session.execute(query)
```

### Варианты как мы можем посмотреть объекты

```python
hotels = result.all() # Все возвращенные отели
hotels = result.first() # Только первый возвращенный отель
hotels = result.one() # Если вернулся 1 отель - выведет если 0 или больше 1 - ошибка
hotels = result.one_or_none() # Если ничего или 1 отель - выведет. Иначе ошибка
```

Еще лучше использовать .scalars() - достает из кортежа первый элемент

```python
hotels = result.scalars().all()
```

Полезно видеть какой конкретно запрос алхимия отправляет в БД

```python
print(add_hotel_stmt.compile(engine, compile_kwargs={"literal_binds": True})) 
```

Здесь `.compile(compile_kwargs={"literal_binds": True})` для читаемого вывода отправленного запроса


# Авторизация и Аутентификация

**Необходимые библиотеки**

```python
pip install pyjwt "passlib[bcrypt]"
```
**Реализация в коде**

```python
from passlib.context import CryptContext  # Нужен этот импорт
# Важно passlib уже не используют. Сейчас делают чисто через bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Создаем контекст

pwd_context.hash(password) # Вставляем в ручку - это и есть функция дающая хэшированный пароль
```

### JWT токен

**JWT Токен** - это такой набор данных, в зашифрованном виде, который выдается при входе на ресурс.
Его можно легко расшифровать на сайте jwt.io, никакой критической информации о пользователе он не несет.
Состоит он из 3-ех блоков разделенных через точку. Если мы поменяем информацию в средней части токена - 
то шифрованная часть будет меняться и не будет валидна 3-ей части токена. Поэтому их крайне тяжело подделать.

**Реализация в коде**
```python
import jwt

# Так же помещаем в переменные окружения следующее

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Ключ генерации
ALGORITHM = "HS256"   # Алгоритм генерации
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Время жизни токена

# Функция генерации токена из документации 

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Более простая версия без дельт временных зон. Под мой проект

async with async_session_maker() as session:
    user = await UsersRepository(session).get_one_or_none(email=data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь с таким email не зарегистрирован")
    access_token = create_access_token({"user_id": user.id})
    return {"access_token": access_token}

# Обязательно помимо мэйла нужно проверять валидность пароля - тот ли это пользователь

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
```