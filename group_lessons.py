import os
import re
import csv
import shutil
from datetime import date, timedelta

from mutagen.mp3 import MP3

PARTIAL_THRESHOLD_SECONDS = 60 * 60  # 1 hour — recordings shorter than this are flagged as Partial

from config import (
    ANCHOR_LESSON_NUMBER,
    ANCHOR_LESSON_SUNDAY,
    AUDIO_EXTENSION,
    AUDIO_FILES_DIR,
    OUTPUT_DIR,
)

# Build absolute paths relative to this script's location
# so the script works no matter which folder you run it from
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILES_DIR = os.path.join(SCRIPT_DIR, AUDIO_FILES_DIR)
OUTPUT_DIR = os.path.join(SCRIPT_DIR, OUTPUT_DIR)

# The three expected meeting days per lesson week, in order
EXPECTED_DAYS = ["Sunday", "Monday", "Tuesday"]


def get_lesson_sunday(file_date):
    """Return the Sunday that started the lesson week for a given date."""
    # Python weekday(): Monday=0 ... Saturday=5, Sunday=6
    days_since_sunday = (file_date.weekday() + 1) % 7
    return file_date - timedelta(days=days_since_sunday)


def calculate_lesson_number(file_date):
    """Calculate which lesson number a date belongs to."""
    lesson_sunday = get_lesson_sunday(file_date)
    weeks_offset = (lesson_sunday - ANCHOR_LESSON_SUNDAY).days // 7
    return ANCHOR_LESSON_NUMBER + weeks_offset


def parse_filename(filename):
    """
    Extract the date and code number from a filename.
    Expected format: 2025-06-01-#274.mp3
    Returns (date, code_string) or (None, None) if the format doesn't match.
    """
    pattern = r"^(\d{4}-\d{2}-\d{2})-#(\d+)"
    match = re.match(pattern, filename)
    if not match:
        return None, None
    date_str, code = match.groups()
    year, month, day = map(int, date_str.split("-"))
    return date(year, month, day), code


def get_duration_seconds(filepath):
    """Return the duration of an MP3 file in seconds, or None if it can't be read."""
    try:
        audio = MP3(filepath)
        return audio.info.length
    except Exception:
        return None


def format_duration(seconds):
    """Format a duration in seconds as h:mm:ss."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:02d}"


def get_day_name(file_date):
    """Return the day of the week as a string."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[file_date.weekday()]


def is_already_processed(lesson_num, filename):
    """Return True if this file already exists in the output lesson folder."""
    folder_name = f"lesson_{lesson_num:02d}"
    output_path = os.path.join(OUTPUT_DIR, folder_name, filename)
    return os.path.exists(output_path)


def main():
    print(f"Scanning '{AUDIO_FILES_DIR}' for {AUDIO_EXTENSION} files...\n")

    # Group recordings by lesson number
    # Structure: { lesson_number: [ { filename, date, day, code }, ... ] }
    lessons = {}
    skipped = []

    for filename in sorted(os.listdir(AUDIO_FILES_DIR)):
        if not filename.lower().endswith(AUDIO_EXTENSION):
            continue

        file_date, code = parse_filename(filename)
        if file_date is None:
            skipped.append(filename)
            continue

        lesson_num = calculate_lesson_number(file_date)
        day_name = get_day_name(file_date)
        filepath = os.path.join(AUDIO_FILES_DIR, filename)
        duration = get_duration_seconds(filepath)
        duplicate = is_already_processed(lesson_num, filename)

        if lesson_num not in lessons:
            lessons[lesson_num] = []

        lessons[lesson_num].append({
            "filename": filename,
            "date": file_date,
            "day": day_name,
            "code": code,
            "duration": duration,
            "is_duplicate": duplicate,
        })

    if not lessons:
        print("No audio files found. Add .mp3 files to the audio_files/ folder and try again.")
        return

    # Copy files into lesson subfolders under output/
    print("Copying files into lesson folders...\n")
    for lesson_num in sorted(lessons.keys()):
        folder_name = f"lesson_{lesson_num:02d}"
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        for recording in lessons[lesson_num]:
            if recording["day"] not in EXPECTED_DAYS:
                continue
            if recording["is_duplicate"]:
                print(f"  {recording['filename']}  ->  already processed, skipping")
                continue
            src = os.path.join(AUDIO_FILES_DIR, recording["filename"])
            dst = os.path.join(folder_path, recording["filename"])
            shutil.copy2(src, dst)
            print(f"  {recording['filename']}  ->  {folder_name}/")

    # Generate CSV report
    report_path = os.path.join(OUTPUT_DIR, "report.csv")
    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Lesson", "Day", "Date", "Code", "Filename", "Duration", "Status"])

        for lesson_num in sorted(lessons.keys()):
            recordings = lessons[lesson_num]
            days_present = {r["day"]: r for r in recordings}

            # Calculate the Sunday for this lesson
            lesson_sunday = ANCHOR_LESSON_SUNDAY + timedelta(
                weeks=(lesson_num - ANCHOR_LESSON_NUMBER)
            )

            for i, day in enumerate(EXPECTED_DAYS):
                expected_date = lesson_sunday + timedelta(days=i)
                if day in days_present:
                    r = days_present[day]
                    duration = r["duration"]
                    duration_str = format_duration(duration) if duration is not None else ""
                    if r["is_duplicate"]:
                        status = "Already processed"
                    elif duration is None:
                        status = "Present (duration unknown)"
                    elif duration < PARTIAL_THRESHOLD_SECONDS:
                        status = "Partial"
                    else:
                        status = "Present"
                    writer.writerow([lesson_num, day, r["date"], f"#{r['code']}", r["filename"], duration_str, status])
                else:
                    writer.writerow([lesson_num, day, expected_date, "", "", "", "Missing"])

            # Report recordings that fell on unexpected days (not copied to output)
            for r in recordings:
                if r["day"] not in EXPECTED_DAYS:
                    duration = r["duration"]
                    duration_str = format_duration(duration) if duration is not None else ""
                    writer.writerow([lesson_num, r["day"], r["date"], f"#{r['code']}", r["filename"], duration_str, "Unexpected day (not copied)"])

    print(f"\nReport saved to: {report_path}")
    print(f"Lessons found:   {sorted(lessons.keys())}")

    if skipped:
        print(f"\nSkipped (unrecognized filename format):")
        for name in skipped:
            print(f"  {name}")


if __name__ == "__main__":
    main()
