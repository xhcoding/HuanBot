import os

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command, FindExecutable


def generate_launch_description():
    pkg_path = get_package_share_directory("robot_describes")
    urdf_file = os.path.join(pkg_path, "urdf", "ackermann_car.urdf.xacro")
    rviz_file = os.path.join(pkg_path, "rviz", "display_robot.rviz")

    robot_description_content = Command([FindExecutable(name="xacro"), " ", urdf_file])

    robot_description = {"robot_description": robot_description_content}

    # 发布机器人状态
    robot_state_pub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
    )

    robot_joint_pub = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
    )

    # RViz可视化
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_file],
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable("QT_SCREEN_SCALE_FACTORS", "0"),
            robot_state_pub,
            robot_joint_pub,
            rviz_node,
        ]
    )
