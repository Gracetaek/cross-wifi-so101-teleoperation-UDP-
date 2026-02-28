# 07. Troubleshooting

## 1. `/dev/leader` or `/dev/follower` does not exist

Cause:

- udev rule not applied correctly
- wrong USB cable/device selected
- rule matched the wrong attributes

Check:

```bash
udevadm info -a -n /dev/ttyACM0
ls -l /dev/leader
ls -l /dev/follower
```

Fix:

- re-check the values used in the udev rule
- reload rules with `sudo udevadm control --reload-rules && sudo udevadm trigger`
- unplug and reconnect the USB cable

## 2. SSH to the Pi fails over Tailscale

Check:

```bash
tailscale ip -4
sudo systemctl status ssh --no-pager
ping <PI_TAILSCALE_IP>
```

Fix:

- make sure both machines joined the same tailnet
- make sure SSH is enabled on the Pi
- retry using the current Pi Tailscale IP

## 3. Pi server says it cannot open `/dev/follower`

Cause:

- wrong device name
- another process already owns the port
- permission problem

Check:

```bash
ls -l /dev/follower
lsof /dev/follower
```

Fix:

- stop the competing process
- verify the symlink points to the real device
- run the server with `sudo`

## 4. Laptop client cannot create `/dev/ttyFOLLOWER`

Cause:

- no permission to create a symlink in `/dev`

Fix:

Run the client with `sudo`:

```bash
sudo python3 scripts/pi_hardware_bus.py client --remote-host <PI_TAILSCALE_IP>
```

## 5. Laptop client cannot connect to the Pi

Check on the Pi:

```bash
ss -lntp | grep 5500
```

Fix:

- make sure the server is running
- verify the Pi Tailscale IP is correct
- verify port `5500` matches on both sides

## 6. `lerobot-teleoperate` starts but the follower does not respond correctly

Check:

- leader really uses `/dev/leader`
- follower really uses `/dev/ttyFOLLOWER`
- local teleop worked before trying cross-WiFi
- calibration, center, and scale values are already correct

This repo only covers the **transport path** from laptop to Pi.
If joint ranges or pose mapping are wrong, that is a separate calibration issue.

## 7. Connection drops during teleop

Likely cause:

- unstable WiFi or internet path

Fix:

- reduce network congestion
- keep Pi on stable power
- keep Tailscale session active
- use the provided client service if you want automatic reconnect behavior
