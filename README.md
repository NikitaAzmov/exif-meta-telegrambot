# EXIF Meta Telegram Bot

Бот для Telegram, который извлекает метаданные (EXIF, GPS, видео-метаданные) из присланных фото/видео/документов и возвращает их пользователю.  
Название основного скрипта: `meta.py`

## 🛠️ Возможности

- Извлечение EXIF-данных из изображений (включая информацию о камере, объективе, диафрагме, ISO и т.п.)
- Извлечение GPS-координат и генерация ссылки на Google Maps
- Разбор видео-метаданных через `hachoir`
- Резервное извлечение через `exiftool`, если установлен
- Поддержка фото, видео, документов, кружков в Telegram
- Удобный вывод в чат (HTML-разметка)

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий:
```bash
git clone https://github.com/NikitaAzmov/exif-meta-telegrambot.git
cd exif-meta-telegrambot
```

### 2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Установите зависимости:

```
python-telegram-bot>=20.0
pytz
exifread
hachoir-core
hachoir-metadata
hachoir-parser
```

### 4. Установите системную зависимость `exiftool` (рекомендуется, но не обязательно):

- **Ubuntu / Debian:**
  ```bash
  sudo apt update
  sudo apt install libimage-exiftool-perl
  ```

- **macOS (через Homebrew):**
  ```bash
  brew install exiftool
  ```

- **Windows:**
  Скачайте `exiftool` с официального сайта и добавьте в PATH.

### 5. Настройте токен

Создайте файл `.env`:
```env
TOKEN=ваш_токен_от_Telegram
```

### 6. Запуск
```bash
python meta.py
```

## ⚙️ Требуемые библиотеки

```
python-telegram-bot>=20.0
pytz
exifread
hachoir-core
hachoir-metadata
hachoir-parser
```

## 📦 Поддерживаемые типы файлов

- JPEG, PNG (изображения)
- Видео — поддерживаемые `hachoir`
