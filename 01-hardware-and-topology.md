# 01. Hardware and topology

## Target setup

This guide assumes:

- **Laptop**: Ubuntu laptop with the **leader** arm connected by USB
- **Pi**: Raspberry Pi 4 running Ubuntu with the **follower** arm connected by USB
- **Network**: laptop and Pi can be on different WiFi networks
- **Software**: LeRobot already installed on the laptop

## Why this architecture is needed

`lerobot-teleoperate` expects a serial port for the follower.
But the follower is physically attached to the Pi, not the laptop.

So we do this:

- On the **Pi**, `pi_hardware_bus.py server` reads and writes the real follower serial port.
- On the **laptop**, `pi_hardware_bus.py client` creates a fake local serial port.
- LeRobot opens the fake local port and talks through the network to the real follower.

## Data flow

```text
Leader arm
  -> /dev/leader on laptop
  -> lerobot-teleoperate
  -> /dev/ttyFOLLOWER on laptop (virtual port)
  -> pi_hardware_bus.py client
  -> Tailscale network
  -> pi_hardware_bus.py server on Pi
  -> /dev/follower on Pi (real USB serial)
  -> Follower arm
```

## Build sequence

Use this order:

1. Plug in each arm and identify the raw USB serial path.
2. Rename ports with `udev` so they become stable.
3. Install Tailscale on both machines.
4. Confirm SSH from laptop to Pi over Tailscale.
5. Run the Python server on the Pi.
6. Run the Python client on the laptop.
7. Run `lerobot-teleoperate` on the laptop.

## Before moving on

You should know which machine owns which arm:

- **Laptop** -> leader
- **Pi** -> follower

If that is not true in your setup, rewrite the port names before following the rest of the guide.
