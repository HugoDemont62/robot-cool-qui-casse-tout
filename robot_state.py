import time
import threading
import math
import random
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, List
from enum import Enum


class WheelState(Enum):
    STOPPED = "stopped"
    FORWARD = "forward"
    BACKWARD = "backward"


class RobotMode(Enum):
    IDLE = "idle"
    AUTONOMOUS = "autonomous"
    MANUAL = "manual"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


@dataclass
class Wheel:
    name: str
    state: str = WheelState.STOPPED.value
    speed: float = 0.0
    target_speed: float = 0.0
    encoder_ticks: int = 0


@dataclass
class Sensor:
    name: str
    value: float = 0.0
    unit: str = ""
    is_active: bool = True


@dataclass
class Actuator:
    name: str
    position: float = 0.0
    is_enabled: bool = False


@dataclass
class RobotState:
    robot_name: str = "Robot cool qui casse tout"
    team_name: str = "Pas encore ingénieur"
    mode: str = RobotMode.IDLE.value
    is_connected: bool = False
    battery_level: float = 100.0
    match_time_remaining: int = 100
    score: int = 0

    position: Position = field(default_factory=Position)
    target_position: Position = field(default_factory=Position)
    direction: float = 0.0
    angular_velocity: float = 0.0
    linear_velocity: float = 0.0

    wheels: List[Wheel] = field(default_factory=lambda: [
        Wheel(name="front_left"),
        Wheel(name="front_right"),
        Wheel(name="rear_left"),
        Wheel(name="rear_right"),
    ])

    sensors: List[Sensor] = field(default_factory=lambda: [
        Sensor(name="lidar_front", unit="mm"),
        Sensor(name="lidar_rear", unit="mm"),
        Sensor(name="ultrasonic_left", unit="mm"),
        Sensor(name="ultrasonic_right", unit="mm"),
        Sensor(name="line_sensor_1", unit=""),
        Sensor(name="line_sensor_2", unit=""),
        Sensor(name="line_sensor_3", unit=""),
    ])

    actuators: List[Actuator] = field(default_factory=lambda: [
        Actuator(name="gripper"),
        Actuator(name="arm_elevation"),
        Actuator(name="arm_rotation"),
        Actuator(name="flag_deployer"),
    ])

    obstacle_detected: bool = False
    emergency_stop_active: bool = False
    calibration_done: bool = False
    aruco_detected: bool = False
    detected_aruco_ids: List[int] = field(default_factory=list)

    last_update: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            'robot_name': self.robot_name,
            'team_name': self.team_name,
            'mode': self.mode,
            'is_connected': self.is_connected,
            'battery_level': self.battery_level,
            'match_time_remaining': self.match_time_remaining,
            'score': self.score,
            'position': asdict(self.position),
            'target_position': asdict(self.target_position),
            'direction': self.direction,
            'angular_velocity': self.angular_velocity,
            'linear_velocity': self.linear_velocity,
            'wheels': [asdict(w) for w in self.wheels],
            'sensors': [asdict(s) for s in self.sensors],
            'actuators': [asdict(a) for a in self.actuators],
            'obstacle_detected': self.obstacle_detected,
            'emergency_stop_active': self.emergency_stop_active,
            'calibration_done': self.calibration_done,
            'aruco_detected': self.aruco_detected,
            'detected_aruco_ids': self.detected_aruco_ids,
            'last_update': self.last_update,
        }


