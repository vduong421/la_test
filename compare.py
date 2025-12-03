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
