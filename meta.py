import os
import pytz
import subprocess
import json
import re
import exifread
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from datetime import datetime

TOKEN = "" #you token
TIMEZONE = pytz.timezone("UTC") 


def _convert_to_degrees(values):
    """Конвертирует GPS-координаты в десятичные градусы."""
    try:
        d, m, s = values
        deg = float(d.num) / float(d.den)
        min_ = float(m.num) / float(m.den)
        sec = float(s.num) / float(s.den)
        return deg + (min_ / 60.0) + (sec / 3600.0)
    except Exception:
        return None

def _safe_get(tags, key):
    return str(tags.get(key)) if key in tags else None

def run_exiftool(path):
    try:
        proc = subprocess.run(
            ["exiftool", "-j", "-n", path],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        output = proc.stdout
        arr = json.loads(output)
        if isinstance(arr, list) and arr:
            return arr[0]
    except Exception:
        return None

def format_exiftool_metadata(raw):
    metadata = {}

    def try_set(kdisplay, key):
        if key in raw:
            metadata[kdisplay] = raw.get(key)

    try_set("Manufacturer", "Make")
    try_set("Model", "Model")
    try_set("Lens", "LensSpecification")
    try_set("Lens ID", "LensID")
    try_set("Lens Serial Number", "LensSerialNumber")
    try_set("Software", "Software")
    try_set("Image Format", "FileType")
    try_set("Compression", "Compression")

    try_set("Aperture", "ApertureValue")
    try_set("Shutter Speed", "ShutterSpeedValue")
    try_set("ISO", "ISO")
    try_set("Focal Length", "FocalLength")
    try_set("35mm Equivalent", "FocalLengthIn35mmFormat")
    try_set("Exposure Bias", "ExposureCompensation")
    try_set("White Balance", "WhiteBalance")
    try_set("Metering Mode", "MeteringMode")
    try_set("Shooting Mode", "ExposureMode")  
    try_set("Light Source", "LightSource")
    try_set("Orientation", "Orientation")
    try_set("Color Space", "ColorSpace")
    try_set("Date Taken", "DateTimeOriginal")
    try_set("Digitized Date", "CreateDate")
    try_set("File Modified Date", "ModifyDate")

    if "ImageWidth" in raw and "ImageHeight" in raw:
        metadata["Resolution"] = f"{raw.get('ImageWidth')} × {raw.get('ImageHeight')}"


    if "GPSLatitude" in raw and "GPSLongitude" in raw:
        lat = raw.get("GPSLatitude")
        lon = raw.get("GPSLongitude")
        lat_ref = raw.get("GPSLatitudeRef", "")
        lon_ref = raw.get("GPSLongitudeRef", "")
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            if lat_ref in ("S",):
                lat_val = -lat_val
            if lon_ref in ("W",):
                lon_val = -lon_val
            metadata["GPS Coordinates"] = f"{lat_val:.6f}, {lon_val:.6f}"
            metadata["GPS Latitude"] = lat
            metadata["GPS Longitude"] = lon
        except Exception:
            pass

    return metadata

def extract_photo_metadata(file_path):
    metadata = {}
    raw_et = run_exiftool(file_path)
    if raw_et:
        try:
            formatted = format_exiftool_metadata(raw_et)
            if "Aperture" in formatted:
                formatted["Aperture"] = f"f/{formatted['Aperture']}"
            if "Shutter Speed" in formatted:
                try:
                    ss = float(raw_et.get("ShutterSpeedValue", 0))
                    if ss != 0:
                        pass
                except Exception:
                    pass
            metadata.update(formatted)
            return metadata
        except Exception:
            pass

    try:
        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, details=True)
            camera = _safe_get(tags, "Image Make")
            model = _safe_get(tags, "Image Model")
            if camera or model:
                if camera:
                    metadata["Manufacturer"] = camera
                if model:
                    metadata["Model"] = model

            if "Image Software" in tags:
                metadata["Software"] = str(tags["Image Software"])
            if "EXIF LensModel" in tags:
                metadata["Lens"] = str(tags["EXIF LensModel"])
            if "EXIF LensSerialNumber" in tags:
                metadata["Lens Serial Number"] = str(tags["EXIF LensSerialNumber"])
            if "EXIF FNumber" in tags:
                metadata["Aperture"] = f"f/{tags['EXIF FNumber'].values[0].num}/{tags['EXIF FNumber'].values[0].den}" if hasattr(tags['EXIF FNumber'].values[0], 'num') else str(tags["EXIF FNumber"])
            if "EXIF ExposureTime" in tags:
                metadata["Shutter Speed"] = str(tags["EXIF ExposureTime"])
            if "EXIF ISOSpeedRatings" in tags:
                metadata["ISO"] = str(tags["EXIF ISOSpeedRatings"])
            if "EXIF FocalLength" in tags:
                metadata["Focal Length"] = str(tags["EXIF FocalLength"])
            if "EXIF ExposureBiasValue" in tags:
                metadata["Exposure Bias"] = str(tags["EXIF ExposureBiasValue"])
            if "EXIF WhiteBalance" in tags:
                metadata["White Balance"] = str(tags["EXIF WhiteBalance"])
            if "EXIF MeteringMode" in tags:
                metadata["Metering Mode"] = str(tags["EXIF MeteringMode"])
            if "EXIF ExposureProgram" in tags:
                metadata["Shooting Mode"] = str(tags["EXIF ExposureProgram"])

            if "Image Orientation" in tags:
                metadata["Orientation"] = str(tags["Image Orientation"])

            if "EXIF ColorSpace" in tags:
                metadata["Color Space"] = str(tags["EXIF ColorSpace"])

            if "EXIF DateTimeOriginal" in tags:
                try:
                    dt = str(tags["EXIF DateTimeOriginal"])
                    date_obj = datetime.strptime(dt, "%Y:%m:%d %H:%M:%S")
                    metadata["Date Taken"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    metadata["Date Taken"] = str(tags["EXIF DateTimeOriginal"])
            if "EXIF DateTimeDigitized" in tags:
                metadata["Digitized Date"] = str(tags["EXIF DateTimeDigitized"])
            if "Image DateTime" in tags:
                metadata["File Modified Date"] = str(tags["Image DateTime"])

            if "EXIF ExifImageWidth" in tags and "EXIF ExifImageLength" in tags:
                metadata["Resolution"] = f"{tags['EXIF ExifImageWidth']} × {tags['EXIF ExifImageLength']}"

            if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                lat = _convert_to_degrees(tags["GPS GPSLatitude"].values)
                lon = _convert_to_degrees(tags["GPS GPSLongitude"].values)
                lat_ref = tags.get("GPS GPSLatitudeRef", "").values
                lon_ref = tags.get("GPS GPSLongitudeRef", "").values
                if lat is not None and lon is not None:
                    if lat_ref == "S":
                        lat = -lat
                    if lon_ref == "W":
                        lon = -lon
                    metadata["GPS Coordinates"] = f"{lat:.6f}, {lon:.6f}"
                    metadata["Google Maps Link"] = f"https://www.google.com/maps?q={lat},{lon}"

    except Exception as e:
        metadata["Error"] = f"Ошибка при извлечении EXIF: {str(e)}"

    return metadata

def extract_video_metadata(file_path):
    metadata = {}
    try:
        parser = createParser(file_path)
        if not parser:
            return {"Error": "Неподдерживаемый формат видео"}

        with parser:
            meta = extractMetadata(parser)
            if meta:
                for line in meta.exportPlaintext():
                    if ":" in line:
                        key, val = line.split(":", 1)
                        metadata[key.strip()] = val.strip()
            else:
                metadata["Error"] = "Метаданные видео не найдены"
    except Exception as e:
        metadata["Error"] = f"Ошибка при извлечении метаданных видео: {str(e)}"
    return metadata

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Здарова, чушпанчик! 😎 Отправь фото, видео или документ (JPEG/PNG), и я покажу все метаданные, включая EXIF, GPS и дату!"
    )

