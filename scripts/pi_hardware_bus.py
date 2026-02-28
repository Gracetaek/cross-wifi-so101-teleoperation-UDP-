#!/usr/bin/env python3
"""
pi_hardware_bus.py

Single-path Python bridge for SO101 cross-WiFi teleoperation.

This file supports two modes:

1) server
   Run on the Raspberry Pi. It exposes the follower serial port over TCP.

2) client
   Run on the laptop. It connects to the Pi over TCP and creates a local
   pseudo-terminal, for example /dev/ttyFOLLOWER. LeRobot then opens that local
   pseudo-terminal as if the follower were connected by USB.

Examples
--------
Pi side:
    sudo python3 pi_hardware_bus.py server \
      --serial-port /dev/follower \
      --baud 1000000 \
      --listen-host 0.0.0.0 \
      --listen-port 5500

Laptop side:
    sudo python3 pi_hardware_bus.py client \
      --remote-host 100.x.y.z \
      --remote-port 5500 \
      --link-path /dev/ttyFOLLOWER
"""

from __future__ import annotations

import argparse
import logging
import os
import pty
import select
import signal
import socket
import sys
import termios
import threading
import time
from pathlib import Path

try:
    import serial
except ImportError as exc:
    raise SystemExit(
        "pyserial is required. Install it with: python3 -m pip install --user pyserial"
    ) from exc


def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return ivalue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Python-only TCP/serial bridge for SO101 cross-WiFi teleoperation."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level. Default: INFO",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    server = subparsers.add_parser("server", help="Expose a serial port over TCP on the Pi")
    server.add_argument("--serial-port", required=True, help="Serial device path on the Pi")
    server.add_argument("--baud", type=positive_int, default=1_000_000, help="Serial baud rate")
    server.add_argument("--serial-timeout", type=float, default=0.01, help="Serial timeout seconds")
    server.add_argument("--listen-host", default="0.0.0.0", help="TCP bind host")
    server.add_argument("--listen-port", type=positive_int, default=5500, help="TCP bind port")

    client = subparsers.add_parser("client", help="Create a local PTY and connect it to the Pi")
    client.add_argument("--remote-host", required=True, help="Pi Tailscale IP or DNS name")
    client.add_argument("--remote-port", type=positive_int, default=5500, help="Pi TCP port")
    client.add_argument(
        "--link-path",
        default="/dev/ttyFOLLOWER",
        help="Stable symlink path for the local PTY. Default: /dev/ttyFOLLOWER",
    )
    client.add_argument(
        "--reconnect-delay",
        type=float,
        default=2.0,
        help="Seconds between reconnect attempts. Default: 2.0",
    )

    return parser


class ShutdownFlag:
    def __init__(self) -> None:
        self._event = threading.Event()

    def set(self) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set()

    def wait(self, seconds: float) -> bool:
        return self._event.wait(seconds)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def install_signal_handlers(stop: ShutdownFlag) -> None:
    def _handler(signum, frame):  # type: ignore[no-untyped-def]
        logging.info("Received signal %s, shutting down.", signum)
        stop.set()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def run_server(args: argparse.Namespace, stop: ShutdownFlag) -> int:
    try:
        ser = serial.Serial(
            port=args.serial_port,
            baudrate=args.baud,
            timeout=args.serial_timeout,
            write_timeout=args.serial_timeout,
            exclusive=True,
        )
    except serial.SerialException as exc:
        logging.error("Failed to open serial port %s: %s", args.serial_port, exc)
        return 1

    logging.info("Opened %s at %d baud", args.serial_port, args.baud)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            server.bind((args.listen_host, args.listen_port))
            server.listen(1)
            server.settimeout(1.0)
            logging.info("Listening on %s:%d", args.listen_host, args.listen_port)

            while not stop.is_set():
                try:
                    conn, address = server.accept()
                except socket.timeout:
                    continue
                except OSError as exc:
                    if stop.is_set():
                        break
                    logging.error("Accept failed: %s", exc)
                    continue

                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                logging.info("Client connected from %s:%s", address[0], address[1])
                session_result = handle_serial_socket_session(ser, conn, stop)
                if session_result != 0 and stop.is_set():
                    break

    finally:
        try:
            ser.close()
        except Exception:
            pass
        logging.info("Serial port closed.")

    return 0


