# SO101 Cross-WiFi Teleoperation - Python-Only Guide

This repository explains **one implementation path only** for SO101 cross-WiFi teleoperation:

- **Leader arm** on the Ubuntu laptop
- **Follower arm** on the Raspberry Pi
- **Tailscale** for cross-network access
- **SSH** to manage the Pi
- **`scripts/pi_hardware_bus.py`** on both machines
- **No socat path anywhere in this repo**

The goal is to help someone build this setup **from scratch** without mixing multiple methods.

## What this repo does

The laptop does not talk to the follower arm directly.

Instead:

1. The **Raspberry Pi** opens the follower serial port and publishes it over TCP.
2. The **laptop** connects to that TCP stream.
3. The laptop creates a local pseudo serial port: `/dev/ttyFOLLOWER`.
4. `lerobot-teleoperate` opens `/dev/ttyFOLLOWER` as if the follower were plugged into the laptop.

## Work order

Follow the files in this exact order:

1. `docs/01-hardware-and-topology.md`
2. `docs/02-rename-usb-ports.md`
3. `docs/03-install-tailscale-and-ssh.md`
4. `docs/04-pi-server-setup.md`
5. `docs/05-laptop-client-setup.md`
6. `docs/06-run-teleop.md`
7. `docs/07-troubleshooting.md`

## Repository layout

```text
.
├── README.md
├── docs
│   ├── 01-hardware-and-topology.md
│   ├── 02-rename-usb-ports.md
│   ├── 03-install-tailscale-and-ssh.md
│   ├── 04-pi-server-setup.md
│   ├── 05-laptop-client-setup.md
│   ├── 06-run-teleop.md
│   └── 07-troubleshooting.md
├── scripts
│   └── pi_hardware_bus.py
├── systemd
│   ├── pi-hardware-bus-client.service
│   └── pi-hardware-bus-server.service
└── udev
    └── 99-so101-ports.rules.example
```

## Required final device names

Before running teleop, this guide assumes you have:

- **Laptop leader port**: `/dev/leader`
- **Pi follower port**: `/dev/follower`
- **Laptop virtual follower port**: `/dev/ttyFOLLOWER`

## Final teleop command

Run this on the **laptop** after the Python client is connected:

```bash
lerobot-teleoperate \
  --robot.type so101_follower \
  --robot.port /dev/ttyFOLLOWER \
  --robot.id follower \
  --teleop.type so101_leader \
  --teleop.port /dev/leader \
  --teleop.id leader
```

## Important rule

Do **not** mix this repo with an older `socat` workflow.
This repository is intentionally **Python-only** so the setup path stays deterministic.
