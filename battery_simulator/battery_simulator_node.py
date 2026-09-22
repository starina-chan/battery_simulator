from itertools import pairwise

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import BatteryState

_CELL_VOLTAGE_BY_STATE_OF_CHARGE = (
    (0.00, 3.00),
    (0.10, 3.40),
    (0.20, 3.55),
    (0.40, 3.70),
    (0.70, 3.85),
    (0.90, 4.00),
    (1.00, 4.20),
)


def _interpolate_cell_voltage(state_of_charge):
    soc = min(max(state_of_charge, 0.0), 1.0)
    for (lower_soc, lower_v), (upper_soc, upper_v) in pairwise(
        _CELL_VOLTAGE_BY_STATE_OF_CHARGE
    ):
        if soc <= upper_soc:
            fraction = (soc - lower_soc) / (upper_soc - lower_soc)
            return lower_v + fraction * (upper_v - lower_v)
    return _CELL_VOLTAGE_BY_STATE_OF_CHARGE[-1][1]


class BatterySimulatorNode(Node):
    def __init__(self):
        super().__init__("battery_simulator")

        self.declare_parameter("update_rate_hz", 2.0)
        self.declare_parameter("design_capacity_ah", 2.0)
        self.declare_parameter("cell_count", 3)
        self.declare_parameter("idle_current_a", 9.0)
        self.declare_parameter("load_current_per_linear_mps", 6.0)
        self.declare_parameter("load_current_per_angular_radps", 2.0)
        self.declare_parameter("cmd_vel_timeout_s", 1.0)
        self.declare_parameter("battery_frame_id", "base_link")

        self.update_rate_hz = self.get_parameter("update_rate_hz").value
        self.design_capacity_ah = self.get_parameter("design_capacity_ah").value
        self.cell_count = self.get_parameter("cell_count").value
        self.idle_current_a = self.get_parameter("idle_current_a").value
        self.load_current_per_linear_mps = self.get_parameter(
            "load_current_per_linear_mps"
        ).value
        self.load_current_per_angular_radps = self.get_parameter(
            "load_current_per_angular_radps"
        ).value
        self.cmd_vel_timeout_s = self.get_parameter("cmd_vel_timeout_s").value
        self.battery_frame_id = self.get_parameter("battery_frame_id").value

        self.charge_ah = self.design_capacity_ah
        self.last_linear_x = 0.0
        self.last_angular_z = 0.0
        self.last_cmd_vel_time = None

        self.battery_pub = self.create_publisher(BatteryState, "battery_state", 10)
        self.cmd_vel_sub = self.create_subscription(
            Twist, "cmd_vel", self.cmd_vel_callback, 10
        )
        self.timer = self.create_timer(1.0 / self.update_rate_hz, self.tick)

    def cmd_vel_callback(self, msg):
        self.last_linear_x = msg.linear.x
        self.last_angular_z = msg.angular.z
        self.last_cmd_vel_time = self.get_clock().now()

    def load_current_a(self):
        if self.last_cmd_vel_time is None:
            return 0.0
        elapsed_s = (self.get_clock().now() - self.last_cmd_vel_time).nanoseconds / 1e9
        if elapsed_s > self.cmd_vel_timeout_s:
            return 0.0
        return (
            abs(self.last_linear_x) * self.load_current_per_linear_mps
            + abs(self.last_angular_z) * self.load_current_per_angular_radps
        )

    def tick(self):
        dt_s = 1.0 / self.update_rate_hz
        total_current_a = self.idle_current_a + self.load_current_a()

        self.charge_ah -= total_current_a * dt_s / 3600.0
        self.charge_ah = min(max(self.charge_ah, 0.0), self.design_capacity_ah)
        percentage = self.charge_ah / self.design_capacity_ah
        is_empty = self.charge_ah <= 0.0
        cell_voltage = _interpolate_cell_voltage(percentage)

        battery_msg = BatteryState()
        battery_msg.header.stamp = self.get_clock().now().to_msg()
        battery_msg.header.frame_id = self.battery_frame_id
        battery_msg.voltage = cell_voltage * self.cell_count
        battery_msg.current = -total_current_a
        battery_msg.charge = self.charge_ah
        battery_msg.capacity = self.design_capacity_ah
        battery_msg.design_capacity = self.design_capacity_ah
        battery_msg.percentage = percentage
        battery_msg.cell_voltage = [cell_voltage] * self.cell_count
        battery_msg.power_supply_status = (
            BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
            if is_empty
            else BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        )
        battery_msg.power_supply_health = (
            BatteryState.POWER_SUPPLY_HEALTH_DEAD
            if is_empty
            else BatteryState.POWER_SUPPLY_HEALTH_GOOD
        )
        battery_msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        battery_msg.present = True

        self.battery_pub.publish(battery_msg)


def main(args=None):
    rclpy.init(args=args)
    node = BatterySimulatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