async def handle_media(update: Update, context: CallbackContext):
    message = update.message

    if message.photo:
        file = await message.photo[-1].get_file()
        file_type = "photo"
    elif message.video:
        file = await message.video.get_file()
        file_type = "video"
    elif message.video_note:
        file = await message.video_note.get_file()
        file_type = "video_note"
    elif message.document:
        file = await message.document.get_file()
        file_type = "document"
        if not message.document.mime_type.startswith("image"):
            await update.message.reply_text("❌ Файл не является изображением! Поддерживаются JPEG/PNG.")
            return
    else:
        await update.message.reply_text("❌ Отправьте фото, видео или документ (JPEG/PNG)!")
        return

    file_path = f"temp_{file.file_id}"
    try:
        await file.download_to_drive(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка загрузки файла: {str(e)}")
        return

    if file_type in ("photo", "document"):
        metadata = extract_photo_metadata(file_path)
    else:
        metadata = extract_video_metadata(file_path)

    if metadata and not (len(metadata) == 1 and "Error" in metadata):
        order_keys = [
            "Manufacturer", "Model", "Lens", "Lens ID", "Lens Serial Number", "Software",
            "Aperture", "Shutter Speed", "ISO", "Focal Length", "35mm Equivalent",
            "Exposure Bias", "White Balance", "Metering Mode", "Shooting Mode",
            "Orientation", "Color Space", "Resolution", "GPS Coordinates", "Google Maps Link",
            "Date Taken", "Digitized Date", "File Modified Date", "Image Format", "Compression"
        ]
        lines = []
        used = set()
        for key in order_keys:
            if key in metadata:
                lines.append(f"▪ <b>{key}:</b> <code>{metadata[key]}</code>")
                used.add(key)
        for key, val in metadata.items():
            if key in used:
                continue
            lines.append(f"▪ <b>{key}:</b> <code>{val}</code>")

        reply_text = "\n".join(lines)
        await update.message.reply_text(f"🔍 <b>Метаданные файла:</b>\n{reply_text}", parse_mode="HTML")
    else:
        error_msg = metadata.get("Error", "Метаданные не найдены")
        await update.message.reply_text(f"❌ {error_msg}")

    try:
        os.remove(file_path)
    except Exception:
        pass

def main():
    job_queue = None 
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE | filters.Document.IMAGE, handle_media))
    app.run_polling()

if __name__ == "__main__":
    main()
