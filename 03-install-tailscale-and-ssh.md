# 03. Install Tailscale and verify SSH

This step makes the laptop reach the Pi even when both are on different WiFi networks.

## Step 1: install Tailscale on both machines

### Ubuntu laptop

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Raspberry Pi Ubuntu

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Follow the login flow on both machines.

## Step 2: check each machine joined the tailnet

Run on both machines:

```bash
tailscale ip -4
```

Record the **Pi Tailscale IP**. You will use it later as `<PI_TAILSCALE_IP>`.

## Step 3: confirm the Pi has SSH enabled

On the Pi:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh --no-pager
```

## Step 4: SSH from laptop to Pi

From the laptop:

```bash
ssh ubuntu@<PI_TAILSCALE_IP>
```

Example:

```bash
ssh ubuntu@100.103.76.89
```

## Step 5: verify follower port on the Pi over SSH

After SSH succeeds:

```bash
ls -l /dev/follower
```

If this path does not exist, go back to the udev step first.

## Success condition

Do not continue until all of these work:

- `tailscale ip -4` works on both machines
- the laptop can `ssh` into the Pi
- `/dev/follower` exists on the Pi
