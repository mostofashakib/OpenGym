#!/usr/bin/env python3
import argparse
import json
import random
import sys
from datetime import datetime, timezone

try:
    from faker import Faker
except ImportError:
    class Faker:
        _first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Jamie"]
        _last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson"]

        @classmethod
        def seed(cls, seed_val: Any) -> None:
            pass

        def first_name(self) -> str:
            return random.choice(self._first_names)

        def last_name(self) -> str:
            return random.choice(self._last_names)


EPOCH_BASE_MS = 1700000000000


def iso_from_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def next_ts(step=[0]) -> int:
    # increment by 5-35 minutes randomly
    step[0] += int((random.random() * 30 + 5) * 60_000)
    return EPOCH_BASE_MS + step[0]


def nanoid(n: int = 8) -> str:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(alphabet) for _ in range(n))


def make_address(fake: Faker, name: str) -> str:
    user = name.lower().replace(" ", ".")
    domain = random.choice(["example.com", "company.com", "startup.io", "mail.test", "corp.co"])
    return f"{user}@{domain}"


def generate_state(seed: str = "gmail", threads: int = 8, singles: int = 12, max_messages_per_thread: int = 4):
    fake = Faker()
    Faker.seed(seed)
    random.seed(str(seed))

    system_labels = [
        {"id": "INBOX", "name": "INBOX", "type": "SYSTEM"},
        {"id": "SENT", "name": "SENT", "type": "SYSTEM"},
        {"id": "DRAFTS", "name": "DRAFTS", "type": "SYSTEM"},
        {"id": "TRASH", "name": "TRASH", "type": "SYSTEM"},
        {"id": "SPAM", "name": "SPAM", "type": "SYSTEM"},
        {"id": "ARCHIVE", "name": "ARCHIVE", "type": "SYSTEM"},
        {"id": "STARRED", "name": "STARRED", "type": "SYSTEM"},
        {"id": "IMPORTANT", "name": "IMPORTANT", "type": "SYSTEM"},
    ]
    user_labels = [
        {"id": "work", "name": "work", "type": "USER"},
        {"id": "personal", "name": "personal", "type": "USER"},
        {"id": "receipts", "name": "receipts", "type": "USER"},
        {"id": "travel", "name": "travel", "type": "USER"},
        {"id": "important", "name": "important", "type": "USER"},
    ]

    subjects = [
        "Project update",
        "Meeting follow-up",
        "Invoice attached",
        "Welcome!",
        "Your order confirmation",
        "Vacation plans",
        "Quarterly results",
        "Action required",
        "Event invitation",
        "Thanks for your time",
        "Shipping notice",
        "Reset your password",
        "Introductions",
        "Re: Quick question",
        "Weekly digest",
    ]

    bodies = [
        "Hi there, just checking in on the latest status. Let me know if you have any questions.",
        "Please find the attached document and share your feedback when you have a moment.",
        "Thanks again for the meeting today — I appreciated the discussion and next steps.",
        "This is a friendly reminder about the upcoming deadline. We are almost there!",
        "I wanted to share the updates we discussed. Everything is on track.",
        "Congratulations on the milestone! Looking forward to the next phase.",
    ]

    messages = []
    threads_arr = []

    # Threaded conversations
    for _ in range(int(threads)):
        thread_id = nanoid(8)
        subject = random.choice(subjects)
        if random.random() < 0.6:
            subject = f"{subject} - Q{random.randint(1,4)}"
        participants = {"You"}
        msg_ids = []
        count = 2 + random.randint(0, max(1, int(max_messages_per_thread) - 1))
        last_activity_iso = ""
        prev_mid = None
        for _m in range(count):
            sender_is_you = random.random() < 0.5
            sender_name = "You" if sender_is_you else f"{fake.first_name()} {fake.last_name()}"
            if sender_name != "You":
                participants.add(sender_name)
            sender_email = "you@example.com" if sender_is_you else make_address(fake, sender_name)
            # To field: alternate
            if sender_is_you:
                other = next(iter(p for p in participants if p != "You"), None) or f"{fake.first_name()} {fake.last_name()}"
                to_field = [f"{other} <{make_address(fake, other)}>" ]
            else:
                to_field = ["You <you@example.com>"]
            mid = nanoid(8)
            date_iso = iso_from_ms(next_ts())
            last_activity_iso = date_iso
            label_ids = ["SENT"] if sender_is_you else (["INBOX"] if random.random() < 0.8 else ["ARCHIVE"])
            if random.random() < 0.2:
                label_ids.append("STARRED")
            if random.random() < 0.25:
                label_ids.append(random.choice(user_labels)["id"])
            # Optional cc/bcc sprinkling
            cc_field = [f"{fake.first_name()} {fake.last_name()} <{make_address(fake, fake.first_name() + ' ' + fake.last_name())}>"] if random.random() < 0.2 else []
            bcc_field = [f"{fake.first_name()} {fake.last_name()} <{make_address(fake, fake.first_name() + ' ' + fake.last_name())}>"] if random.random() < 0.15 else []

            msg = {
                "id": mid,
                "threadId": thread_id,
                **({"replyToId": prev_mid} if prev_mid else {}),
                "from": f"{sender_name} <{sender_email}>",
                "to": to_field,
                **({"cc": cc_field} if cc_field else {}),
                **({"bcc": bcc_field} if bcc_field else {}),
                "subject": subject,
                "date": date_iso,
                "text": random.choice(bodies),
                "attachments": [],
                "labelIds": label_ids,
                "isRead": True if sender_is_you else bool(random.random() < 0.5),
                "isStarred": "STARRED" in label_ids,
                "isImportant": bool(random.random() < 0.15),
                "snoozeUntil": None,
            }
            messages.append(msg)
            msg_ids.append(mid)
            prev_mid = mid
        threads_arr.append({
            "id": thread_id,
            "subject": subject,
            "participants": list(participants),
            "messageIds": msg_ids,
            "lastActivity": last_activity_iso,
            "isStarred": any((m for m in messages if m["id"] in msg_ids and m["isStarred"]))
        })

    # Standalone messages
    for _ in range(int(singles)):
        standalone_id = nanoid(8)
        sender_name = f"{fake.first_name()} {fake.last_name()}"
        sender_email = make_address(fake, sender_name)
        subject = random.choice(subjects)
        date_iso = iso_from_ms(next_ts())
        label_ids = ["INBOX"] if random.random() < 0.85 else ["ARCHIVE"]
        if random.random() < 0.2:
            label_ids.append("STARRED")
        if random.random() < 0.25:
            label_ids.append(random.choice(user_labels)["id"])
        # Optional cc/bcc sprinkling for single messages
        cc_field = [f"{fake.first_name()} {fake.last_name()} <{make_address(fake, fake.first_name() + ' ' + fake.last_name())}>"] if random.random() < 0.25 else []
        bcc_field = [f"{fake.first_name()} {fake.last_name()} <{make_address(fake, fake.first_name() + ' ' + fake.last_name())}>"] if random.random() < 0.2 else []

        messages.append({
            "id": standalone_id,
            "threadId": standalone_id,
            "from": f"{sender_name} <{sender_email}>",
            "to": ["you@example.com"],
            **({"cc": cc_field} if cc_field else {}),
            **({"bcc": bcc_field} if bcc_field else {}),
            "subject": subject,
            "date": date_iso,
            "text": random.choice(bodies),
            "attachments": [],
            "labelIds": label_ids,
            "isRead": bool(random.random() < 0.5),
            "isStarred": "STARRED" in label_ids,
            "isImportant": bool(random.random() < 0.15),
            "snoozeUntil": None,
        })

    state = {
        "messages": messages,
        "threads": threads_arr,
        "labels": system_labels + user_labels,
        "settings": {"displayName": "You", "signature": "", "email": "you@example.com"},
        "contacts": {},
    }
    return state


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="gmail")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--singles", type=int, default=12)
    ap.add_argument("--maxMessagesPerThread", type=int, default=4)
    ap.add_argument("-o", "--output", default="-")  # '-' = stdout
    args = ap.parse_args()

    state = generate_state(
        seed=args.seed,
        threads=args.threads,
        singles=args.singles,
        max_messages_per_thread=args.maxMessagesPerThread,
    )

    if args.output == "-":
        json.dump(state, sys.stdout, ensure_ascii=True, indent=2)
        if sys.stdout.isatty():
            sys.stdout.write("\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=True, indent=2)
        print(args.output)


