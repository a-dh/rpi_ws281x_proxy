import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from wsled_client import WSLEDClient

class BatteryIndicatorNode(Node):
    def __init__(self):
        super().__init__('battery_indicator_node')
        self.leds = WSLEDClient()

        self.subscription = self.create_subscription(
            BatteryState, 'battery_state', self.battery_callback, 10)

        # Timer for blinking (runs at 2Hz)
        self.blink_timer = self.create_timer(0.5, self.blink_callback)
        self.is_critical = False
        self.blink_state = False

    def battery_callback(self, msg):
        percentage = msg.percentage

        if percentage > 0.70:
            self.is_critical = False
            self.leds.set_intensity_color("green", intensity=0.33)
        elif 0.30 < percentage <= 0.70:
            self.is_critical = False
            self.leds.set_intensity_color("#FFA500", intensity=0.33)
        elif 0.15 < percentage <= 0.30:
            self.is_critical = False
            self.leds.set_intensity_color("red", intensity=0.66)
        else:
            # Drop into critical mode for the timer to handle
            self.is_critical = True

    def blink_callback(self):
        if not self.is_critical:
            return

        if self.blink_state:
            self.leds.set_intensity_color("red", intensity=1.0)
        else:
            self.leds.off()
        self.blink_state = not self.blink_state

    def on_shutdown(self):
        self.leds.off()

def main(args=None):
    rclpy.init(args=args)
    node = BatteryIndicatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.on_shutdown()
    finally:
        node.destroy_node()
        rclpy.shutdown()
