# План рефакторинга: Миграция на SQLAlchemy с адаптерами БД

## Цели
1. Добавить поддержку PostgreSQL через SQLAlchemy
2. Сохранить обратную совместимость с существующим SQLite кодом
3. Использовать паттерн Adapter для абстракции работы с БД
4. Обеспечить плавный переход от старого API к новому

## Архитектура

### Структура файлов
```
src/
├── database.py              # [DEPRECATED] Старый SQLite код (сохраняется без изменений)
├── db/                      # Новый пакет для работы с БД
│   ├── __init__.py         # Экспорт основных классов
│   ├── adapter.py          # Базовый абстрактный класс DatabaseAdapter
│   ├── sqlite_adapter.py   # SQLite адаптер через SQLAlchemy
│   ├── postgres_adapter.py # PostgreSQL адаптер через SQLAlchemy
│   ├── models.py           # SQLAlchemy модели (ORM)
│   └── factory.py          # Фабрика для создания адаптеров
└── config.py               # Обновить для новых настроек БД

```

### Компоненты

#### 1. `src/db/models.py` - SQLAlchemy ORM модели
```python
# Определение моделей для всех таблиц:
# - Chat
# - Message
# - User
# - Media
# - Reaction
# - SyncStatus
# - Metadata

# Используем декларативный стиль SQLAlchemy
# Модели должны быть совместимы с текущей схемой SQLite
```

#### 2. `src/db/adapter.py` - Базовый абстрактный класс
```python
from abc import ABC, abstractmethod

class DatabaseAdapter(ABC):
    """Базовый интерфейс для всех адаптеров БД"""

    @abstractmethod
    def initialize_schema(self) -> None:
        """Создать таблицы если не существуют"""
        pass

    @abstractmethod
    def upsert_chat(self, chat_data: dict) -> None:
        """Вставить или обновить чат"""
        pass

    @abstractmethod
    def insert_messages(self, messages: List[dict]) -> None:
        """Вставить сообщения батчами"""
        pass

    @abstractmethod
    def get_last_synced_message_id(self, chat_id: int) -> int:
        """Получить ID последнего синхронизированного сообщения"""
        pass

    # ... остальные методы из текущего Database класса
```

#### 3. `src/db/sqlite_adapter.py` - SQLite адаптер
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .adapter import DatabaseAdapter
from .models import Base, Chat, Message, User, Media, ...

class SQLiteAdapter(DatabaseAdapter):
    """Адаптер для SQLite через SQLAlchemy"""

    def __init__(self, database_path: str, timeout: float = 60.0):
        # SQLite connection string
        db_url = f"sqlite:///{database_path}"

        # Engine с настройками для SQLite
        self.engine = create_engine(
            db_url,
            connect_args={
                "timeout": timeout,
                "check_same_thread": False
            },
            echo=False
        )

        # Session factory
        self.Session = sessionmaker(bind=self.engine)

        # Включить WAL mode
        self._enable_wal_mode()

    def initialize_schema(self):
        """Создать таблицы"""
        Base.metadata.create_all(self.engine)

    # ... реализация всех методов
```

#### 4. `src/db/postgres_adapter.py` - PostgreSQL адаптер
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .adapter import DatabaseAdapter
from .models import Base, Chat, Message, User, Media, ...

class PostgreSQLAdapter(DatabaseAdapter):
    """Адаптер для PostgreSQL через SQLAlchemy"""

    def __init__(self, host: str, port: int, database: str,
                 user: str, password: str):
        # PostgreSQL connection string
        db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

        # Engine с connection pooling
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Проверка соединений
            echo=False
        )

        # Session factory
        self.Session = sessionmaker(bind=self.engine)

    def initialize_schema(self):
        """Создать таблицы"""
        Base.metadata.create_all(self.engine)

    # ... реализация всех методов
```

#### 5. `src/db/factory.py` - Фабрика адаптеров
```python
from typing import Union
from .adapter import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgreSQLAdapter

def create_database_adapter(config) -> DatabaseAdapter:
    """
    Фабрика для создания адаптера БД на основе конфигурации

    Args:
        config: Config объект с настройками

    Returns:
        DatabaseAdapter: Экземпляр адаптера (SQLite или PostgreSQL)
    """
    db_type = config.db_type.lower()

    if db_type == "sqlite":
        return SQLiteAdapter(
            database_path=config.database_path,
            timeout=config.database_timeout
        )
    elif db_type == "postgresql":
        return PostgreSQLAdapter(
            host=config.postgres_host,
            port=config.postgres_port,
            database=config.postgres_db,
            user=config.postgres_user,
            password=config.postgres_password
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
```

#### 6. `src/config.py` - Обновления конфигурации
```python
# Добавить новые поля:
self.db_type = os.getenv("DB_TYPE", "sqlite").lower()

# PostgreSQL настройки
self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
self.postgres_db = os.getenv("POSTGRES_DB", "telegram_backup")
self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
self.postgres_password = os.getenv("POSTGRES_PASSWORD", "")

# Флаг для использования нового адаптера (для плавного перехода)
self.use_new_database_adapter = os.getenv("USE_NEW_DB_ADAPTER", "false").lower() == "true"
```

## План миграции по этапам

