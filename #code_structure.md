Here is the folder structure in my root folder
La_test
├── compare.py
├── lap.py
└── pi.py

Here is files code:
compare.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare sender and receiver logs.

It reads:
  - sender_log.csv  (send_timestamp, command)
  - receiver_log.csv (receive_timestamp, command, sender_timestamp_raw)

For each corresponding row, it calculates:
  delay_ms = receive_timestamp - send_timestamp

Output:
  delay_result.csv with columns:
    index, command, send_timestamp, receive_timestamp, delay_ms
"""

# ================== USER CONFIG (EDIT THESE) ==================
SENDER_FILE = "sender_log.csv"        # Path to sender log (copy from laptop if needed)
RECEIVER_FILE = "receiver_log.csv"    # Path to receiver log (copy from Pi if needed)
OUTPUT_FILE = "delay_result.csv"      # Output CSV with delays
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"  # Must match sender/receiver
# =============================================================

import csv
from datetime import datetime

def parse_ts(ts_str: str) -> datetime:
    """
    Parse a timestamp string like "2025-12-02 18:36:05.123"
    The %f directive will accept 3 digits (treated as microseconds).
    """
    # If there are exactly 3 digits after '.', Python still accepts it as microseconds (e.g. 123000)
    return datetime.strptime(ts_str, TIME_FORMAT)

def main():
    with open(SENDER_FILE, newline="", encoding="utf-8") as fs, \
         open(RECEIVER_FILE, newline="", encoding="utf-8") as fr, \
         open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fout:

        sender_reader = csv.reader(fs)
        receiver_reader = csv.reader(fr)
        writer = csv.writer(fout)

        # Skip headers in input files
        try:
            next(sender_reader)  # skip sender header
        except StopIteration:
            print("Sender file seems empty.")
            return

        try:
            next(receiver_reader)  # skip receiver header
        except StopIteration:
            print("Receiver file seems empty.")
            return

        # Write header for output
        writer.writerow(["index", "command", "send_timestamp", "receive_timestamp", "delay_ms"])

        index = 1
        for s_row, r_row in zip(sender_reader, receiver_reader):
            if len(s_row) < 2 or len(r_row) < 2:
                print(f"Skipping row {index} due to missing data.")
                continue

            send_ts_str, cmd_s = s_row[0], s_row[1]
            recv_ts_str, cmd_r = r_row[0], r_row[1]

            if cmd_s != cmd_r:
                print(f"Warning: command mismatch on row {index}: {cmd_s} vs {cmd_r}")

            send_dt = parse_ts(send_ts_str)
            recv_dt = parse_ts(recv_ts_str)

            delay_ms = (recv_dt - send_dt).total_seconds() * 1000.0

            writer.writerow([index, cmd_s, send_ts_str, recv_ts_str, f"{delay_ms:.3f}"])
            index += 1

    print(f"Done. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
```

lap.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sender Button Logger

Run this on your LAPTOP.

When you click the button, it:
  - records the current time (with milliseconds)
  - sends a command to the Raspberry Pi over TCP
  - appends the time + command to sender_log.csv
"""

# ================== USER CONFIG (EDIT THESE) ==================
PI_IP = "172.20.10.5"          # Raspberry Pi IP address on your iPhone hotspot
PI_PORT = 5000                 # TCP port; must match RECEIVER_PORT in receiver_pi.py
COMMAND_TEXT = "BTN1"          # Command label to send when button is pressed
SENDER_LOG_FILE = "sender_log.csv"  # Output CSV file on laptop
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"  # Do not change unless you know what you're doing
# =============================================================

import os
import socket
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk

def ensure_log_has_header(path: str):
    """Create the CSV file with header if it does not exist or is empty."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["send_timestamp", "command"])

def get_timestamp_str() -> str:
    """
    Example: "2025-12-02 18:36:05.123"
    We generate microseconds, then cut to milliseconds.
    """
    now = datetime.now()
    return now.strftime(TIME_FORMAT)[:-3]  # keep only 3 digits of microseconds → milliseconds

def send_command():
    ts = get_timestamp_str()
    message = f"{COMMAND_TEXT}|{ts}"

    # 1) Send to Raspberry Pi
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((PI_IP, PI_PORT))
            s.sendall(message.encode("utf-8"))
    except Exception as e:
        status_var.set(f"Send FAILED at {ts}: {e}")
        return

    # 2) Log to local CSV
    ensure_log_has_header(SENDER_LOG_FILE)
    with open(SENDER_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ts, COMMAND_TEXT])

    status_var.set(f"Sent '{COMMAND_TEXT}' at {ts}")

# ---------- Simple GUI ----------
root = tk.Tk()
root.title("Sender Laptop – Time Logger")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

btn = ttk.Button(main_frame, text="SEND COMMAND", command=send_command)
btn.pack(pady=10)

status_var = tk.StringVar(value="Ready")
status_label = ttk.Label(main_frame, textvariable=status_var)
status_label.pack(pady=5)

root.mainloop()
```

pi.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Receiver Logger (Raspberry Pi)

Run this on your RASPBERRY PI.

It:
  - listens on a TCP port
  - when it receives a message "COMMAND_TEXT|sender_timestamp"
  - records the receive time (with milliseconds)
  - appends to receiver_log.csv
"""

# ================== USER CONFIG (EDIT THESE) ==================
RECEIVER_HOST = ""               # "" = listen on all interfaces (recommended)
RECEIVER_PORT = 5000             # Must match PI_PORT in sender_button.py
RECEIVER_LOG_FILE = "receiver_log.csv"  # Output CSV file on Raspberry Pi
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"    # Same as sender; do not change lightly
PRINT_DEBUG = True               # Set to False to reduce console prints
# =============================================================

import os
import socket
import csv
from datetime import datetime

def ensure_log_has_header(path: str):
    """Create the CSV file with header if it does not exist or is empty."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["receive_timestamp", "command", "sender_timestamp_raw"])

def get_timestamp_str() -> str:
    """
    Example: "2025-12-02 18:36:05.789"
    We generate microseconds, then cut to milliseconds.
    """
    now = datetime.now()
    return now.strftime(TIME_FORMAT)[:-3]  # keep only 3 digits of microseconds → milliseconds

def main():
    ensure_log_has_header(RECEIVER_LOG_FILE)

    print(f"Listening on {RECEIVER_HOST or '0.0.0.0'}:{RECEIVER_PORT} ...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((RECEIVER_HOST, RECEIVER_PORT))
        srv.listen(5)

        while True:
            conn, addr = srv.accept()
            with conn:
                data = conn.recv(1024)
                if not data:
                    continue

                message = data.decode("utf-8").strip()
                # Expected format: "COMMAND_TEXT|sender_timestamp"
                parts = message.split("|", 1)
                if len(parts) == 2:
                    cmd, sender_ts = parts
                else:
                    cmd = message
                    sender_ts = ""

                recv_ts = get_timestamp_str()

                # Log: receive time, command, raw sender time string
                with open(RECEIVER_LOG_FILE, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([recv_ts, cmd, sender_ts])

                if PRINT_DEBUG:
                    print(f"From {addr}: cmd={cmd}, recv={recv_ts}, sender_ts={sender_ts}")

if __name__ == "__main__":
    main()
```
