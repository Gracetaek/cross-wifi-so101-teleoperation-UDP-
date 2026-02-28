# 05. Laptop client setup

This step runs the **client mode** of `pi_hardware_bus.py` on the laptop.

The client connects to the Pi server and creates a local virtual serial port:

- `/dev/ttyFOLLOWER`

LeRobot will use that path for the follower.

## Step 1: install Python dependency on the laptop

```bash
python3 -m pip install --user pyserial
```

## Step 2: confirm the leader port exists

```bash
ls -l /dev/leader
```

Do not continue until this path exists.

## Step 3: run client mode manually

From the laptop:

```bash
sudo python3 scripts/pi_hardware_bus.py client \
  --remote-host <PI_TAILSCALE_IP> \
  --remote-port 5500 \
  --link-path /dev/ttyFOLLOWER
```

Example:

```bash
sudo python3 scripts/pi_hardware_bus.py client \
  --remote-host 100.103.76.89 \
  --remote-port 5500 \
  --link-path /dev/ttyFOLLOWER
```

## Expected client log

You should see something like:

```text
Created stable symlink /dev/ttyFOLLOWER -> /dev/pts/3
Connecting to 100.103.76.89:5500 ...
Connected to Pi. Local follower port is /dev/ttyFOLLOWER
```

## Step 4: verify the virtual port exists

In another terminal on the laptop:

```bash
ls -l /dev/ttyFOLLOWER
```

Expected shape:

```bash
/dev/ttyFOLLOWER -> /dev/pts/3
```

## Optional: run as a service

Edit `systemd/pi-hardware-bus-client.service` and set:

- the correct user name
- the correct repo path
- the correct Pi Tailscale IP

Then install it:

```bash
sudo cp systemd/pi-hardware-bus-client.service /etc/systemd/system/pi-hardware-bus-client.service
sudo systemctl daemon-reload
sudo systemctl enable pi-hardware-bus-client.service
sudo systemctl start pi-hardware-bus-client.service
sudo systemctl status pi-hardware-bus-client.service --no-pager
```

## Success condition

Do not continue until:

- client mode is connected to the Pi
- `/dev/ttyFOLLOWER` exists on the laptop