class RobotStateManager:
    def __init__(self):
        self._state = RobotState()
        self._lock = threading.Lock()
        self._listeners: List[Callable[[RobotState], None]] = []
        self._running = False
        self._simulation_thread: Optional[threading.Thread] = None

    @property
    def state(self) -> RobotState:
        with self._lock:
            return self._state

    def get_state(self) -> RobotState:
        with self._lock:
            return self._state

    def add_listener(self, callback: Callable[[RobotState], None]):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[RobotState], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        for listener in self._listeners:
            try:
                listener(self._state)
            except Exception as e:
                print(f"[ERREUR] Erreur lors de la notification du listener: {e}")

    def update_position(self, x: float, y: float, theta: float):
        with self._lock:
            self._state.position.x = x
            self._state.position.y = y
            self._state.position.theta = theta
            self._state.direction = theta
            self._state.last_update = time.time()
        self._notify_listeners()

    def update_wheel(self, wheel_index: int, state: str = None, speed: float = None):
        with self._lock:
            if 0 <= wheel_index < len(self._state.wheels):
                if state is not None:
                    self._state.wheels[wheel_index].state = state
                if speed is not None:
                    self._state.wheels[wheel_index].speed = speed
                self._state.last_update = time.time()
        self._notify_listeners()

    def update_sensor(self, sensor_index: int, value: float):
        with self._lock:
            if 0 <= sensor_index < len(self._state.sensors):
                self._state.sensors[sensor_index].value = value
                self._state.last_update = time.time()
        self._notify_listeners()

    def update_actuator(self, actuator_index: int, position: float = None, 
                        is_enabled: bool = None):
        with self._lock:
            if 0 <= actuator_index < len(self._state.actuators):
                if position is not None:
                    self._state.actuators[actuator_index].position = position
                if is_enabled is not None:
                    self._state.actuators[actuator_index].is_enabled = is_enabled
                self._state.last_update = time.time()
        self._notify_listeners()

    def set_mode(self, mode: str):
        with self._lock:
            self._state.mode = mode
            self._state.last_update = time.time()
        self._notify_listeners()

    def set_connected(self, connected: bool):
        with self._lock:
            self._state.is_connected = connected
            self._state.last_update = time.time()
        self._notify_listeners()

    def set_battery_level(self, level: float):
        with self._lock:
            self._state.battery_level = max(0.0, min(100.0, level))
            self._state.last_update = time.time()
        self._notify_listeners()

    def set_emergency_stop(self, active: bool):
        with self._lock:
            self._state.emergency_stop_active = active
            if active:
                self._state.mode = RobotMode.EMERGENCY_STOP.value
                for wheel in self._state.wheels:
                    wheel.state = WheelState.STOPPED.value
                    wheel.speed = 0.0
            self._state.last_update = time.time()
        self._notify_listeners()

    def update_aruco_detection(self, detected: bool, ids: List[int] = None):
        with self._lock:
            self._state.aruco_detected = detected
            self._state.detected_aruco_ids = ids if ids else []
            self._state.last_update = time.time()
        self._notify_listeners()

    def update_match_time(self, time_remaining: int):
        with self._lock:
            self._state.match_time_remaining = max(0, time_remaining)
            self._state.last_update = time.time()
        self._notify_listeners()

    def update_score(self, score: int):
        with self._lock:
            self._state.score = score
            self._state.last_update = time.time()
        self._notify_listeners()

    def start_simulation(self):
        self._running = True
        def simulation_loop():
            t = 0
            while self._running:
                with self._lock:
                    self._state.position.x = 1500 + 500 * math.sin(t * 0.1)
                    self._state.position.y = 1000 + 400 * math.cos(t * 0.1)
                    self._state.position.theta = (t * 10) % 360
                    self._state.direction = self._state.position.theta
                    self._state.linear_velocity = 100 + random.uniform(-10, 10)
                    self._state.angular_velocity = 5 + random.uniform(-2, 2)
                    for wheel in self._state.wheels:
                        wheel.state = WheelState.FORWARD.value
                        wheel.speed = 60 + random.uniform(-5, 5)
                        wheel.encoder_ticks += int(wheel.speed)
                    for sensor in self._state.sensors:
                        if "lidar" in sensor.name or "ultrasonic" in sensor.name:
                            sensor.value = 200 + random.uniform(-50, 50)
                        else:
                            sensor.value = random.choice([0, 1])
                    if self._state.battery_level <= 20:
                        self._state.battery_level = 100.0
                    else:
                        self._state.battery_level -= 0.05
                    self._state.aruco_detected = random.random() > 0.3
                    if self._state.aruco_detected:
                        self._state.detected_aruco_ids = [23]
                    else:
                        self._state.detected_aruco_ids = []
                    self._state.is_connected = True
                    self._state.mode = RobotMode.AUTONOMOUS.value
                    self._state.last_update = time.time()
                self._notify_listeners()
                t += 1
                time.sleep(0.1)
        self._simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        self._simulation_thread.start()
        print("[INFO] Mode simulation démarré")

    def stop_simulation(self):
        self._running = False
        if self._simulation_thread:
            self._simulation_thread.join(timeout=1.0)
            self._simulation_thread = None
        print("[INFO] Mode simulation arrêté")