def handle_serial_socket_session(ser: serial.Serial, conn: socket.socket, stop: ShutdownFlag) -> int:
    conn.settimeout(0.05)
    try:
        while not stop.is_set():
            try:
                net_data = conn.recv(4096)
                if net_data:
                    ser.write(net_data)
                    ser.flush()
                else:
                    logging.info("Client disconnected.")
                    break
            except socket.timeout:
                pass
            except OSError as exc:
                logging.error("TCP receive failed: %s", exc)
                break

            try:
                serial_data = ser.read(4096)
                if serial_data:
                    conn.sendall(serial_data)
            except serial.SerialException as exc:
                logging.error("Serial read/write failed: %s", exc)
                return 1
            except OSError as exc:
                logging.error("TCP send failed: %s", exc)
                break
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()
        logging.info("Session ended.")
    return 0


def ensure_parent_exists(path: Path) -> None:
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")


def configure_slave_raw_mode(slave_fd: int) -> None:
    attrs = termios.tcgetattr(slave_fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = attrs[2] | termios.CREAD | termios.CLOCAL | termios.CS8
    attrs[3] = 0
    attrs[6][termios.VMIN] = 1
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)


def create_linked_pty(link_path: str) -> tuple[int, int, str]:
    master_fd, slave_fd = pty.openpty()
    configure_slave_raw_mode(slave_fd)
    slave_name = os.ttyname(slave_fd)

    link = Path(link_path)
    ensure_parent_exists(link)

    if link.exists() or link.is_symlink():
        link.unlink()
    os.symlink(slave_name, link)
    os.chmod(slave_name, 0o666)

    logging.info("Created PTY slave %s", slave_name)
    logging.info("Created stable symlink %s -> %s", link_path, slave_name)
    return master_fd, slave_fd, slave_name


def cleanup_link(link_path: str, slave_fd: int, master_fd: int) -> None:
    try:
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.unlink(link_path)
    except OSError:
        pass
    for fd in (slave_fd, master_fd):
        try:
            os.close(fd)
        except OSError:
            pass


def open_tcp_client(remote_host: str, remote_port: int) -> socket.socket:
    conn = socket.create_connection((remote_host, remote_port), timeout=5)
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    conn.setblocking(False)
    return conn


def run_client(args: argparse.Namespace, stop: ShutdownFlag) -> int:
    try:
        master_fd, slave_fd, slave_name = create_linked_pty(args.link_path)
    except OSError as exc:
        logging.error("Failed to create PTY link %s: %s", args.link_path, exc)
        return 1

    try:
        while not stop.is_set():
            try:
                logging.info(
                    "Connecting to %s:%d ...", args.remote_host, args.remote_port
                )
                conn = open_tcp_client(args.remote_host, args.remote_port)
                logging.info("Connected to Pi. Local follower port is %s", args.link_path)
                bridge_pty_and_socket(master_fd, conn, stop)
            except (ConnectionError, OSError, socket.timeout) as exc:
                if stop.is_set():
                    break
                logging.warning("Connection failed or dropped: %s", exc)
                logging.info("Retrying in %.1f seconds", args.reconnect_delay)
                stop.wait(args.reconnect_delay)
    finally:
        cleanup_link(args.link_path, slave_fd, master_fd)
        logging.info("Removed %s and closed PTY %s", args.link_path, slave_name)

    return 0


def bridge_pty_and_socket(master_fd: int, conn: socket.socket, stop: ShutdownFlag) -> None:
    try:
        while not stop.is_set():
            read_fds, _, _ = select.select([master_fd, conn], [], [], 0.1)

            if master_fd in read_fds:
                try:
                    pty_data = os.read(master_fd, 4096)
                    if pty_data:
                        conn.sendall(pty_data)
                except OSError as exc:
                    logging.error("PTY -> TCP forwarding failed: %s", exc)
                    break

            if conn in read_fds:
                try:
                    net_data = conn.recv(4096)
                    if not net_data:
                        logging.warning("Pi closed the TCP connection.")
                        break
                    os.write(master_fd, net_data)
                except OSError as exc:
                    logging.error("TCP -> PTY forwarding failed: %s", exc)
                    break
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(args.log_level)
    stop = ShutdownFlag()
    install_signal_handlers(stop)

    if args.mode == "server":
        return run_server(args, stop)
    if args.mode == "client":
        return run_client(args, stop)

    parser.error("Unknown mode")
    return 2


if __name__ == "__main__":
    sys.exit(main())
