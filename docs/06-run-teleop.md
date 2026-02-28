# 06. Run teleop

At this point, all required ports should exist:

- laptop leader: `/dev/leader`
- laptop virtual follower: `/dev/ttyFOLLOWER`
- Pi follower: `/dev/follower`

## Startup order

Use this order every time:

1. Power the arms.
2. Confirm `/dev/leader` exists on the laptop.
3. Confirm `/dev/follower` exists on the Pi.
4. Start `pi_hardware_bus.py server` on the Pi.
5. Start `pi_hardware_bus.py client` on the laptop.
6. Confirm `/dev/ttyFOLLOWER` exists on the laptop.
7. Start `lerobot-teleoperate` on the laptop.

## Final teleop command

Run on the **laptop**:

```bash
lerobot-teleoperate \
  --robot.type so101_follower \
  --robot.port /dev/ttyFOLLOWER \
  --robot.id follower \
  --teleop.type so101_leader \
  --teleop.port /dev/leader \
  --teleop.id leader
```

## What each port means

- `/dev/leader` -> real leader arm on laptop USB
- `/dev/ttyFOLLOWER` -> local virtual port created by Python client
- `/dev/follower` -> real follower arm on Pi USB

## If teleop does not move the follower

Check in this order:

1. Is the Pi server still running?
2. Is the laptop client still connected?
3. Does `/dev/ttyFOLLOWER` still exist?
4. Did the leader and follower names resolve correctly?
5. Is LeRobot using the exact paths shown above?
