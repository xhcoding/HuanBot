from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable, AppendEnvironmentVariable
from launch.substitutions import Command, FindExecutable
from launch.actions import IncludeLaunchDescription
from launch.substitutions.text_substitution import TextSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import (
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit


def generate_launch_description():
    pkg_path = FindPackageShare("robot_describes")
    urdf_file = PathJoinSubstitution([pkg_path, "urdf", "ackermann_car.urdf.xacro"])
    rviz_file = PathJoinSubstitution([pkg_path, "rviz", "display_robot.rviz"])
    PathJoinSubstitution([pkg_path, "world", "empty.world"])

    gz_launch_path = PathJoinSubstitution(
        [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
    )

    robot_description_content = Command([FindExecutable(name="xacro"), " ", urdf_file])

    robot_description = {"robot_description": robot_description_content}

    # 发布机器人状态
    robot_state_pub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
    )

    # 控制器配置路径
    gz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch_path),
        launch_arguments={
            "gz_args": [TextSubstitution(text="-r -v 1 empty.sdf")],
            "on_exit_shutdown": "True",
        }.items(),
    )

    # RViz可视化
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_file],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "xbot",
            "-topic",
            "robot_description",
        ],
    )

    controller_path = PathJoinSubstitution(
        [pkg_path, "config", "ackermann_drive_controller.yaml"]
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    ackermann_steering_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "ackermann_steering_controller",
            "--param-file",
            controller_path,
            "--controller-ros-args",
            "-r /ackermann_steering_controller/tf_odometry:=/tf",
            "--controller-ros-args",
            "-r /ackermann_steering_controller/reference:=/cmd_vel",
        ],
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable("QT_ENABLE_HIGHDPI_SCALING", "0"),
            AppendEnvironmentVariable(
                "GZ_SIM_RESOURCE_PATH", PathJoinSubstitution([pkg_path, ".."])
            ),
            robot_state_pub,
            bridge,
            gz_launch,
            RegisterEventHandler(
                OnProcessExit(
                    target_action=gz_spawn_entity,
                    on_exit=[joint_state_broadcaster_spawner],
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action=joint_state_broadcaster_spawner,
                    on_exit=[ackermann_steering_controller_spawner],
                )
            ),
            gz_spawn_entity,
            rviz_node,
        ]
    )
