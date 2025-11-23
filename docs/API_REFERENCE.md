# BlueBuzzah v2 API Reference

**Comprehensive API documentation for BlueBuzzah v2 bilateral haptic therapy system**

Version: 2.0.0
Last Updated: 2025-01-11

---

## Table of Contents

- [Overview](#overview)
- [Core Types and Constants](#core-types-and-constants)
- [Configuration System](#configuration-system)
- [Event System](#event-system)
- [State Machine](#state-machine)
- [Hardware Abstraction](#hardware-abstraction)
- [BLE Communication](#ble-communication)
- [Therapy Engine](#therapy-engine)
- [Synchronization Protocol](#synchronization-protocol)
- [Application Layer](#application-layer)
- [LED UI](#led-ui)
- [Usage Examples](#usage-examples)

---

## Overview

BlueBuzzah v2 provides a clean, layered API for bilateral haptic therapy control. The architecture follows Clean Architecture principles with clear separation between layers:

- **Core**: Types, constants, and fundamental definitions
- **Configuration**: System and therapy configuration management
- **Events**: Event-driven communication between components
- **State**: Explicit state machine for therapy sessions
- **Hardware**: Hardware abstraction for haptic controllers, battery, etc.
- **Communication**: BLE protocol and message handling
- **Therapy**: Pattern generation and therapy execution
- **Application**: High-level use cases and workflows

---

## Core Types and Constants

### Module: `core.types`

#### DeviceRole

Device role in the bilateral therapy system.

```python
from core.types import DeviceRole

class DeviceRole(Enum):
    PRIMARY = "Primary"     # Initiates therapy, controls timing
    SECONDARY = "Secondary" # Follows PRIMARY commands
```

**Methods:**

```python
def is_primary() -> bool
```
Check if this is the PRIMARY role.

```python
def is_secondary() -> bool
```
Check if this is the SECONDARY role.

**Usage:**
```python
role = DeviceRole.PRIMARY
if role.is_primary():
    advertise_ble()
else:
    scan_for_primary()
```

---

#### TherapyState

Therapy session state machine states.

```python
class TherapyState(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    LOW_BATTERY = "low_battery"
    CRITICAL_BATTERY = "critical_battery"
    CONNECTION_LOST = "connection_lost"
    PHONE_DISCONNECTED = "phone_disconnected"
```

**State Transitions:**
```
IDLE → CONNECTING → READY → RUNNING ⇄ PAUSED → STOPPING → IDLE
                        ↓
                      ERROR
```

**Methods:**

```python
def is_active() -> bool
```
Check if state represents an active session (RUNNING or PAUSED).

```python
def is_error() -> bool
```
Check if state represents an error condition.

```python
def is_battery_warning() -> bool
```
Check if state represents a battery warning.

```python
def can_start_therapy() -> bool
```
Check if therapy can be started from this state.

```python
def can_pause() -> bool
```
Check if therapy can be paused from this state.

```python
def can_resume() -> bool
```
Check if therapy can be resumed from this state.

**Usage:**
```python
state = TherapyState.RUNNING
if state.is_active():
    execute_therapy_cycle()
elif state.can_start_therapy():
    start_new_session()
```

---

#### BootResult

Boot sequence outcome enumeration.

```python
class BootResult(Enum):
    FAILED = "failed"
    SUCCESS_NO_PHONE = "success_no_phone"
    SUCCESS_WITH_PHONE = "success_with_phone"
    SUCCESS = "success"  # For SECONDARY
```

**Methods:**

```python
def is_success() -> bool
```
Check if boot was successful.

```python
def has_phone() -> bool
```
Check if phone connection was established.

**Usage:**
```python
result = await boot_manager.execute_boot_sequence()
if result.is_success():
    if result.has_phone():
        wait_for_phone_commands()
    else:
        start_default_therapy()
```

---

#### BatteryStatus

Battery status information dataclass.

```python
@dataclass
class BatteryStatus:
    voltage: float          # Current voltage in volts
    percentage: int         # Battery percentage (0-100)
    status: str            # Status string ("OK", "LOW", "CRITICAL")
    is_low: bool          # True if below LOW_VOLTAGE threshold
    is_critical: bool     # True if below CRITICAL_VOLTAGE threshold
```

**Methods:**

```python
def is_ok() -> bool
```
Check if battery status is OK (not low or critical).

```python
def requires_action() -> bool
```
Check if battery status requires user action.

**Usage:**
```python
battery = battery_monitor.get_status()
if battery.is_critical:
    shutdown_immediately()
elif battery.is_low:
    show_warning_led()
print(f"Battery: {battery.voltage:.2f}V ({battery.percentage}%)")
```

---

#### SessionInfo

Therapy session information dataclass.

```python
@dataclass
class SessionInfo:
    session_id: str        # Unique session identifier
    start_time: float      # Session start timestamp (monotonic time)
    duration_sec: int      # Total session duration in seconds
    elapsed_sec: int       # Elapsed time in seconds (excluding pauses)
    profile_name: str      # Therapy profile name
    state: TherapyState    # Current therapy state
```

**Methods:**

```python
def progress_percentage() -> int
```
Calculate session progress as percentage (0-100).

```python
def remaining_sec() -> int
```
Calculate remaining session time in seconds.

```python
def is_complete() -> bool
```
Check if session has reached its duration.

**Usage:**
```python
session = SessionInfo(
    session_id="session_001",
    start_time=time.monotonic(),
    duration_sec=7200,
    elapsed_sec=3600,
    profile_name="noisy_vcr",
    state=TherapyState.RUNNING
)

print(f"Progress: {session.progress_percentage()}%")
print(f"Remaining: {session.remaining_sec()}s")
```

---

### Module: `core.constants`

System-wide constants for timing, hardware, battery thresholds, and more.

#### Firmware Version

```python
FIRMWARE_VERSION: str = "2.0.0"
```
Current firmware version following semantic versioning.

---

#### Timing Constants

```python
STARTUP_WINDOW: int = 30
```
Boot sequence connection window in seconds.

```python
CONNECTION_TIMEOUT: int = 30
```
BLE connection establishment timeout in seconds.

```python
BLE_INTERVAL: float = 0.0075
```
BLE connection interval in seconds (7.5ms) for sub-10ms synchronization.

```python
SYNC_INTERVAL: float = 1.0
```
Periodic synchronization interval in seconds (SYNC_ADJ messages).

```python
COMMAND_TIMEOUT: float = 5.0
```
General BLE command timeout in seconds.

---

#### Hardware Constants

```python
I2C_MULTIPLEXER_ADDR: int = 0x70
```
TCA9548A I2C multiplexer address.

```python
DRV2605_DEFAULT_ADDR: int = 0x5A
```
DRV2605 haptic driver I2C address.

```python
I2C_FREQUENCY: int = 400000
```
I2C bus frequency in Hz (400 kHz Fast Mode).

```python
MAX_ACTUATORS: int = 5
```
Maximum number of haptic actuators per device (5 fingers).

```python
MAX_AMPLITUDE: int = 100
```
Maximum haptic amplitude percentage (0-100).

---

#### Pin Assignments

```python
NEOPIXEL_PIN: str = "D13"
```
NeoPixel LED data pin for visual feedback.

```python
BATTERY_PIN: str = "A6"
```
Battery voltage monitoring analog pin.

```python
I2C_SDA_PIN: str = "SDA"
```
I2C data line pin.

```python
I2C_SCL_PIN: str = "SCL"
```
I2C clock line pin.

---

#### LED Colors

```python
LED_BLUE: Tuple[int, int, int] = (0, 0, 255)     # BLE operations
LED_GREEN: Tuple[int, int, int] = (0, 255, 0)    # Success/Normal
LED_RED: Tuple[int, int, int] = (255, 0, 0)      # Error/Critical
LED_WHITE: Tuple[int, int, int] = (255, 255, 255) # Special indicators
LED_YELLOW: Tuple[int, int, int] = (255, 255, 0)  # Paused
LED_ORANGE: Tuple[int, int, int] = (255, 128, 0)  # Low battery
LED_OFF: Tuple[int, int, int] = (0, 0, 0)        # LED off
```

---

#### Battery Thresholds

```python
CRITICAL_VOLTAGE: float = 3.3
```
Critical battery voltage (immediate shutdown).

```python
LOW_VOLTAGE: float = 3.4
```
Low battery warning voltage (warning, therapy continues).

```python
BATTERY_CHECK_INTERVAL: float = 60.0
```
Battery voltage check interval in seconds during therapy.

---

#### Memory Management

```python
GC_THRESHOLD: int = 4096
```
Garbage collection threshold in bytes.

```python
GC_ENABLED: bool = True
```
Enable automatic garbage collection.

---

## Configuration System

### Module: `config.base`

#### BaseConfig

Base configuration with system defaults.

```python
@dataclass
class BaseConfig:
    device_role: DeviceRole
    firmware_version: str = "2.0.0"
    startup_window_sec: int = 30
    connection_timeout_sec: int = 30
    ble_interval: float = 0.0075
    sync_interval: float = 1.0
```

**Usage:**
```python
from config.base import BaseConfig
from core.types import DeviceRole

config = BaseConfig(
    device_role=DeviceRole.PRIMARY,
    startup_window_sec=30
)
```

---

### Module: `config.therapy`

#### TherapyConfig

Therapy-specific configuration.

```python
@dataclass
class TherapyConfig:
    profile_name: str
    burst_duration_ms: int
    inter_burst_interval_ms: int
    bursts_per_cycle: int
    pattern_type: str
    actuator_type: ActuatorType
    frequency_hz: int
    amplitude_percent: int
    jitter_percent: float = 0.0
    mirror_pattern: bool = True
```

**Class Methods:**

```python
@classmethod
def default_noisy_vcr() -> TherapyConfig
```
Create default Noisy vCR therapy configuration.

```python
@classmethod
def default_regular_vcr() -> TherapyConfig
```
Create default Regular vCR therapy configuration.

```python
@classmethod
def default_hybrid_vcr() -> TherapyConfig
```
Create default Hybrid vCR therapy configuration.

**Usage:**
```python
from config.therapy import TherapyConfig

# Use default profile
config = TherapyConfig.default_noisy_vcr()

# Custom profile
custom = TherapyConfig(
    profile_name="custom_research",
    burst_duration_ms=100,
    inter_burst_interval_ms=668,
    bursts_per_cycle=3,
    pattern_type="random_permutation",
    actuator_type=ActuatorType.LRA,
    frequency_hz=175,
    amplitude_percent=100,
    jitter_percent=23.5
)
```

---

### Module: `config.loader`

#### ConfigLoader

Loads and validates configuration from JSON files.

```python
class ConfigLoader:
    @staticmethod
    def load_from_json(path: str) -> Config

    @staticmethod
    def validate(config: Config) -> List[str]
```

**Usage:**
```python
from config.loader import ConfigLoader

# Load configuration
config = ConfigLoader.load_from_json("/settings.json")

# Validate configuration
errors = ConfigLoader.validate(config)
if errors:
    print(f"Configuration errors: {errors}")
```

---

## Event System

### Module: `events.bus`

#### EventBus

Publish-subscribe event bus for decoupled component communication.

```python
class EventBus:
    def __init__(self)

    def subscribe(
        self,
        event_type: Type[Event],
        handler: Callable[[Event], None]
    ) -> None

    def unsubscribe(
        self,
        event_type: Type[Event],
        handler: Callable[[Event], None]
    ) -> None

    def publish(self, event: Event) -> None

    def clear(self) -> None
```

**Usage:**
```python
from events.bus import EventBus
from events.events import SessionStartedEvent, BatteryLowEvent

bus = EventBus()

# Subscribe to events
def on_session_started(event: SessionStartedEvent):
    print(f"Session {event.session_id} started")

def on_battery_low(event: BatteryLowEvent):
    print(f"Battery low: {event.voltage}V")

bus.subscribe(SessionStartedEvent, on_session_started)
bus.subscribe(BatteryLowEvent, on_battery_low)

# Publish events
bus.publish(SessionStartedEvent(session_id="001", profile="noisy_vcr"))
bus.publish(BatteryLowEvent(voltage=3.3, percentage=15))

# Cleanup
bus.unsubscribe(SessionStartedEvent, on_session_started)
```

---

### Module: `events.events`

#### Event Classes

Base event class and specific event types.

```python
@dataclass
class Event:
    """Base event class."""
    timestamp: float = field(default_factory=time.monotonic)

@dataclass
class SessionStartedEvent(Event):
    session_id: str
    profile: str
    duration_sec: int

@dataclass
class SessionPausedEvent(Event):
    session_id: str

@dataclass
class SessionResumedEvent(Event):
    session_id: str

@dataclass
class SessionStoppedEvent(Event):
    session_id: str
    elapsed_sec: int
    cycles_completed: int

@dataclass
class BatteryLowEvent(Event):
    voltage: float
    percentage: int

@dataclass
class BatteryCriticalEvent(Event):
    voltage: float

@dataclass
class ConnectionLostEvent(Event):
    device_type: str  # "PRIMARY", "SECONDARY", or "PHONE"

@dataclass
class StateTransitionEvent(Event):
    from_state: TherapyState
    to_state: TherapyState
    trigger: str
```

**Usage:**
```python
from events.events import SessionStartedEvent
import time

event = SessionStartedEvent(
    session_id="session_001",
    profile="noisy_vcr",
    duration_sec=7200,
    timestamp=time.monotonic()
)
```

---

## State Machine

### Module: `state.machine`

#### TherapyStateMachine

Explicit state machine for therapy session management.

```python
class TherapyStateMachine:
    def __init__(self, event_bus: Optional[EventBus] = None)

    def get_current_state(self) -> TherapyState

    def transition(self, trigger: StateTrigger) -> bool

    def can_transition(self, trigger: StateTrigger) -> bool

    def reset(self) -> None

    def add_observer(
        self,
        callback: Callable[[TherapyState, TherapyState], None]
    ) -> None
```

**StateTrigger Enum:**
```python
class StateTrigger(Enum):
    POWER_ON = "power_on"
    CONNECT = "connect"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    START_SESSION = "start_session"
    PAUSE_SESSION = "pause_session"
    RESUME_SESSION = "resume_session"
    STOP_SESSION = "stop_session"
    SESSION_COMPLETE = "session_complete"
    ERROR_OCCURRED = "error_occurred"
    CRITICAL_BATTERY = "critical_battery"
    CONNECTION_LOST = "connection_lost"
    RESET = "reset"
```

**Usage:**
```python
from state.machine import TherapyStateMachine, StateTrigger
from events.bus import EventBus

# Create state machine
bus = EventBus()
state_machine = TherapyStateMachine(event_bus=bus)

# Check current state
print(f"Current state: {state_machine.get_current_state()}")

# Attempt transition
if state_machine.can_transition(StateTrigger.START_SESSION):
    success = state_machine.transition(StateTrigger.START_SESSION)
    if success:
        print("Session started successfully")

# Add observer for state changes
def on_state_change(from_state, to_state):
    print(f"State changed: {from_state} → {to_state}")

state_machine.add_observer(on_state_change)

# Reset state machine
state_machine.reset()
```

---

## Hardware Abstraction

### Module: `hardware.haptic`

#### HapticController (Abstract Base Class)

Abstract interface for haptic motor control.

```python
from abc import ABC, abstractmethod

class HapticController(ABC):
    @abstractmethod
    async def activate(self, finger: int, amplitude: int) -> None:
        """Activate motor for specified finger."""
        pass

    @abstractmethod
    async def deactivate(self, finger: int) -> None:
        """Deactivate motor for specified finger."""
        pass

    @abstractmethod
    async def deactivate_all(self) -> None:
        """Deactivate all motors."""
        pass

    @abstractmethod
    def is_active(self, finger: int) -> bool:
        """Check if motor is currently active."""
        pass
```

---

#### DRV2605Controller

Concrete implementation for DRV2605 haptic drivers.

```python
class DRV2605Controller(HapticController):
    def __init__(
        self,
        i2c: I2C,
        multiplexer: I2CMultiplexer,
        actuator_type: ActuatorType = ActuatorType.LRA,
        frequency_hz: int = 175
    )

    async def activate(self, finger: int, amplitude: int) -> None

    async def deactivate(self, finger: int) -> None

    async def deactivate_all(self) -> None

    def is_active(self, finger: int) -> bool

    def set_frequency(self, frequency_hz: int) -> None

    def set_actuator_type(self, actuator_type: ActuatorType) -> None
```

**Usage:**
```python
from hardware.haptic import DRV2605Controller
from hardware.multiplexer import I2CMultiplexer
from core.types import ActuatorType
import board
import busio

# Initialize I2C and multiplexer
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mux = I2CMultiplexer(i2c, address=0x70)

# Create haptic controller
haptic = DRV2605Controller(
    i2c=i2c,
    multiplexer=mux,
    actuator_type=ActuatorType.LRA,
    frequency_hz=175
)

# Activate motor
await haptic.activate(finger=0, amplitude=100)  # Thumb at 100%
await asyncio.sleep(0.1)
await haptic.deactivate(finger=0)

# Deactivate all motors
await haptic.deactivate_all()
```

---

### Module: `hardware.battery`

#### BatteryMonitor

Battery voltage monitoring and status reporting.

```python
class BatteryMonitor:
    def __init__(
        self,
        battery_pin: Pin,
        voltage_divider_ratio: float = 2.0,
        low_voltage: float = 3.4,
        critical_voltage: float = 3.3
    )

    def read_voltage(self) -> float

    def get_percentage(self) -> int

    def get_status(self) -> BatteryStatus

    def is_low(self) -> bool

    def is_critical(self) -> bool
```

**Usage:**
```python
from hardware.battery import BatteryMonitor
import board

# Create battery monitor
battery = BatteryMonitor(
    battery_pin=board.A6,
    voltage_divider_ratio=2.0,
    low_voltage=3.4,
    critical_voltage=3.3
)

# Read voltage
voltage = battery.read_voltage()
print(f"Battery: {voltage:.2f}V")

# Get full status
status = battery.get_status()
print(f"Status: {status.status} ({status.percentage}%)")

# Check critical conditions
if battery.is_critical():
    shutdown_device()
elif battery.is_low():
    show_warning()
```

---

### Module: `hardware.multiplexer`

#### I2CMultiplexer

TCA9548A I2C multiplexer for managing multiple DRV2605 devices.

```python
class I2CMultiplexer:
    def __init__(
        self,
        i2c: I2C,
        address: int = 0x70
    )

    def select_channel(self, channel: int) -> None

    def disable_all_channels(self) -> None

    def get_current_channel(self) -> Optional[int]
```

**Usage:**
```python
from hardware.multiplexer import I2CMultiplexer
import board
import busio

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Create multiplexer
mux = I2CMultiplexer(i2c, address=0x70)

# Select channel for finger 0 (thumb)
mux.select_channel(0)

# Communicate with DRV2605 on channel 0
# ...

# Disable all channels
mux.disable_all_channels()
```

---

### Module: `hardware.led`

#### LEDController (Base Class)

Base NeoPixel LED controller.

```python
class LEDController:
    def __init__(self, pixel_pin: Pin, num_pixels: int = 1)

    def set_color(self, color: Tuple[int, int, int]) -> None

    def off(self) -> None

    def rapid_flash(
        self,
        color: Tuple[int, int, int],
        frequency: float = 10.0
    ) -> None

    def slow_flash(
        self,
        color: Tuple[int, int, int],
        frequency: float = 1.0
    ) -> None

    def flash_count(
        self,
        color: Tuple[int, int, int],
        count: int
    ) -> None

    def solid(self, color: Tuple[int, int, int]) -> None
```

**Usage:**
```python
from hardware.led import LEDController
from core.constants import LED_GREEN, LED_RED
import board

# Create LED controller
led = LEDController(pixel_pin=board.D13, num_pixels=1)

# Solid green
led.solid(LED_GREEN)

# Flash red 5 times
led.flash_count(LED_RED, count=5)

# Turn off
led.off()
```

---

## BLE Communication

### Module: `communication.ble.service`

#### BLEService

Abstracted BLE communication service.

```python
class BLEService:
    def __init__(
        self,
        device_name: str,
        event_bus: Optional[EventBus] = None
    )

    async def advertise(self, name: str) -> None

    async def scan_and_connect(self, target_name: str) -> Connection

    async def send(self, connection: Connection, data: bytes) -> None

    async def receive(self, connection: Connection) -> Optional[bytes]

    async def disconnect(self, connection: Connection) -> None

    def is_connected(self) -> bool

    def get_connections(self) -> List[Connection]
```

**Usage:**
```python
from communication.ble.service import BLEService

# Create BLE service
ble = BLEService(device_name="BlueBuzzah")

# PRIMARY: Advertise
await ble.advertise(name="BlueBuzzah")

# SECONDARY: Scan and connect
connection = await ble.scan_and_connect(target_name="BlueBuzzah")

# Send data
await ble.send(connection, b"PING\n")

# Receive data
data = await ble.receive(connection)

# Disconnect
await ble.disconnect(connection)
```

---

### Module: `communication.protocol.commands`

#### CommandType (Enum)

BLE protocol command types.

```python
class CommandType(Enum):
    # Device Information
    INFO = "INFO"
    BATTERY = "BATTERY"
    PING = "PING"

    # Profile Management
    PROFILE_LIST = "PROFILE_LIST"
    PROFILE_LOAD = "PROFILE_LOAD"
    PROFILE_GET = "PROFILE_GET"
    PROFILE_CUSTOM = "PROFILE_CUSTOM"

    # Session Control
    SESSION_START = "SESSION_START"
    SESSION_PAUSE = "SESSION_PAUSE"
    SESSION_RESUME = "SESSION_RESUME"
    SESSION_STOP = "SESSION_STOP"
    SESSION_STATUS = "SESSION_STATUS"

    # Parameter Adjustment
    PARAM_SET = "PARAM_SET"

    # Calibration
    CALIBRATE_START = "CALIBRATE_START"
    CALIBRATE_BUZZ = "CALIBRATE_BUZZ"
    CALIBRATE_STOP = "CALIBRATE_STOP"

    # System
    HELP = "HELP"
    RESTART = "RESTART"
```

---

#### Command Classes

```python
@dataclass
class Command:
    command_type: CommandType
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw: Optional[str] = None

@dataclass
class InfoCommand(Command):
    command_type: CommandType = CommandType.INFO

@dataclass
class SessionStartCommand(Command):
    command_type: CommandType = CommandType.SESSION_START
    profile: str = ""
    duration_sec: int = 7200

@dataclass
class CalibrateCommand(Command):
    command_type: CommandType = CommandType.CALIBRATE_BUZZ
    finger: int = 0
    amplitude: int = 100
    duration_ms: int = 100
```

**Usage:**
```python
from communication.protocol.commands import SessionStartCommand, InfoCommand

# Create commands
info_cmd = InfoCommand()

start_cmd = SessionStartCommand(
    profile="noisy_vcr",
    duration_sec=7200
)

# Access command data
print(f"Command: {start_cmd.command_type}")
print(f"Profile: {start_cmd.profile}")
```

---

### Module: `communication.protocol.handler`

#### ProtocolHandler

BLE protocol message parsing and routing.

```python
class ProtocolHandler:
    def __init__(self, command_processor: CommandProcessor)

    def parse_command(self, data: bytes) -> Command

    def format_response(self, response: Response) -> bytes

    async def handle_command(self, command: Command) -> Response

    def validate_message(self, message: bytes) -> bool
```

**Usage:**
```python
from communication.protocol.handler import ProtocolHandler
from application.commands.processor import CommandProcessor

# Create handler
processor = CommandProcessor(...)
handler = ProtocolHandler(command_processor=processor)

# Parse incoming command
command = handler.parse_command(b"SESSION_START:noisy_vcr:7200\n")

# Handle command
response = await handler.handle_command(command)

# Format response
response_bytes = handler.format_response(response)
```

---

## Therapy Engine

### Module: `therapy.engine`

#### TherapyEngine

Core therapy execution engine.

```python
class TherapyEngine:
    def __init__(
        self,
        pattern_generator: PatternGenerator,
        haptic_controller: HapticController,
        battery_monitor: Optional[BatteryMonitor] = None,
        state_machine: Optional[TherapyStateMachine] = None
    )

    async def execute_session(
        self,
        config: TherapyConfig,
        duration_sec: int
    ) -> ExecutionStats

    async def execute_cycle(self, config: PatternConfig) -> None

    async def execute_pattern(self, pattern: Pattern) -> None

    def pause(self) -> None

    def resume(self) -> None

    def stop(self) -> None

    def is_paused(self) -> bool

    def is_stopped(self) -> bool

    def get_stats(self) -> ExecutionStats

    def on_cycle_complete(
        self,
        callback: Callable[[int], None]
    ) -> None

    def on_battery_warning(
        self,
        callback: Callable[[BatteryStatus], None]
    ) -> None

    def on_error(
        self,
        callback: Callable[[Exception], None]
    ) -> None
```

**ExecutionStats:**
```python
@dataclass
class ExecutionStats:
    cycles_completed: int = 0
    total_activations: int = 0
    average_cycle_duration_ms: float = 0.0
    timing_drift_ms: float = 0.0
    pause_count: int = 0
    total_pause_duration_sec: float = 0.0
```

**Usage:**
```python
from therapy.engine import TherapyEngine
from therapy.patterns.rndp import RandomPermutationGenerator
from hardware.haptic import DRV2605Controller
from hardware.battery import BatteryMonitor
from state.machine import TherapyStateMachine
from config.therapy import TherapyConfig

# Initialize components
pattern_gen = RandomPermutationGenerator()
haptic = DRV2605Controller(...)
battery = BatteryMonitor(...)
state_machine = TherapyStateMachine()

# Create engine
engine = TherapyEngine(
    pattern_generator=pattern_gen,
    haptic_controller=haptic,
    battery_monitor=battery,
    state_machine=state_machine
)

# Register callbacks
engine.on_cycle_complete(lambda count: print(f"Cycle {count}"))
engine.on_battery_warning(lambda status: print(f"Battery: {status}"))

# Execute therapy session
config = TherapyConfig.default_noisy_vcr()
stats = await engine.execute_session(config, duration_sec=7200)

print(f"Completed {stats.cycles_completed} cycles")
print(f"Average cycle duration: {stats.average_cycle_duration_ms:.1f}ms")
print(f"Timing drift: {stats.timing_drift_ms:.2f}ms")
```

---

### Module: `therapy.patterns.generator`

#### PatternGenerator (Abstract Base Class)

Abstract pattern generation interface.

```python
from abc import ABC, abstractmethod

class PatternGenerator(ABC):
    @abstractmethod
    def generate(self, config: PatternConfig) -> Pattern:
        """Generate therapy pattern from configuration."""
        pass

    def validate_config(self, config: PatternConfig) -> None:
        """Validate pattern configuration."""
        pass
```

---

#### Pattern

Therapy pattern dataclass.

```python
@dataclass
class Pattern:
    left_sequence: List[int]        # Left hand finger sequence
    right_sequence: List[int]       # Right hand finger sequence
    timing_ms: List[int]            # Inter-burst intervals (ms)
    burst_duration_ms: int          # Duration of each burst
    inter_burst_interval_ms: int   # Base interval between bursts

    def get_finger_pair(self, index: int) -> Tuple[int, int]:
        """Get left and right finger for given index."""
        return (self.left_sequence[index], self.right_sequence[index])

    def get_total_duration_ms(self) -> float:
        """Calculate total pattern duration in milliseconds."""
        return sum(self.timing_ms) + len(self.timing_ms) * self.burst_duration_ms
```

---

#### PatternConfig

Pattern generation configuration.

```python
@dataclass
class PatternConfig:
    num_fingers: int = 5
    time_on_ms: int = 100
    time_off_ms: int = 67
    bursts_per_cycle: int = 3
    jitter_percent: float = 0.0
    mirror_pattern: bool = True
    random_seed: Optional[int] = None

    @classmethod
    def from_therapy_config(cls, therapy_config: TherapyConfig) -> PatternConfig:
        """Convert TherapyConfig to PatternConfig."""
        pass

    def get_total_duration_ms(self) -> float:
        """Calculate total cycle duration in milliseconds."""
        pass
```

**Usage:**
```python
from therapy.patterns.generator import PatternConfig, Pattern

# Create configuration
config = PatternConfig(
    num_fingers=5,
    time_on_ms=100,
    time_off_ms=67,
    jitter_percent=23.5,
    mirror_pattern=True
)

# Pattern is generated by PatternGenerator implementations
```

---

### Module: `therapy.patterns.rndp`

#### RandomPermutationGenerator

Random permutation pattern generator for Noisy vCR therapy.

```python
class RandomPermutationGenerator(PatternGenerator):
    def __init__(self, random_seed: Optional[int] = None)

    def generate(self, config: PatternConfig) -> Pattern
```

**Usage:**
```python
from therapy.patterns.rndp import RandomPermutationGenerator
from therapy.patterns.generator import PatternConfig

# Create generator
generator = RandomPermutationGenerator()

# Generate pattern
config = PatternConfig(jitter_percent=23.5)
pattern = generator.generate(config)

print(f"Left sequence: {pattern.left_sequence}")
print(f"Right sequence: {pattern.right_sequence}")
# Output: [2, 0, 4, 1, 3] (random permutation)
```

---

### Module: `therapy.patterns.sequential`

#### SequentialGenerator

Sequential pattern generator for Regular vCR therapy.

```python
class SequentialGenerator(PatternGenerator):
    def __init__(self)

    def generate(self, config: PatternConfig) -> Pattern
```

**Usage:**
```python
from therapy.patterns.sequential import SequentialGenerator
from therapy.patterns.generator import PatternConfig

# Create generator
generator = SequentialGenerator()

# Generate pattern
config = PatternConfig()
pattern = generator.generate(config)

print(f"Left sequence: {pattern.left_sequence}")
# Output: [0, 1, 2, 3, 4] (sequential order)
```

---

### Module: `therapy.patterns.mirrored`

#### MirroredPatternGenerator

Mirrored bilateral pattern generator for Hybrid vCR therapy.

```python
class MirroredPatternGenerator(PatternGenerator):
    def __init__(self)

    def generate(self, config: PatternConfig) -> Pattern
```

**Usage:**
```python
from therapy.patterns.mirrored import MirroredPatternGenerator
from therapy.patterns.generator import PatternConfig

# Create generator
generator = MirroredPatternGenerator()

# Generate pattern
config = PatternConfig()
pattern = generator.generate(config)

print(f"Left: {pattern.left_sequence}")
print(f"Right: {pattern.right_sequence}")
# Sequences are mirrored for bilateral symmetry
```

---

## Synchronization Protocol

### Module: `domain.sync.protocol`

#### SyncProtocol

Time synchronization between PRIMARY and SECONDARY devices.

```python
class SyncProtocol:
    def __init__(self)

    def calculate_offset(
        self,
        primary_time: int,
        secondary_time: int
    ) -> int

    def apply_compensation(
        self,
        timestamp: int,
        offset: int
    ) -> int

    def format_sync_message(
        self,
        command_type: SyncCommandType,
        payload: Dict[str, Any]
    ) -> bytes

    def parse_sync_message(self, data: bytes) -> Tuple[SyncCommandType, Dict]
```

**Usage:**
```python
from domain.sync.protocol import SyncProtocol
import time

# Create sync protocol
sync = SyncProtocol()

# Calculate time offset (PRIMARY)
primary_time = time.monotonic_ns()
secondary_time = time.monotonic_ns()  # From SECONDARY
offset = sync.calculate_offset(primary_time, secondary_time)

# Apply compensation (SECONDARY)
compensated_time = sync.apply_compensation(
    timestamp=primary_time,
    offset=offset
)

# Format sync message
message = sync.format_sync_message(
    command_type=SyncCommandType.SYNC_ADJ,
    payload={"timestamp": primary_time}
)

# Parse sync message
cmd_type, payload = sync.parse_sync_message(message)
```

---

### Module: `domain.sync.coordinator`

#### SyncCoordinator

Coordinates bilateral synchronization between devices.

```python
class SyncCoordinator:
    def __init__(
        self,
        role: DeviceRole,
        sync_protocol: SyncProtocol,
        ble_service: BLEService
    )

    async def establish_sync(self) -> bool

    async def send_sync_adjustment(self, timestamp: int) -> None

    async def send_execute_command(
        self,
        sequence_index: int,
        timestamp: int
    ) -> None

    async def wait_for_acknowledgment(self, timeout: float = 2.0) -> bool

    def get_time_offset(self) -> int
```

**Usage:**
```python
from domain.sync.coordinator import SyncCoordinator
from domain.sync.protocol import SyncProtocol
from communication.ble.service import BLEService
from core.types import DeviceRole

# Initialize coordinator (PRIMARY)
sync_protocol = SyncProtocol()
ble = BLEService("BlueBuzzah")
coordinator = SyncCoordinator(
    role=DeviceRole.PRIMARY,
    sync_protocol=sync_protocol,
    ble_service=ble
)

# Establish initial synchronization
success = await coordinator.establish_sync()

# Send periodic sync adjustment
await coordinator.send_sync_adjustment(timestamp=time.monotonic_ns())

# Send execute command
await coordinator.send_execute_command(
    sequence_index=2,
    timestamp=time.monotonic_ns()
)

# Wait for acknowledgment
ack = await coordinator.wait_for_acknowledgment(timeout=2.0)
```

---

## Application Layer

### Module: `application.session.manager`

#### SessionManager

High-level session lifecycle management.

```python
class SessionManager:
    def __init__(
        self,
        therapy_engine: TherapyEngine,
        profile_manager: ProfileManager,
        event_bus: EventBus
    )

    async def start_session(
        self,
        profile_name: str,
        duration_sec: int
    ) -> SessionInfo

    async def pause_session(self) -> None

    async def resume_session(self) -> None

    async def stop_session(self) -> None

    def get_current_session(self) -> Optional[SessionInfo]

    def get_status(self) -> Dict[str, Any]
```

**Usage:**
```python
from application.session.manager import SessionManager
from therapy.engine import TherapyEngine
from application.profile.manager import ProfileManager
from events.bus import EventBus

# Initialize manager
engine = TherapyEngine(...)
profile_mgr = ProfileManager()
event_bus = EventBus()

session_mgr = SessionManager(
    therapy_engine=engine,
    profile_manager=profile_mgr,
    event_bus=event_bus
)

# Start session
session = await session_mgr.start_session(
    profile_name="noisy_vcr",
    duration_sec=7200
)

# Pause session
await session_mgr.pause_session()

# Resume session
await session_mgr.resume_session()

# Get status
status = session_mgr.get_status()
print(f"Session: {status}")

# Stop session
await session_mgr.stop_session()
```

---

### Module: `application.profile.manager`

#### ProfileManager

Therapy profile management and loading.

```python
class ProfileManager:
    def __init__(self, profiles_dir: str = "/profiles")

    def list_profiles(self) -> List[str]

    def load_profile(self, profile_name: str) -> TherapyConfig

    def save_profile(
        self,
        profile_name: str,
        config: TherapyConfig
    ) -> None

    def delete_profile(self, profile_name: str) -> None

    def get_default_profile(self) -> TherapyConfig
```

**Usage:**
```python
from application.profile.manager import ProfileManager

# Create manager
profile_mgr = ProfileManager(profiles_dir="/profiles")

# List available profiles
profiles = profile_mgr.list_profiles()
print(f"Available profiles: {profiles}")

# Load profile
config = profile_mgr.load_profile("noisy_vcr")

# Save custom profile
custom_config = TherapyConfig(...)
profile_mgr.save_profile("custom_research", custom_config)

# Get default profile
default = profile_mgr.get_default_profile()
```

---

### Module: `application.calibration.controller`

#### CalibrationController

Calibration mode for individual finger testing.

```python
class CalibrationController:
    def __init__(
        self,
        haptic_controller: HapticController,
        event_bus: EventBus
    )

    async def start_calibration(self) -> None

    async def test_finger(
        self,
        finger: int,
        amplitude: int = 100,
        duration_ms: int = 100
    ) -> None

    async def test_all_fingers(
        self,
        amplitude: int = 100,
        duration_ms: int = 100
    ) -> None

    async def stop_calibration(self) -> None

    def is_calibrating(self) -> bool
```

**Usage:**
```python
from application.calibration.controller import CalibrationController
from hardware.haptic import DRV2605Controller
from events.bus import EventBus

# Create controller
haptic = DRV2605Controller(...)
event_bus = EventBus()
calibration = CalibrationController(
    haptic_controller=haptic,
    event_bus=event_bus
)

# Start calibration mode
await calibration.start_calibration()

# Test individual finger
await calibration.test_finger(
    finger=0,       # Thumb
    amplitude=75,   # 75% intensity
    duration_ms=200 # 200ms buzz
)

# Test all fingers sequentially
await calibration.test_all_fingers(amplitude=100, duration_ms=100)

# Stop calibration
await calibration.stop_calibration()
```

---

### Module: `application.commands.processor`

#### CommandProcessor

Central command routing and processing.

```python
class CommandProcessor:
    def __init__(
        self,
        session_manager: SessionManager,
        profile_manager: ProfileManager,
        calibration_controller: CalibrationController,
        battery_monitor: BatteryMonitor
    )

    async def process_command(self, command: Command) -> Response

    def register_handler(
        self,
        command_type: CommandType,
        handler: Callable[[Command], Response]
    ) -> None
```

**Usage:**
```python
from application.commands.processor import CommandProcessor
from communication.protocol.commands import SessionStartCommand

# Create processor
processor = CommandProcessor(
    session_manager=session_mgr,
    profile_manager=profile_mgr,
    calibration_controller=calibration,
    battery_monitor=battery
)

# Process command
command = SessionStartCommand(profile="noisy_vcr", duration_sec=7200)
response = await processor.process_command(command)

print(f"Response: {response.status}")
```

---

## LED UI

### Module: `ui.boot_led`

#### BootSequenceLEDController

Specialized LED controller for boot sequence visual feedback.

```python
class BootSequenceLEDController(LEDController):
    def indicate_ble_init(self) -> None

    def indicate_connection_success(self) -> None

    def indicate_waiting_for_phone(self) -> None

    def indicate_ready(self) -> None

    def indicate_failure(self) -> None
```

**Usage:**
```python
from ui.boot_led import BootSequenceLEDController
import board

# Create boot LED controller
led = BootSequenceLEDController(pixel_pin=board.D13)

# Boot sequence stages
led.indicate_ble_init()              # Rapid blue flash
# ... wait for connections ...
led.indicate_connection_success()    # 5x green flash
led.indicate_waiting_for_phone()     # Slow blue flash
# ... timeout or phone connects ...
led.indicate_ready()                 # Solid green

# Or on failure
led.indicate_failure()               # Slow red flash
```

---

### Module: `ui.therapy_led`

#### TherapyLEDController

LED controller for therapy session visual feedback.

```python
class TherapyLEDController(LEDController):
    def set_therapy_state(self, state: TherapyState) -> None

    def update_breathing(self) -> None

    def fade_out(
        self,
        color: Tuple[int, int, int],
        duration_sec: float
    ) -> None

    def alternate_flash(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        frequency: float
    ) -> None
```

**Usage:**
```python
from ui.therapy_led import TherapyLEDController
from core.types import TherapyState
import board

# Create therapy LED controller
led = TherapyLEDController(pixel_pin=board.D13)

# Set state-based LED patterns
led.set_therapy_state(TherapyState.RUNNING)  # Breathing green
led.set_therapy_state(TherapyState.PAUSED)   # Slow yellow pulse
led.set_therapy_state(TherapyState.STOPPING) # Fading green

# Update breathing effect (call periodically at ~20Hz)
while therapy_running:
    led.update_breathing()
    await asyncio.sleep(0.05)
```

---

## Usage Examples

### Complete System Initialization

```python
import asyncio
import board
import busio
from core.types import DeviceRole
from config.loader import ConfigLoader
from config.therapy import TherapyConfig
from events.bus import EventBus
from state.machine import TherapyStateMachine
from hardware.haptic import DRV2605Controller
from hardware.battery import BatteryMonitor
from hardware.multiplexer import I2CMultiplexer
from communication.ble.service import BLEService
from therapy.engine import TherapyEngine
from therapy.patterns.rndp import RandomPermutationGenerator
from application.session.manager import SessionManager
from application.profile.manager import ProfileManager
from ui.boot_led import BootSequenceLEDController
from ui.therapy_led import TherapyLEDController
from boot.manager import BootSequenceManager

async def main():
    # Load device configuration
    config = ConfigLoader.load_from_json("/settings.json")

    # Initialize event bus
    event_bus = EventBus()

    # Initialize hardware
    i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
    mux = I2CMultiplexer(i2c, address=0x70)
    haptic = DRV2605Controller(i2c, mux)
    battery = BatteryMonitor(board.A6)

    # Initialize LED controllers
    boot_led = BootSequenceLEDController(board.D13)
    therapy_led = TherapyLEDController(board.D13)

    # Initialize BLE
    ble = BLEService(device_name="BlueBuzzah", event_bus=event_bus)

    # Execute boot sequence
    boot_manager = BootSequenceManager(
        role=config.device.role,
        ble_service=ble,
        led_controller=boot_led
    )
    boot_result = await boot_manager.execute_boot_sequence()

    if not boot_result.is_success():
        print("Boot failed - exiting")
        return

    # Initialize therapy components
    state_machine = TherapyStateMachine(event_bus=event_bus)
    pattern_gen = RandomPermutationGenerator()
    therapy_engine = TherapyEngine(
        pattern_generator=pattern_gen,
        haptic_controller=haptic,
        battery_monitor=battery,
        state_machine=state_machine
    )

    # Initialize application layer
    profile_mgr = ProfileManager()
    session_mgr = SessionManager(
        therapy_engine=therapy_engine,
        profile_manager=profile_mgr,
        event_bus=event_bus
    )

    # Start therapy session
    therapy_config = TherapyConfig.default_noisy_vcr()
    session = await session_mgr.start_session(
        profile_name="noisy_vcr",
        duration_sec=7200
    )

    print(f"Session started: {session.session_id}")

    # Main loop
    while not session.is_complete():
        # Update LED
        therapy_led.set_therapy_state(state_machine.get_current_state())
        therapy_led.update_breathing()

        # Check for commands from phone
        # ...

        await asyncio.sleep(0.05)

    print("Session complete")

# Run application
asyncio.run(main())
```

---

### Simple Therapy Execution

```python
from therapy.engine import TherapyEngine
from therapy.patterns.rndp import RandomPermutationGenerator
from hardware.haptic import DRV2605Controller
from config.therapy import TherapyConfig

# Create components
pattern_gen = RandomPermutationGenerator()
haptic = DRV2605Controller()  # Actual hardware controller

# Create engine
engine = TherapyEngine(
    pattern_generator=pattern_gen,
    haptic_controller=haptic
)

# Execute therapy
config = TherapyConfig.default_noisy_vcr()
stats = await engine.execute_session(config, duration_sec=60)

print(f"Completed {stats.cycles_completed} cycles")
```

---

### Event-Driven Architecture

```python
from events.bus import EventBus
from events.events import (
    SessionStartedEvent,
    SessionPausedEvent,
    BatteryLowEvent
)

# Create event bus
bus = EventBus()

# Define handlers
def on_session_started(event: SessionStartedEvent):
    print(f"Session {event.session_id} started with {event.profile}")
    led.indicate_therapy_running()

def on_session_paused(event: SessionPausedEvent):
    print(f"Session {event.session_id} paused")
    led.indicate_paused()

def on_battery_low(event: BatteryLowEvent):
    print(f"Low battery: {event.voltage}V ({event.percentage}%)")
    led.indicate_low_battery()

# Subscribe handlers
bus.subscribe(SessionStartedEvent, on_session_started)
bus.subscribe(SessionPausedEvent, on_session_paused)
bus.subscribe(BatteryLowEvent, on_battery_low)

# Publish events (done automatically by components)
bus.publish(SessionStartedEvent(
    session_id="001",
    profile="noisy_vcr",
    duration_sec=7200
))
```

---

### Custom Pattern Generator

```python
from therapy.patterns.generator import PatternGenerator, Pattern, PatternConfig
from typing import List

class CustomPatternGenerator(PatternGenerator):
    """Custom pattern with specific research requirements."""

    def generate(self, config: PatternConfig) -> Pattern:
        # Validate configuration
        self.validate_config(config)

        # Generate custom sequence (e.g., alternating pairs)
        left_sequence = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
        right_sequence = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]

        # Calculate timing
        timing_ms = [config.time_on_ms + config.time_off_ms] * len(left_sequence)

        return Pattern(
            left_sequence=left_sequence,
            right_sequence=right_sequence,
            timing_ms=timing_ms,
            burst_duration_ms=config.time_on_ms,
            inter_burst_interval_ms=config.time_off_ms
        )

# Use custom generator
custom_gen = CustomPatternGenerator()
config = PatternConfig(time_on_ms=150, time_off_ms=100)
pattern = custom_gen.generate(config)
```

---

### State Machine Integration

```python
from state.machine import TherapyStateMachine, StateTrigger
from events.bus import EventBus

# Create state machine with event bus
event_bus = EventBus()
state_machine = TherapyStateMachine(event_bus=event_bus)

# Add observer for state changes
def on_state_change(from_state, to_state):
    print(f"State: {from_state} → {to_state}")
    update_led(to_state)

state_machine.add_observer(on_state_change)

# Perform transitions
state_machine.transition(StateTrigger.CONNECTED)
state_machine.transition(StateTrigger.START_SESSION)
state_machine.transition(StateTrigger.PAUSE_SESSION)
state_machine.transition(StateTrigger.RESUME_SESSION)
state_machine.transition(StateTrigger.STOP_SESSION)

# Check state
current = state_machine.get_current_state()
if current.can_start_therapy():
    start_session()
```

---

## Type Aliases and Imports

### Common Import Patterns

```python
# Core types
from core.types import (
    DeviceRole, TherapyState, BootResult,
    ActuatorType, BatteryStatus, SessionInfo
)

# Constants
from core.constants import (
    FIRMWARE_VERSION,
    STARTUP_WINDOW,
    BLE_INTERVAL,
    CRITICAL_VOLTAGE,
    LOW_VOLTAGE,
    LED_GREEN,
    LED_RED
)

# Configuration
from config.base import BaseConfig
from config.therapy import TherapyConfig
from config.loader import ConfigLoader

# Events
from events.bus import EventBus
from events.events import (
    SessionStartedEvent,
    SessionPausedEvent,
    BatteryLowEvent
)

# State management
from state.machine import TherapyStateMachine, StateTrigger

# Hardware
from hardware.haptic import HapticController, DRV2605Controller
from hardware.battery import BatteryMonitor
from hardware.multiplexer import I2CMultiplexer

# Communication
from communication.ble.service import BLEService
from communication.protocol.commands import Command, CommandType
from communication.protocol.handler import ProtocolHandler

# Therapy
from therapy.engine import TherapyEngine
from therapy.patterns.generator import PatternGenerator, Pattern
from therapy.patterns.rndp import RandomPermutationGenerator

# Application
from application.session.manager import SessionManager
from application.profile.manager import ProfileManager
from application.calibration.controller import CalibrationController

# UI
from ui.boot_led import BootSequenceLEDController
from ui.therapy_led import TherapyLEDController
```

---

## Error Handling

### Common Exceptions

```python
# Configuration errors
try:
    config = ConfigLoader.load_from_json("/settings.json")
except FileNotFoundError:
    print("Settings file not found")
except ValueError as e:
    print(f"Invalid configuration: {e}")

# Therapy errors
try:
    await engine.execute_session(config, duration_sec=7200)
except RuntimeError as e:
    print(f"Therapy execution failed: {e}")
    state_machine.transition(StateTrigger.ERROR_OCCURRED)

# Battery errors
if battery.is_critical():
    raise RuntimeError(f"Critical battery: {battery.read_voltage()}V")

# BLE errors
try:
    connection = await ble.scan_and_connect("BlueBuzzah")
except TimeoutError:
    print("Connection timeout")
    boot_result = BootResult.FAILED
```

---

## Testing

BlueBuzzah v2 uses **hardware integration testing** to validate firmware functionality on actual Feather nRF52840 devices.

**Current Test Coverage:**
- 8/18 BLE protocol commands tested (44%)
- Calibration commands (CALIBRATE_START, CALIBRATE_BUZZ, CALIBRATE_STOP)
- Session commands (SESSION_START, SESSION_PAUSE, SESSION_RESUME, SESSION_STOP, SESSION_STATUS)
- Memory stress testing
- Synchronization latency measurement

**Testing Approach:**
- Manual testing on actual hardware via BLE
- No automated unit tests or mocks currently implemented
- See [Testing Guide](TESTING.md) for detailed procedures

**Future Testing:**
- Automated unit tests with mock implementations (planned)
- CI/CD integration (planned)
- Code coverage reporting (planned)

---

## Version Information

**API Version**: 2.0.0
**Protocol Version**: 2.0.0
**Firmware Version**: 2.0.0

---

## Additional Resources

- [Architecture Guide](ARCHITECTURE.md) - System design and patterns
- [Boot Sequence](BOOT_SEQUENCE.md) - Boot process and LED indicators
- [Therapy Engine](THERAPY_ENGINE.md) - Pattern generation and timing
- [Deployment Guide](DEPLOYMENT.md) - Deployment procedures
- [Testing Guide](TESTING.md) - Hardware integration testing procedures
- [Changelog](CHANGELOG.md) - Version history

---

## Support

For questions, issues, or contributions:

- **GitHub**: [BlueBuzzah Repository](https://github.com/yourusername/bluebuzzah)
- **Issues**: [GitHub Issues](https://github.com/yourusername/bluebuzzah/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/bluebuzzah/discussions)

---

**Last Updated**: 2025-01-11
**Document Version**: 1.0.0
