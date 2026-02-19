from datetime import date

# ---------------------------------------------------------------------------
# Anchor lesson: set these two values to tell the program where to start
# counting lessons from.
#
# ANCHOR_LESSON_NUMBER : the lesson number you know (e.g. 11)
# ANCHOR_LESSON_SUNDAY : the date of the Sunday that started that lesson
#                        Format: date(YEAR, MONTH, DAY)
# ---------------------------------------------------------------------------
ANCHOR_LESSON_NUMBER = 11
ANCHOR_LESSON_SUNDAY = date(2025, 6, 1)  # <-- Replace with the actual Sunday date for lesson 11

# ---------------------------------------------------------------------------
# Audio settings
# ---------------------------------------------------------------------------
AUDIO_EXTENSION = ".mp3"

# ---------------------------------------------------------------------------
# Folder paths (relative to where you run the script)
# ---------------------------------------------------------------------------
AUDIO_FILES_DIR = "audio_files"
OUTPUT_DIR = "output"
