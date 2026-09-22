import os
from glob import glob

from setuptools import find_packages, setup

package_name = "battery_simulator"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(include=[package_name, package_name + ".*"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="starina-chan",
    maintainer_email="154484150+starina-chan@users.noreply.github.com",
    description="Simulates a Li-ion battery discharging over time, draining faster under cmd_vel load, publishing sensor_msgs/BatteryState",
    license="MIT",
    entry_points={
        "console_scripts": [
            "battery_simulator = battery_simulator.battery_simulator_node:main",
        ],
    },
)
