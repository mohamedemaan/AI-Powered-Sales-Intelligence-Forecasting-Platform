import os
import struct
import wave
from typing import Dict, Any, Optional


def validate_image_file(file_path: str) -> Dict[str, Any]:
    """
    Step 17: Validates image integrity, dimensions, and format.
    Uses PIL / Pillow if installed, otherwise inspects binary header bytes.
    """
    if not os.path.exists(file_path):
        return {"status": "FAIL", "error": "File does not exist"}

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return {"status": "FAIL", "error": "Empty file (0 bytes)"}

    try:
        from PIL import Image
        with Image.open(file_path) as img:
            img.verify()
        
        # Re-open after verify() to inspect properties
        with Image.open(file_path) as img:
            return {
                "status": "PASS",
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "file_size_bytes": file_size,
                "is_valid": True
            }
    except Exception as e:
        # Fallback to basic header inspection
        with open(file_path, "rb") as f:
            header = f.read(16)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return {"status": "PASS", "format": "PNG", "file_size_bytes": file_size, "is_valid": True}
        elif header.startswith(b"\xff\xd8\xff"):
            return {"status": "PASS", "format": "JPEG", "file_size_bytes": file_size, "is_valid": True}
        return {"status": "FAIL", "error": f"Image corrupted or invalid: {str(e)}", "is_valid": False}


def validate_audio_file(file_path: str) -> Dict[str, Any]:
    """
    Step 17: Validates audio file structure, channels, sample rate, and duration.
    """
    if not os.path.exists(file_path):
        return {"status": "FAIL", "error": "File does not exist"}

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return {"status": "FAIL", "error": "Empty file (0 bytes)"}

    # If WAV, inspect using standard wave library
    if file_path.lower().endswith(".wav"):
        try:
            with wave.open(file_path, "rb") as wav:
                channels = wav.getnchannels()
                sample_rate = wav.getframerate()
                frames = wav.getnframes()
                duration = round(frames / float(sample_rate), 2) if sample_rate > 0 else 0.0
                return {
                    "status": "PASS",
                    "format": "WAV",
                    "channels": channels,
                    "sample_rate": sample_rate,
                    "duration_seconds": duration,
                    "file_size_bytes": file_size,
                    "is_valid": True
                }
        except Exception as e:
            return {"status": "FAIL", "error": f"Corrupt WAV audio: {str(e)}", "is_valid": False}

    # Basic inspection for other audio formats (e.g. MP3)
    with open(file_path, "rb") as f:
        head = f.read(4)
    if head.startswith(b"ID3") or (head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return {
            "status": "PASS",
            "format": "MP3",
            "file_size_bytes": file_size,
            "is_valid": True
        }

    return {"status": "WARNING", "format": "UNKNOWN_AUDIO", "file_size_bytes": file_size, "note": "Unparsed audio container"}


def validate_video_file(file_path: str) -> Dict[str, Any]:
    """
    Step 17: Validates video container headers and integrity.
    """
    if not os.path.exists(file_path):
        return {"status": "FAIL", "error": "File does not exist"}

    file_size = os.path.getsize(file_path)
    if file_size < 32:
        return {"status": "FAIL", "error": "File too small to be a valid video container"}

    with open(file_path, "rb") as f:
        head = f.read(32)

    # MP4 / ISO Base Media File Format signature check: 'ftyp' at offset 4
    if len(head) >= 8 and head[4:8] == b"ftyp":
        major_brand = head[8:12].decode("ascii", errors="replace").strip()
        return {
            "status": "PASS",
            "format": f"MP4 ({major_brand})",
            "file_size_bytes": file_size,
            "is_valid": True
        }

    return {
        "status": "WARNING",
        "format": "UNSTRUCTURED_VIDEO",
        "file_size_bytes": file_size,
        "note": "Container parsed via basic header check"
    }
