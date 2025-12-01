# Debugging Techniques for nRF52840 Firmware

Practical debugging strategies for embedded development without traditional debuggers.

## Serial Debugging Patterns

### Structured Logging Format

Use consistent, parseable log output for easier debugging.

```cpp
// Format: [timestamp] [MODULE] MESSAGE
#define LOG(module, msg) do { \
    Serial.print("["); \
    Serial.print(millis()); \
    Serial.print("] ["); \
    Serial.print(module); \
    Serial.print("] "); \
    Serial.println(msg); \
} while(0)

#define LOG_VAL(module, name, val) do { \
    Serial.print("["); \
    Serial.print(millis()); \
    Serial.print("] ["); \
    Serial.print(module); \
    Serial.print("] "); \
    Serial.print(name); \
    Serial.print(": "); \
    Serial.println(val); \
} while(0)

// Usage
LOG("BLE", "Connected");
LOG_VAL("MOTOR", "amplitude", 75);
```

### Conditional Debug Output

Compile-time debug flags to reduce release binary size.

```cpp
// In config.h
#define DEBUG_BLE 1
#define DEBUG_MOTOR 0
#define DEBUG_TIMING 1

#if DEBUG_BLE
#define DBG_BLE(msg) LOG("BLE", msg)
#else
#define DBG_BLE(msg)
#endif

#if DEBUG_MOTOR
#define DBG_MOTOR(msg) LOG("MOTOR", msg)
#else
#define DBG_MOTOR(msg)
#endif
```

### State Transition Logging

Log state machine transitions for debugging flow issues.

```cpp
void transitionTo(TherapyState newState) {
    Serial.print("[");
    Serial.print(millis());
    Serial.print("] STATE: ");
    Serial.print(stateToString(_currentState));
    Serial.print(" -> ");
    Serial.println(stateToString(newState));

    _previousState = _currentState;
    _currentState = newState;
    notifyCallbacks();
}

const char* stateToString(TherapyState state) {
    switch (state) {
        case TherapyState::IDLE: return "IDLE";
        case TherapyState::READY: return "READY";
        case TherapyState::RUNNING: return "RUNNING";
        case TherapyState::PAUSED: return "PAUSED";
        case TherapyState::ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}
```

### Timing Markers

Track execution timing for performance debugging.

```cpp
uint32_t loopStart;
uint32_t maxLoopTime = 0;

void loop() {
    loopStart = micros();

    // ... main loop code ...

    uint32_t loopTime = micros() - loopStart;
    if (loopTime > maxLoopTime) {
        maxLoopTime = loopTime;
        Serial.print("[PERF] New max loop time: ");
        Serial.print(loopTime);
        Serial.println(" us");
    }
}
```

## LED Status Codes

Use NeoPixel for visual state indication when Serial isn't available.

### Color Conventions

```cpp
// Common color meanings (customize as needed)
#define COLOR_IDLE       0x000044  // Dim blue - waiting
#define COLOR_READY      0x004400  // Dim green - ready
#define COLOR_RUNNING    0x444400  // Yellow - active
#define COLOR_PAUSED     0x440044  // Purple - paused
#define COLOR_ERROR      0x440000  // Red - error
#define COLOR_CONNECTED  0x004444  // Cyan - BLE connected
#define COLOR_LOW_BATT   0x220000  // Dim red pulse

void setStatusColor(uint32_t color) {
    pixel.setPixelColor(0, color);
    pixel.show();
}
```

### Blink Patterns for States

```cpp
struct BlinkPattern {
    uint32_t color;
    uint16_t onMs;
    uint16_t offMs;
    uint8_t count;  // 0 = continuous
};

const BlinkPattern PATTERN_SEARCHING = {0x000044, 500, 500, 0};
const BlinkPattern PATTERN_ERROR     = {0x440000, 100, 100, 3};
const BlinkPattern PATTERN_SUCCESS   = {0x004400, 200, 0, 1};

class StatusLED {
private:
    BlinkPattern _pattern;
    uint32_t _lastToggle;
    bool _ledOn;
    uint8_t _blinkCount;
    bool _active;

public:
    void setPattern(const BlinkPattern& pattern) {
        _pattern = pattern;
        _lastToggle = millis();
        _ledOn = true;
        _blinkCount = 0;
        _active = true;
        setStatusColor(_pattern.color);
    }

    void update() {
        if (!_active) return;

        uint32_t now = millis();
        uint32_t interval = _ledOn ? _pattern.onMs : _pattern.offMs;

        if (now - _lastToggle >= interval) {
            _lastToggle = now;
            _ledOn = !_ledOn;

            if (_ledOn) {
                setStatusColor(_pattern.color);
                if (_pattern.count > 0) {
                    _blinkCount++;
                    if (_blinkCount >= _pattern.count) {
                        _active = false;
                        setStatusColor(0);
                    }
                }
            } else {
                setStatusColor(0);
            }
        }
    }
};
```

