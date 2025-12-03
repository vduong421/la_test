#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sender Key Listener Logger (Laptop)

Run this on your LAPTOP.

When you press any printable key (w, k, 1, space, etc) while this window
is focused, it:
  - uses the key itself as the command label (e.g. "w", "k")
  - records the current time (with milliseconds)
  - sends the command + time to the receiver over TCP
  - appends the time + command to sender_log.csv
"""

# ================== USER CONFIG (EDIT THESE) ==================
PI_IP = "10.0.0.89"          # Receiver IP address (desktop or Pi)
PI_PORT = 5000                 # TCP port; must match RECEIVER_PORT in pi.py

SENDER_LOG_FILE = "sender_log.csv"    # Output CSV file on laptop
# Use '-' between time parts so Excel does not auto-reformat
TIME_FORMAT = "%Y-%m-%d %H-%M-%S.%f"  # e.g. 2025-12-02 19-06-12.792
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
    Example: "2025-12-02 19-06-12.792"
    We generate microseconds, then cut to milliseconds.
    """
    now = datetime.now()
    return now.strftime(TIME_FORMAT)[:-3]  # keep only 3 digits of microseconds → milliseconds

def send_command(command: str):
    ts = get_timestamp_str()
    message = f"{command}|{ts}"

    # 1) Send to receiver
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
        writer.writerow([ts, command])

    status_var.set(f"Sent '{command}' at {ts}")

def on_key(event):
    """
    Key event handler.
    - event.char is the character produced by the key, or '' for non-printable keys.
    """
    key = event.char
    if not key:
        # Ignore keys that don't produce a printable character (Ctrl, Shift, arrows, etc.)
        return

    # Use the key itself as the command name
    command = key
    send_command(command)

# ---------- Simple GUI ----------
root = tk.Tk()
root.title("Laptop – Key Listener Time Logger")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

info_label = ttk.Label(
    main_frame,
    text=(
        "Focus this window and press any key.\n"
        "The exact key you press will be sent and logged\n"
        "as the 'command' (e.g., 'w', 'k', '1')."
    )
)
info_label.pack(pady=10)

status_var = tk.StringVar(value="Ready – press a key")
status_label = ttk.Label(main_frame, textvariable=status_var)
status_label.pack(pady=5)

# Bind key events
root.bind("<Key>", on_key)
root.focus_set()

root.mainloop()
