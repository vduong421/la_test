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