### Error Code Flashing

Flash specific patterns for different error types.

```cpp
void flashErrorCode(uint8_t errorCode) {
    // Flash red: errorCode times, then pause
    for (uint8_t i = 0; i < errorCode; i++) {
        setStatusColor(0x440000);
        delay(200);
        setStatusColor(0);
        delay(200);
    }
    delay(1000);  // Pause before repeat
}

// Error codes
#define ERR_I2C_FAIL      1
#define ERR_BLE_FAIL      2
#define ERR_MOTOR_FAIL    3
#define ERR_CONFIG_FAIL   4
```

## I2C Bus Diagnostics

### I2C Scanner

Verify device addresses on the bus.

```cpp
void scanI2C() {
    Serial.println("[I2C] Scanning...");
    uint8_t count = 0;

    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        uint8_t error = Wire.endTransmission();

        if (error == 0) {
            Serial.print("[I2C] Found device at 0x");
            if (addr < 16) Serial.print("0");
            Serial.println(addr, HEX);
            count++;
        }
    }

    Serial.print("[I2C] Scan complete. Found ");
    Serial.print(count);
    Serial.println(" device(s)");
}
```

### Multiplexer Channel Verification

For TCA9548A multiplexer debugging.

```cpp
void scanMultiplexerChannels() {
    Serial.println("[MUX] Scanning all channels...");

    for (uint8_t channel = 0; channel < 8; channel++) {
        selectChannel(channel);
        Serial.print("[MUX] Channel ");
        Serial.print(channel);
        Serial.print(": ");

        // Scan for devices on this channel
        uint8_t count = 0;
        for (uint8_t addr = 1; addr < 127; addr++) {
            if (addr == TCA9548A_ADDR) continue;  // Skip mux itself

            Wire.beginTransmission(addr);
            if (Wire.endTransmission() == 0) {
                Serial.print("0x");
                if (addr < 16) Serial.print("0");
                Serial.print(addr, HEX);
                Serial.print(" ");
                count++;
            }
        }

        if (count == 0) Serial.print("(empty)");
        Serial.println();
    }

    closeChannels();
}
```

### I2C Transaction Logging

```cpp
#define I2C_DEBUG 1

bool i2cWrite(uint8_t addr, uint8_t reg, uint8_t value) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    Wire.write(value);
    uint8_t error = Wire.endTransmission();

    #if I2C_DEBUG
    Serial.print("[I2C] Write 0x");
    Serial.print(addr, HEX);
    Serial.print(" reg=0x");
    Serial.print(reg, HEX);
    Serial.print(" val=0x");
    Serial.print(value, HEX);
    Serial.print(" -> ");
    Serial.println(error == 0 ? "OK" : "FAIL");
    #endif

    return error == 0;
}
```

## Memory Monitoring

### Free Memory Check

```cpp
extern "C" char* sbrk(int incr);

int freeMemory() {
    char top;
    return &top - reinterpret_cast<char*>(sbrk(0));
}

void logMemory() {
    Serial.print("[MEM] Free: ");
    Serial.print(freeMemory());
    Serial.println(" bytes");
}
```

### Heap Fragmentation Detection

Monitor memory over time to detect fragmentation.

```cpp
int _minFreeMemory = INT_MAX;

void checkMemoryHealth() {
    int current = freeMemory();

    if (current < _minFreeMemory) {
        _minFreeMemory = current;
        Serial.print("[MEM] New minimum: ");
        Serial.println(current);
    }

    // Warn if memory is getting low
    if (current < 10000) {
        Serial.println("[MEM] WARNING: Low memory!");
    }
}
```