### Этап 1: Подготовка (без breaking changes)
- [x] Добавить PostgreSQL в docker-compose.yml
- [x] Добавить psycopg2-binary и SQLAlchemy в requirements.txt
- [ ] Создать структуру каталога `src/db/`
- [ ] Создать SQLAlchemy модели на основе текущей схемы
- [ ] Добавить тесты для моделей

### Этап 2: Реализация адаптеров
- [ ] Реализовать базовый класс `DatabaseAdapter`
- [ ] Реализовать `SQLiteAdapter` (полный функционал)
- [ ] Реализовать `PostgreSQLAdapter` (полный функционал)
- [ ] Реализовать фабрику `create_database_adapter()`
- [ ] Добавить unit-тесты для каждого адаптера

### Этап 3: Интеграция с существующим кодом
- [ ] Обновить `src/telegram_backup.py`:
  ```python
  # Старый способ (deprecated, но работает)
  if not config.use_new_database_adapter:
      from src.database import Database
      self.db = Database(config)
  else:
      # Новый способ через адаптеры
      from src.db.factory import create_database_adapter
      self.db = create_database_adapter(config)
  ```
- [ ] Обновить `src/web/main.py` аналогично
- [ ] Обеспечить одинаковый API между старым и новым подходом

### Этап 4: Тестирование
- [ ] Тест миграции данных SQLite → PostgreSQL
- [ ] Интеграционные тесты с обоими адаптерами
- [ ] Тест обратной совместимости (старый код + новый адаптер)
- [ ] Performance тесты (сравнение SQLite vs PostgreSQL)

### Этап 5: Миграционный скрипт
- [ ] Создать `src/migrate_to_postgres.py`:
  - Подключиться к SQLite (источник)
  - Подключиться к PostgreSQL (назначение)
  - Скопировать данные таблица за таблицей
  - Верифицировать целостность данных
  - Отчет о миграции

### Этап 6: Документация
- [ ] Обновить README.md с инструкциями по PostgreSQL
- [ ] Обновить CLAUDE.md с новой архитектурой
- [ ] Добавить примеры миграции в документацию
- [ ] Создать troubleshooting guide

### Этап 7: Deprecation path (будущее)
- [ ] Пометить `src/database.py` как deprecated
- [ ] Добавить warnings при использовании старого кода
- [ ] Установить дату удаления старого кода (например, через 6 месяцев)

## Ключевые решения

### 1. Обратная совместимость
- Старый `database.py` остается без изменений
- Переключение через переменную `USE_NEW_DB_ADAPTER`
- По умолчанию используется старый подход (безопасно)

### 2. API совместимость
Оба адаптера должны предоставлять одинаковый интерфейс:
```python
# Текущий Database класс
db = Database(config)
db.upsert_chat(...)

# Новые адаптеры
db = create_database_adapter(config)
db.upsert_chat(...)  # Тот же метод!
```

### 3. Различия SQLite vs PostgreSQL
| Фича | SQLite | PostgreSQL |
|------|--------|-----------|
| Тип данных INTEGER | INTEGER | BIGINT |
| AUTO INCREMENT | AUTOINCREMENT | SERIAL/BIGSERIAL |
| Boolean | INTEGER (0/1) | BOOLEAN |
| JSON | TEXT | JSONB |
| WAL mode | Вручную PRAGMA | Встроенный |
| Concurrent writes | Ограничены | Полная поддержка |

### 4. Миграция схемы
SQLAlchemy автоматически создаст схему при первом запуске:
```python
# Для SQLite
Base.metadata.create_all(engine)  # Создаст .db файл

# Для PostgreSQL
Base.metadata.create_all(engine)  # Создаст таблицы в БД
```

## Риски и митигация

### Риск 1: Breaking changes для пользователей
**Митигация:**
- Сохранить старый код
- Использовать feature flag `USE_NEW_DB_ADAPTER`
- По умолчанию старое поведение

### Риск 2: Проблемы с производительностью PostgreSQL
**Митигация:**
- Использовать connection pooling
- Batch inserts через SQLAlchemy
- Индексы на важных полях

### Риск 3: Различия в типах данных
**Митигация:**
- Тщательное тестирование моделей
- Явное указание типов в моделях SQLAlchemy
- Миграционный скрипт с валидацией

### Риск 4: Потеря данных при миграции
**Митигация:**
- Создать бэкап перед миграцией
- Валидация целостности после миграции
- Возможность отката (rollback)

## Следующие шаги

1. **Получить одобрение плана** от вас
2. **Создать SQLAlchemy модели** на основе текущей схемы
3. **Реализовать базовый адаптер** и SQLite адаптер
4. **Добавить PostgreSQL адаптер**
5. **Интегрировать в существующий код**
6. **Тестировать и итерировать**

## Вопросы для обсуждения

1. Название пакета: `src/db/` или `src/database_v2/` или `src/adapters/`?
Пусть будет `src/sqlalchemy/`

2. Когда переключить по умолчанию на новый адаптер?
Не сейчас

3. Нужны ли Alembic миграции для управления схемой?
Используй стандартный подход для SQLAlchemy

4. Добавить ли async/await поддержку (SQLAlchemy 2.0)?
Если в текущем код это нужно.

5. Какие db_type нужны и как их использовать?
sqlite - Текущая реализация
sqlite-alchemy - SQLAlchemy с адаптером sqlite
postgres-alchemy - SQLAlchemy с адаптером postgres
