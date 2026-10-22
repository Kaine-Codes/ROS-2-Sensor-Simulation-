# sim_sensor

A ROS 2 (Python / `rclpy`) package that simulates an underwater **pressure sensor**. I chose pressure because it is the most common underwater measurement: it is used to estimate depth, and it is the sensor most underwater vehicles carry.

The node publishes `sensor_msgs/FluidPressure`, can be started and stopped through a service, has a rate that can be changed while it runs, and comes with a launch file. No hardware is required.

**Tested on:** Ubuntu 22.04, ROS 2 Iron. The package only uses basic `rclpy` APIs (parameters, services, timers), so it should also build on Humble and Jazzy, but I have only run it on Iron.

## Interfaces

| Type | Name | Message / type | Notes |
|---|---|---|---|
| Publisher | `/sim_sensor/pressure` | `sensor_msgs/FluidPressure` | Absolute pressure in Pa. Depth follows a 60 s sinusoid (0 to `max_depth_m`) in seawater, plus Gaussian noise |
| Service | `/sim_sensor/enable` | `std_srvs/SetBool` | `data: true` starts publishing, `data: false` stops it. Calling it twice with the same value is harmless |
| Parameter | `rate_hz` | double | Default `10.0`. **Valid range 0.1 to 100.0 Hz.** Can be changed at runtime; invalid values are rejected |
| Parameter | `autostart` | bool | Default `true`. Whether publishing begins on launch |
| Parameter | `frame_id` | string | Default `pressure_sensor_link` |
| Parameter | `max_depth_m` | double | Default `20.0`. Peak depth of the simulated dive |
| Parameter | `noise_std_pa` | double | Default `50.0`. Standard deviation of the noise in Pa |

Defaults are set in `config/params.yaml`.

## Design notes

- **Start/stop** cancels the timer instead of dropping messages, so there are no wake-ups while stopped.
- **Rate changes** destroy and recreate the timer at the new period. The running/stopped state is preserved.
- **Validation** lives in a parameter callback that checks type, finiteness and range, and returns a reason string when it rejects a value. The callback is registered *before* the parameters are declared, so a bad value from the launch file or YAML makes the node fail at startup instead of running with a wrong rate.
- **Pressure model:** `P = 101325 + 1025 * 9.80665 * depth` (Pa), using sea-level atmospheric pressure and seawater density.

## Build

Prerequisites: Ubuntu 22.04 with ROS 2 Iron installed and `colcon` available.

```bash
source /opt/ros/iron/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone <this-repo-url>
cd ~/ros2_ws
colcon build --packages-select sim_sensor
source install/setup.bash
```

Every new terminal needs both `source /opt/ros/iron/setup.bash` and `source ~/ros2_ws/install/setup.bash` before any `ros2` command (or add them to `~/.bashrc`).so i put them in a bash file.

## Run

```bash
ros2 launch sim_sensor sensor.launch.py                         # 10 Hz, autostart
ros2 launch sim_sensor sensor.launch.py rate_hz:=20.0 autostart:=false
```

## Demo

The demo video is uploaded in the github repooo, in it i used three terminals, one for seeing the live data coming in, one for giving in commands and one for shows the runtime update from the node

| Terminal | Purpose |
|---|---|
| **1** | Runs the node |
| **2** | Shows the live data, left running the whole time |
| **3** | Sends the commands |

**Terminal 1: the node**
```bash
ros2 launch sim_sensor sensor.launch.py
```

**Terminal 2: live data** (use `ros2 topic echo /sim_sensor/pressure` without `--field` to see the full message)
```bash
ros2 topic echo /sim_sensor/pressure 
```

**Terminal 3: commands**
```bash   
# Measure the publish rate (about 10 Hz)
ros2 topic hz /sim_sensor/pressure  

# Stop: the output in terminal 2 goes silent
ros2 service call /sim_sensor/enable std_srvs/srv/SetBool "{data: false}"
#   success=True, message='stopped'

# Start: the output resumes
ros2 service call /sim_sensor/enable std_srvs/srv/SetBool "{data: true}"

# Valid rate change: terminal 2 scrolls faster
# (use a decimal point; the parameter is a double, so `25` is refused as a type mismatch)
ros2 param set /sim_sensor rate_hz 25.0
#   Set parameter successful

# Invalid rates are rejected and the old rate is kept
ros2 param set /sim_sensor rate_hz -5.0
ros2 param set /sim_sensor rate_hz 0.0
ros2 param set /sim_sensor rate_hz 500.0
#   Setting parameter failed: rate_hz=... outside allowed range [0.1, 100.0]
ros2 param get /sim_sensor rate_hz        # still 25.0
```

**Invalid rate at startup** (stop terminal 1 first, then run):
```bash
ros2 launch sim_sensor sensor.launch.py rate_hz:=-1.0
```
The node refuses to start.

### Demo video

Video (no audio): `final_demo.mp4` 


## Tests

Unit tests cover the rate validation and the pressure calculation:

```bash
cd ~/ros2_ws
colcon test --packages-select sim_sensor
colcon test-result --verbose
```

![Uploading Screenshot from 2026-10-22 14-49-32.png…]()
