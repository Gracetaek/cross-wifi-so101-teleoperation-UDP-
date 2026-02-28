# 04. Pi server setup

This step runs the **server mode** of `pi_hardware_bus.py` on the Raspberry Pi.

The server opens the real follower serial port and publishes it over TCP.

## Step 1: copy the script to the Pi

From the laptop:

```bash
scp scripts/pi_hardware_bus.py ubuntu@<PI_TAILSCALE_IP>:~/pi_hardware_bus.py
```

Or copy the whole repo to the Pi if you prefer.

## Step 2: install Python dependency on the Pi

SSH into the Pi and run:

```bash
python3 -m pip install --user pyserial
```

If `pip` is missing:

```bash
sudo apt update
sudo apt install -y python3-pip
python3 -m pip install --user pyserial
```

## Step 3: run server mode manually

On the Pi:

```bash
sudo python3 ~/pi_hardware_bus.py server \
  --serial-port /dev/follower \
  --baud 1000000 \
  --listen-host 0.0.0.0 \
  --listen-port 5500
```

## Expected server log

You should see something like:

```text
Opened /dev/follower at 1000000 baud
Listening on 0.0.0.0:5500
```

Leave this running for now.

## Optional: run as a service

Copy the service file:

```bash
scp systemd/pi-hardware-bus-server.service ubuntu@<PI_TAILSCALE_IP>:~/pi-hardware-bus-server.service
```

Then on the Pi:

```bash
sudo cp ~/pi-hardware-bus-server.service /etc/systemd/system/pi-hardware-bus-server.service
sudo systemctl daemon-reload
sudo systemctl enable pi-hardware-bus-server.service
sudo systemctl start pi-hardware-bus-server.service
sudo systemctl status pi-hardware-bus-server.service --no-pager
```

## Success condition

Do not continue until the Pi is listening successfully and `/dev/follower` opens without error.
