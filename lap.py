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
