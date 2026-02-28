# 02. Rename USB ports with udev

This step is important because `/dev/ttyACM0` and `/dev/ttyUSB0` can change after reboot or reconnect.

We will create stable names:

- on the **laptop**: `/dev/leader`
- on the **Pi**: `/dev/follower`

## Step 1: plug in the arm

On the machine where the arm is connected, run:

```bash
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

Typical result:

```bash
/dev/ttyACM0
```

## Step 2: inspect the device

Replace the path below with your actual raw port:

```bash
udevadm info -a -n /dev/ttyACM0
```

Look for values such as:

- `ATTRS{idVendor}`
- `ATTRS{idProduct}`
- `ATTRS{serial}`

You will use those in a udev rule.

## Step 3: create the rule

Open the rules file:

```bash
sudo nano /etc/udev/rules.d/99-so101-ports.rules
```

### Laptop rule example

Use this on the **laptop** for the leader arm:

```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", ATTRS{serial}=="LEADER_SERIAL", SYMLINK+="leader", MODE:="0666"
```

### Pi rule example

Use this on the **Pi** for the follower arm:

```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", ATTRS{serial}=="FOLLOWER_SERIAL", SYMLINK+="follower", MODE:="0666"
```

If `serial` does not exist or is not unique, you can match using a different unique attribute from `udevadm info`.

A template is also provided here:

- `udev/99-so101-ports.rules.example`

## Step 4: reload udev

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Then unplug and reconnect the USB cable.

## Step 5: verify

### On the laptop

```bash
ls -l /dev/leader
```

### On the Pi

```bash
ls -l /dev/follower
```

Expected shape:

```bash
/dev/leader -> ttyACM0
/dev/follower -> ttyACM0
```

## Success condition

Do not continue until:

- the laptop has `/dev/leader`
- the Pi has `/dev/follower`

Everything later in the repo assumes those names exist.
