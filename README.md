# battery_simulator

Simulates a battery pack discharging over time and publishes
`sensor_msgs/BatteryState` on `battery_state`. Charge drains continuously at
an idle rate, plus an extra load-dependent rate scaled by the most recent
`/cmd_vel` (so driving or spinning the robot drains it faster than sitting
still). Voltage is derived from charge via a real single-cell open-circuit-
voltage curve (a flat plateau through most of the discharge, sagging hard
near empty), not a straight-line approximation. The battery only discharges -
there's no charging/docking simulation.

## Cell chemistry curves

`battery_chemistry` selects which open-circuit-voltage-vs-state-of-charge
curve is used, each a 21-point table (5% steps) rather than a handful of
rough points:

- `li_ion` (default) - generic cylindrical Li-ion (e.g. 18650 NMC/NCA), as
  commonly used in robotics/laptops/power tools. Discharges down to a 2.5V
  cutoff.
- `lipo` - generic RC/drone pouch LiPo. Same 4.20V full charge and the same
  ~3.7V mid-discharge plateau (LiPo is the same lithium chemistry in
  different packaging, not a different curve shape), but conventionally
  protected at a much higher ~3.3V cutoff to avoid pouch-cell damage, so it
  reads empty sooner than a Li-ion cell would at the same charge level.

Sourced from 18650 vendor/teardown voltage guides (tycorun, ersaelectronics,
lygte-info.dk) for the Li-ion curve and cutoff, and a widely used generic
LiPo fuel-gauge profile (`mawildoer/battery` on GitHub) for the LiPo curve.

## Usage

```sh
ros2 launch battery_simulator battery_simulator.launch.py
```

## Parameters (`config/battery_simulator.yaml`)

| Param | Default | Meaning |
|---|---|---|
| `update_rate_hz` | `2.0` | How often the simulated charge is recomputed and published |
| `battery_chemistry` | `"li_ion"` | `li_ion` or `lipo` - selects the voltage curve, see below |
| `design_capacity_ah` | `2.0` | Full-charge capacity (Ah) |
| `cell_count` | `3` | Series cell count (3S pack) |
| `idle_current_a` | `9.0` | Constant drain (A) with no recent `/cmd_vel` motion |
| `load_current_per_linear_mps` | `6.0` | Extra drain (A) per m/s of `\|linear.x\|` on `/cmd_vel` |
| `load_current_per_angular_radps` | `2.0` | Extra drain (A) per rad/s of `\|angular.z\|` on `/cmd_vel` |
| `cmd_vel_timeout_s` | `1.0` | If no `/cmd_vel` arrives within this window, load current drops to zero |
| `battery_frame_id` | `"base_link"` | `header.frame_id` on published messages |

The shipped defaults are tuned for a fast, testable drain pace (~13 min idle
life), not a realistic runtime - raise `design_capacity_ah` and lower the
current params for a realistic pace.

## Dependencies

`rclpy`, `sensor_msgs`, `geometry_msgs`
