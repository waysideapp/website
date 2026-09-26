#!/usr/bin/env python3
"""Build Wayside's community camera database from Lufop.net's EU archive.

Reads the GB files out of Lufop-Zones-de-danger-EU-CSV.zip and writes, beside this
script, gb-cameras.zip (one CSV in the lon,lat,rule,description shape the app's
LufopParser reads) and manifest.json. Standard library only.

    python3 build.py                      fetch from lufop.net and build
    python3 build.py --source file.zip    build from a copy already on disk
"""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SOURCE_URL = "https://lufop.net/wp-content/plugins/downloads-manager/upload/Lufop-Zones-de-danger-EU-CSV.zip"
ARCHIVE_NAME = "gb-cameras.zip"
ENTRY_NAME = "gb-cameras.csv"
MANIFEST_NAME = "manifest.json"

MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_ENTRY_BYTES = 16 * 1024 * 1024

# Lufop names each file <country><kind><country><limit>.csv, e.g. GBFixeGB30.csv or GBFeuRougeGB.csv.
FILE_PATTERN = re.compile(r"^([A-Z]{2})(Fixe|FeuRouge|Troncondebut|Tronconfin|Tunnel)([A-Z]{2})(\d+)?\.csv$", re.IGNORECASE)
ROW_PATTERN = re.compile(r"^(-?\d*(?:\.\d*)?)\s*,\s*(-?\d*(?:\.\d*)?)\s*,\s*(.*)$")


def fetch(url, destination):
    # lufop.net sits behind Cloudflare, which lets a plain curl through from GitHub's runners
    # but not from every network; the same user agent Open-GATSO-POI's build uses.
    command = [
        "curl", "-fsSL", "--retry", "3", "--retry-delay", "5", "--retry-all-errors",
        "--max-time", "300", "--max-filesize", str(MAX_SOURCE_BYTES),
        "-A", "Mozilla/5.0", "-D", destination + ".headers", "-o", destination, url,
    ]
    subprocess.run(command, check=True)
    with open(destination + ".headers", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            name, _, value = line.partition(":")
            if name.strip().lower() == "last-modified":
                try:
                    return parsedate_to_datetime(value.strip()).astimezone(timezone.utc)
                except (TypeError, ValueError):
                    return None
    return None


def unescape(comment):
    quote = comment[:1]
    if quote not in ('"', "'"):
        return comment
    return comment.strip(quote).replace(quote + quote, quote)


def quote(field):
    return '"' + field.replace('"', '""') + '"'


def read_rows(archive, country):
    rows = set()
    files = []
    ignored = []
    newest = None
    for info in archive.infolist():
        name = os.path.basename(info.filename)
        match = FILE_PATTERN.match(name)
        if not match or match.group(1).upper() != country:
            continue
        kind = match.group(2).lower()
        limit = match.group(4)
        if kind == "fixe":
            rule = "max @" + limit if limit else "max"
        elif kind == "feurouge":
            rule = "stop"
        else:
            ignored.append(name)
            continue
        if info.file_size > MAX_ENTRY_BYTES:
            sys.exit(f"{name} declares {info.file_size} bytes, more than {MAX_ENTRY_BYTES}.")
        data = archive.read(info)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        count = 0
        for line in text.splitlines():
            row = ROW_PATTERN.match(line)
            if not row:
                continue
            longitude, latitude, comment = row.group(1).strip(), row.group(2).strip(), row.group(3).strip()
            try:
                if not (-90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180):
                    continue
            except ValueError:
                continue
            description = unescape(comment)
            if not description.startswith(country + " "):
                description = country + " " + description
            rows.add(f"{longitude},{latitude},{quote(rule)},{quote(description)}")
            count += 1
        files.append({"name": name, "rows": count})
        modified = datetime(*info.date_time, tzinfo=timezone.utc)
        if newest is None or modified > newest:
            newest = modified
    return sorted(rows), files, ignored, newest


def build(source, out_dir, country, minimum):
    checked_at = datetime.now(timezone.utc).replace(microsecond=0)
    with tempfile.TemporaryDirectory() as workspace:
        if re.match(r"^https?://", source):
            path = os.path.join(workspace, "source.zip")
            data_date = fetch(source, path)
        else:
            path = source
            data_date = datetime.fromtimestamp(os.path.getmtime(path), timezone.utc)
        if not zipfile.is_zipfile(path):
            sys.exit(f"{source} is not a ZIP archive. lufop.net may have answered with its bot challenge instead of the file.")
        with zipfile.ZipFile(path) as archive:
            rows, files, ignored, newest_entry = read_rows(archive, country)

    if data_date is None:
        data_date = newest_entry or checked_at
    data_date = data_date.replace(microsecond=0)

    fixed = sum(1 for row in rows if ',"max' in row)
    red_light = sum(1 for row in rows if ',"stop",' in row)
    if len(rows) < minimum or fixed == 0 or red_light == 0:
        sys.exit(f"Only {len(rows)} {country} cameras ({fixed} fixed, {red_light} red light); expected at least {minimum} of both kinds. Not publishing.")

    csv_bytes = ("\n".join(rows) + "\n").encode("utf-8")
    limits = {}
    for row in rows:
        found = re.search(r'"max @(\d+)"', row)
        if found:
            limits[found.group(1)] = limits.get(found.group(1), 0) + 1

    # The entry date is what the app shows as the build date, and a fixed date keeps the
    # archive byte-identical between runs when the data has not changed.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo(ENTRY_NAME, date_time=data_date.timetuple()[:6])
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, csv_bytes, compresslevel=9)
    archive_bytes = buffer.getvalue()

    manifest = {
        "dataDate": data_date.isoformat().replace("+00:00", "Z"),
        "checkedAt": checked_at.isoformat().replace("+00:00", "Z"),
        "cameras": len(rows),
        "fixedSpeed": fixed,
        "redLight": red_light,
        "speedLimitsMph": {key: limits[key] for key in sorted(limits, key=int)},
        "files": files,
        "ignoredFiles": ignored,
        "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "source": source if re.match(r"^https?://", source) else SOURCE_URL,
        "attribution": "© Lufop.net, CC BY-SA 4.0",
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, ARCHIVE_NAME), "wb") as handle:
        handle.write(archive_bytes)
    with open(os.path.join(out_dir, MANIFEST_NAME), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    summary = (
        f"| | |\n|---|---|\n| Data date | {manifest['dataDate']} |\n| Cameras | {len(rows)} |\n"
        f"| Fixed speed | {fixed} |\n| Red light | {red_light} |\n| Files | {', '.join(f['name'] for f in files)} |\n"
    )
    if ignored:
        summary += f"| Ignored | {', '.join(ignored)} |\n"
    print(summary)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write("## Community database\n\n" + summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=SOURCE_URL, help="URL or path of Lufop's EU archive")
    parser.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)), help="directory to write into")
    parser.add_argument("--country", default="GB", help="two-letter country code of the files to keep")
    parser.add_argument("--min-cameras", type=int, default=4000, help="refuse to publish fewer cameras than this")
    args = parser.parse_args()
    build(args.source, args.out, args.country.upper(), args.min_cameras)


if __name__ == "__main__":
    main()