### Stack Usage Estimation

```cpp
// Paint stack with known pattern at startup
void paintStack() {
    volatile uint8_t* p = (uint8_t*)sbrk(0);
    while (p < (uint8_t*)&p - 256) {  // Leave safety margin
        *p++ = 0xAA;
    }
}

// Check how much stack was used
int getStackHighWaterMark() {
    uint8_t* p = (uint8_t*)sbrk(0);
    int count = 0;
    while (*p == 0xAA && count < 50000) {
        p++;
        count++;
    }
    return count;
}
```

## BLE Connection Debugging

### Connection State Logging

```cpp
void logConnectionState() {
    Serial.print("[BLE] Connections: ");
    Serial.print(Bluefruit.connected());
    Serial.print(" | Advertising: ");
    Serial.print(Bluefruit.Advertising.isRunning());
    Serial.print(" | Scanning: ");
    Serial.println(Bluefruit.Scanner.isRunning());
}

// Log detailed connection info
void logConnectionDetails(uint16_t connHandle) {
    BLEConnection* conn = Bluefruit.Connection(connHandle);
    if (!conn) return;

    Serial.print("[BLE] Handle: ");
    Serial.print(connHandle);
    Serial.print(" | MTU: ");
    Serial.print(conn->getMtu());
    Serial.print(" | Interval: ");
    Serial.print(conn->getConnectionInterval());
    Serial.print("ms | Role: ");
    Serial.println(conn->getRole() == BLE_GAP_ROLE_PERIPH ? "PERIPH" : "CENTRAL");
}
```

### RSSI Monitoring

```cpp
void logRSSI(uint16_t connHandle) {
    BLEConnection* conn = Bluefruit.Connection(connHandle);
    if (conn) {
        int8_t rssi = conn->getRssi();
        Serial.print("[BLE] RSSI: ");
        Serial.print(rssi);
        Serial.println(" dBm");

        // Signal strength indicators
        if (rssi > -50) Serial.println("[BLE] Signal: Excellent");
        else if (rssi > -60) Serial.println("[BLE] Signal: Good");
        else if (rssi > -70) Serial.println("[BLE] Signal: Fair");
        else Serial.println("[BLE] Signal: Weak");
    }
}
```

## Logic Analyzer Integration

### Debug Pin Toggles

Toggle GPIO pins for timing analysis with logic analyzer.

```cpp
#define DEBUG_PIN_LOOP 2
#define DEBUG_PIN_BLE  3
#define DEBUG_PIN_MOTOR 4

void setupDebugPins() {
    pinMode(DEBUG_PIN_LOOP, OUTPUT);
    pinMode(DEBUG_PIN_BLE, OUTPUT);
    pinMode(DEBUG_PIN_MOTOR, OUTPUT);
}

void loop() {
    digitalWrite(DEBUG_PIN_LOOP, HIGH);

    // ... loop code ...

    digitalWrite(DEBUG_PIN_LOOP, LOW);
}

void onBleCallback() {
    digitalWrite(DEBUG_PIN_BLE, HIGH);
    // ... callback code ...
    digitalWrite(DEBUG_PIN_BLE, LOW);
}
```

### Pulse for Event Marking

```cpp
inline void debugPulse(uint8_t pin, uint8_t count = 1) {
    for (uint8_t i = 0; i < count; i++) {
        digitalWrite(pin, HIGH);
        delayMicroseconds(1);
        digitalWrite(pin, LOW);
        if (i < count - 1) delayMicroseconds(1);
    }
}
```

## Common Failure Modes

| Symptom | Likely Cause | Diagnostic |
|---------|--------------|------------|
| BLE disconnects randomly | Loop blocking too long | Add timing markers, check max loop time |
| I2C hangs | Bus stuck, missing pullups | Scan bus, check pullup resistors |
| Memory grows over time | Heap fragmentation | Log free memory periodically |
| Scanner stops working | Library bug | Add health check with auto-restart |
| Motor doesn't respond | Mux channel issue | Scan mux channels, verify I2C |
| Erratic behavior | Stack overflow | Paint stack, check high water mark |
| Slow response | Blocking operations | Profile with debug pins |
