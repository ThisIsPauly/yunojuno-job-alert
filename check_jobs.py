import os
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import re
import html

RSS_URL = os.environ["RSS_URL"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]

SEEN_FILE = "seen_jobs.json"


def safe_header(text):
    """Make text safe to use as an HTTP header."""
    text = str(text)

    # Replace common Unicode punctuation with ASCII equivalents
    replacements = {
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove anything else that can't be encoded in an HTTP header
    text = text.encode("latin-1", "ignore").decode("latin-1")

    return text[:500]


def clean_description(text):
    """Remove HTML and tidy up the RSS description."""
    if not text:
        return ""

    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def send_notification(title, message, url):
    data = f"{message}\n\n{url}".encode("utf-8")

    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=data,
        method="POST",
        headers={
            "Title": safe_header(title),
            "Priority": "high",
            "Tags": "briefcase"
        }
    )

    urllib.request.urlopen(req, timeout=30)


def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(items):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(items), f)


def main():
    seen = load_seen()

    print("Checking YunoJuno RSS feed...")

    with urllib.request.urlopen(RSS_URL, timeout=30) as response:
        xml = response.read()

    root = ET.fromstring(xml)

    items = root.findall(".//item")

    print(f"Found {len(items)} jobs in RSS feed.")

    new_seen = set(seen)

    for item in items:
        title = item.findtext("title", "New YunoJuno job")
        link = item.findtext("link", "")
        description = item.findtext("description", "")

        job_id = link or title

        if job_id not in seen:
            print(f"New job: {title}")

            try:
                send_notification(
                    title,
                    clean_description(description),
                    link
                )
                print("Notification sent.")
            except Exception as e:
                print(f"ERROR sending notification: {e}")
                continue

        new_seen.add(job_id)

    save_seen(new_seen)

    print("Done.")


if __name__ == "__main__":
    main()
