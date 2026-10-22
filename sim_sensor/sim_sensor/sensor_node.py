"""Simulated underwater pressure sensor.

Publishes sensor_msgs/FluidPressure on ~/pressure at a configurable rate.
Depth follows a slow sinusoid (a vehicle doing a yo-yo dive) plus Gaussian noise.
Publishing is gated by the ~/enable std_srvs/SetBool service.
"""
import math
import random

import rclpy
from rcl_interfaces.msg import (FloatingPointRange, ParameterDescriptor,
                                SetParametersResult)
from rclpy.node import Node
from sensor_msgs.msg import FluidPressure
from std_srvs.srv import SetBool

MIN_RATE_HZ = 0.1
MAX_RATE_HZ = 100.0

P_ATM = 101325.0   # Pa
RHO_SEA = 1025.0   # kg/m^3
G = 9.80665        # m/s^2


def depth_to_pressure(depth_m: float) -> float:
    """Absolute pressure (Pa) at a given depth in seawater."""
    return P_ATM + RHO_SEA * G * depth_m


def validate_rate(value) -> str:
    """Return '' if value is a valid rate, otherwise a human-readable reason."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f'rate_hz must be a number, got {type(value).__name__}'
    if not math.isfinite(value):
        return 'rate_hz must be finite'
    if not (MIN_RATE_HZ <= value <= MAX_RATE_HZ):
        return f'rate_hz={value} outside allowed range [{MIN_RATE_HZ}, {MAX_RATE_HZ}]'
    return ''


class SimSensor(Node):
    def __init__(self):
        super().__init__('sim_sensor')

        # Register the validator BEFORE declaring, so launch/YAML values are checked too.
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.declare_parameter(
            'rate_hz', 10.0,
            ParameterDescriptor(
                description='Publish rate in Hz.',
                floating_point_range=[FloatingPointRange(
                    from_value=MIN_RATE_HZ, to_value=MAX_RATE_HZ, step=0.0)]))
        self.declare_parameter('frame_id', 'pressure_sensor_link')
        self.declare_parameter('max_depth_m', 20.0)
        self.declare_parameter('noise_std_pa', 50.0)
        self.declare_parameter('autostart', True)

        self._rate_hz = float(self.get_parameter('rate_hz').value)
        self._running = bool(self.get_parameter('autostart').value)
        self._t0 = self.get_clock().now()

        self._pub = self.create_publisher(FluidPressure, '~/pressure', 10)
        self._srv = self.create_service(SetBool, '~/enable', self._on_enable)
        self._timer = self.create_timer(1.0 / self._rate_hz, self._tick)
        if not self._running:
            self._timer.cancel()

        self.get_logger().info(
            f'sim_sensor ready: rate={self._rate_hz} Hz, '
            f'{"RUNNING" if self._running else "STOPPED"} '
            f'(call ~/enable to start/stop)')

    # --- service ---------------------------------------------------------
    def _on_enable(self, request, response):
        want = request.data
        if want == self._running:
            response.success = True
            response.message = f'already {"running" if want else "stopped"}'
            return response
        self._running = want
        if want:
            self._timer.reset()
        else:
            self._timer.cancel()
        self.get_logger().info('publishing STARTED' if want else 'publishing STOPPED')
        response.success = True
        response.message = 'started' if want else 'stopped'
        return response

    # --- parameters ------------------------------------------------------
    def _on_set_parameters(self, params):
        new_rate = None
        for p in params:
            if p.name == 'rate_hz':
                reason = validate_rate(p.value)
                if reason:
                    self.get_logger().warn(f'Rejected parameter change: {reason}')
                    return SetParametersResult(successful=False, reason=reason)
                new_rate = float(p.value)
        if new_rate is not None and hasattr(self, '_timer') and new_rate != self._rate_hz:
            self._rate_hz = new_rate
            self.destroy_timer(self._timer)
            self._timer = self.create_timer(1.0 / new_rate, self._tick)
            if not self._running:
                self._timer.cancel()
            self.get_logger().info(f'rate changed to {new_rate} Hz')
        return SetParametersResult(successful=True)

    # --- publishing ------------------------------------------------------
    def _tick(self):
        now = self.get_clock().now()
        t = (now - self._t0).nanoseconds * 1e-9
        max_depth = float(self.get_parameter('max_depth_m').value)
        noise = float(self.get_parameter('noise_std_pa').value)

        depth = 0.5 * max_depth * (1.0 - math.cos(2.0 * math.pi * t / 60.0))
        msg = FluidPressure()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = str(self.get_parameter('frame_id').value)
        msg.fluid_pressure = depth_to_pressure(depth) + random.gauss(0.0, noise)
        msg.variance = noise ** 2
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SimSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
