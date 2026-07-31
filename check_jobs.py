import os
import json
import urllib.request
import xml.etree.ElementTree as ET

RSS_URL = os.environ["RSS_URL"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]

SEEN_FILE = "seen_jobs.json"


def send_notification(title, message, url):
    data = f"{title}\n\n{message}\n\n{url}".encode("utf-8")

    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=data,
        method="POST",
        headers={
            "Title": title,
            "Priority": "high",
            "Tags": "briefcase"
        }
    )

    urllib.request.urlopen(req)


def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_seen(items):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(items), f)


def main():
    seen = load_seen()

    with urllib.request.urlopen(RSS_URL) as response:
        xml = response.read()

    root = ET.fromstring(xml)

    new_seen = set(seen)

    for item in root.findall(".//item"):
        title = item.findtext("title", "New YunoJuno job")
        link = item.findtext("link", "")
        description = item.findtext("description", "")

        job_id = link or title

        if job_id not in seen:
            send_notification(
                title,
                description[:500],
                link
            )

        new_seen.add(job_id)

    save_seen(new_seen)


if __name__ == "__main__":
    main()
