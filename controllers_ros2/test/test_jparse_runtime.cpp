#include <algorithm>
#include <chrono>
#include <cmath>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include <geometry_msgs/msg/twist_stamped.hpp>
#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <std_msgs/msg/string.hpp>

#define JPARSE_VELOCITY_CONTROLLER_NO_MAIN
#include "../src/jparse_velocity_controller.cpp"

using namespace std::chrono_literals;

namespace
{
const std::vector<std::string> kJointNames = {
  "joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6"};

std::string testUrdf()
{
  const std::vector<std::string> axes = {
    "0 0 1", "0 1 0", "1 0 0", "0 1 0", "1 0 0", "0 0 1"};
  std::string urdf = "<robot name=\"jparse_test\"><link name=\"base\"/>";
  std::string parent = "base";
  for (std::size_t index = 0; index < axes.size(); ++index) {
    const std::string child = "link_" + std::to_string(index + 1);
    urdf +=
      "<link name=\"" + child + "\"/>"
      "<joint name=\"" + kJointNames[index] + "\" type=\"revolute\">"
      "<parent link=\"" + parent + "\"/><child link=\"" + child + "\"/>"
      "<origin xyz=\"0.1 0 0.1\" rpy=\"0 0 0\"/>"
      "<axis xyz=\"" + axes[index] + "\"/>"
      "<limit lower=\"-3.14\" upper=\"3.14\" effort=\"100\" velocity=\"2.0\"/>"
      "</joint>";
    parent = child;
  }
  return urdf + "</robot>";
}

void spinFor(
  rclcpp::executors::SingleThreadedExecutor & executor,
  std::chrono::milliseconds duration)
{
  const auto deadline = std::chrono::steady_clock::now() + duration;
  while (std::chrono::steady_clock::now() < deadline) {
    executor.spin_some();
    std::this_thread::sleep_for(2ms);
  }
}
}  // namespace

class JParseRuntimeTest : public ::testing::Test
{
protected:
  static void SetUpTestSuite()
  {
    rclcpp::init(0, nullptr);
  }

  static void TearDownTestSuite()
  {
    rclcpp::shutdown();
  }
};

TEST_F(JParseRuntimeTest, ReportsReadinessLimitsVelocityAndZerosOnTimeout)
{
  const auto options = rclcpp::NodeOptions().parameter_overrides({
    rclcpp::Parameter("base_link", "base"),
    rclcpp::Parameter("tip_link", "link_6"),
    rclcpp::Parameter("robot_description_topic", "/test_robot_description"),
    rclcpp::Parameter("joint_states_topic", "/test_joint_states"),
    rclcpp::Parameter("twist_topic", "/test_twist"),
    rclcpp::Parameter("command_topic", "/test_commands"),
    rclcpp::Parameter("readiness_topic", "/test_ready"),
    rclcpp::Parameter("rate_hz", 100.0),
    rclcpp::Parameter("command_timeout", 0.1),
    rclcpp::Parameter("joint_state_timeout", 0.5),
    rclcpp::Parameter("max_joint_velocity", 0.2),
    rclcpp::Parameter(
      "command_joint_names_csv",
      "joint_1,joint_2,joint_3,joint_4,joint_5,joint_6"),
  });
  auto controller = std::make_shared<JParseVelocityController>(options);
  auto harness = std::make_shared<rclcpp::Node>("jparse_runtime_test");
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(controller);
  executor.add_node(harness);

  auto description_pub = harness->create_publisher<std_msgs::msg::String>(
    "/test_robot_description", rclcpp::QoS(1).transient_local().reliable());
  auto joint_pub = harness->create_publisher<sensor_msgs::msg::JointState>(
    "/test_joint_states", rclcpp::SensorDataQoS());
  auto twist_pub = harness->create_publisher<geometry_msgs::msg::TwistStamped>(
    "/test_twist", rclcpp::SystemDefaultsQoS());

  std::vector<bool> readiness;
  std::vector<std::vector<double>> commands;
  auto ready_sub = harness->create_subscription<std_msgs::msg::Bool>(
    "/test_ready", rclcpp::QoS(1).transient_local().reliable(),
    [&readiness](const std_msgs::msg::Bool & msg) {readiness.push_back(msg.data);});
  auto command_sub = harness->create_subscription<std_msgs::msg::Float64MultiArray>(
    "/test_commands", rclcpp::SystemDefaultsQoS(),
    [&commands](const std_msgs::msg::Float64MultiArray & msg) {
      commands.push_back(msg.data);
    });

  std_msgs::msg::String description;
  description.data = testUrdf();
  description_pub->publish(description);
  sensor_msgs::msg::JointState joints;
  joints.name = kJointNames;
  joints.position.assign(kJointNames.size(), 0.1);

  const auto ready_deadline = std::chrono::steady_clock::now() + 2s;
  while (
    std::chrono::steady_clock::now() < ready_deadline &&
    std::find(readiness.begin(), readiness.end(), true) == readiness.end())
  {
    joints.header.stamp = harness->now();
    joint_pub->publish(joints);
    spinFor(executor, 10ms);
  }
  ASSERT_NE(std::find(readiness.begin(), readiness.end(), true), readiness.end());
  spinFor(executor, 100ms);
  ASSERT_GE(
    std::count(commands.begin(), commands.end(), std::vector<double>(6, 0.0)),
    2);

  commands.clear();
  geometry_msgs::msg::TwistStamped twist;
  twist.header.frame_id = "base";
  twist.twist.angular.z = 10.0;
  const auto command_deadline = std::chrono::steady_clock::now() + 300ms;
  while (std::chrono::steady_clock::now() < command_deadline) {
    joints.header.stamp = harness->now();
    joint_pub->publish(joints);
    twist.header.stamp = harness->now();
    twist_pub->publish(twist);
    spinFor(executor, 10ms);
  }

  bool saw_nonzero = false;
  for (const auto & command : commands) {
    ASSERT_EQ(command.size(), 6U);
    for (const double value : command) {
      EXPECT_LE(std::abs(value), 0.200001);
      saw_nonzero = saw_nonzero || std::abs(value) > 1.0e-6;
    }
  }
  EXPECT_TRUE(saw_nonzero);

  commands.clear();
  const auto timeout_deadline = std::chrono::steady_clock::now() + 350ms;
  while (std::chrono::steady_clock::now() < timeout_deadline) {
    joints.header.stamp = harness->now();
    joint_pub->publish(joints);
    spinFor(executor, 10ms);
  }
  EXPECT_GE(
    std::count(commands.begin(), commands.end(), std::vector<double>(6, 0.0)),
    2);
}
