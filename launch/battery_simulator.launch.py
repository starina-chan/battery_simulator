from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    namespace = LaunchConfiguration("namespace")

    use_sim_time_arg = DeclareLaunchArgument("use_sim_time", default_value="false")
    namespace_arg = DeclareLaunchArgument("namespace", default_value="")

    params_file = PathJoinSubstitution(
        [FindPackageShare("battery_simulator"), "config", "battery_simulator.yaml"]
    )

    battery_simulator_node = Node(
        package="battery_simulator",
        executable="battery_simulator",
        name="battery_simulator",
        namespace=namespace,
        parameters=[params_file, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            namespace_arg,
            battery_simulator_node,
        ]
    )
