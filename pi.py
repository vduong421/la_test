#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Receiver Logger (Raspberry Pi or Desktop)

Run this on the RECEIVER machine (the one whose IP is 10.0.0.89).

It:
  - listens on a TCP port
  - when it receives a message "COMMAND_TEXT|sender_timestamp"
  - records the receive time (with milliseconds)
  - appends to receiver_log.csv

Log format (CSV):
  receive_timestamp, command, sender_timestamp_raw

Timestamp format is:
  YYYY-MM-DD HH-MM-SS.mmm
e.g. 2025-12-02 19-06-12.792
"""

# ================== USER CONFIG (EDIT THESE) ==================
# This is the IP of the receiver machine itself (from ipconfig)
RECEIVER_HOST = "10.0.0.89"      # bind only on this address
RECEIVER_PORT = 5000             # Must match PI_PORT in lap.py
RECEIVER_LOG_FILE = "receiver_log.csv"  # Output CSV file on receiver

# Use '-' between time parts so Excel does not auto-reformat as mm:ss
TIME_FORMAT = "%Y-%m-%d %H-%M-%S.%f"    # Same as sender; e.g. 2025-12-02 19-06-12.792

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
    Example: "2025-12-02 19-06-12.260"
    We generate microseconds, then cut to milliseconds.
    """
    now = datetime.now()
    return now.strftime(TIME_FORMAT)[:-3]  # keep only 3 digits of microseconds → milliseconds


def main():
    ensure_log_has_header(RECEIVER_LOG_FILE)

    listen_addr = RECEIVER_HOST
    print(f"Listening on {listen_addr}:{RECEIVER_PORT} ...")

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
