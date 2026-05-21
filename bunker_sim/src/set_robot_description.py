import rclpy
from rclpy.node import Node
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue

def main():
    rclpy.init()
    node = rclpy.create_node('param_setter')

    client = node.create_client(SetParameters, '/controller_manager/set_parameters')
    while not client.wait_for_service(timeout_sec=1.0):
        node.get_logger().info('Service not available, waiting...')

    # Read URDF content
    with open('/home/guenther/ws_restore/src/bunker.urdf', 'r') as f:
        urdf_content = f.read()

    request = SetParameters.Request()
    param = Parameter()
    param.name = 'robot_description'
    param.value = ParameterValue(string_value=urdf_content, type=ParameterType.PARAMETER_STRING)
    request.parameters = [param]

    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future)

    response = future.result()
    for result in response.results:
        if result.successful:
            node.get_logger().info('Successfully set robot_description')
        else:
            node.get_logger().error(f'Failed to set robot_description: {result.reason}')

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
