import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from wsled_client import WSLEDClient

class MyRobotNode(Node):
    def __init__(self):
        super().__init__('led_node')
        self.leds = WSLEDClient()
        self.count = self.leds.get_count()
        self.get_logger().info(f"LED proxy reports {self.count} pixels")
        self.subscription = self.create_subscription(Bool, 'error', self.status_callback, 10)

    def status_callback(self, msg):
        if msg.data:
            self.leds.set_intensity_color("red")
        else:
            self.leds.set_intensity_color("green", intensity=0.2, index=0)

def main(args=None):
    rclpy.init(args=args)
    node = MyRobotNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.leds.off()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
