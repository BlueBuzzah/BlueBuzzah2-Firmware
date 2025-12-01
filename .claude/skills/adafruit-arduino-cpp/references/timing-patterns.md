# Non-Blocking Timing Patterns for nRF52840

Techniques for implementing precise timing without blocking the BLE stack or main loop.

## Why Non-Blocking Matters

The nRF52840 BLE stack requires regular servicing. Blocking calls like `delay()` prevent:
- BLE packet processing (causes disconnects)
- Connection parameter updates
- Advertising/scanning operations
- Peripheral callbacks

**Rule**: Never block for more than a few milliseconds in the main loop.

## millis()-Based State Machine Template

The fundamental pattern for non-blocking timing uses `millis()` to track elapsed time.

### Basic Structure

```cpp
class TimedOperation {
private:
    uint32_t _startTime;
    uint32_t _duration;
    bool _active;

public:
    void start(uint32_t durationMs) {
        _startTime = millis();
        _duration = durationMs;
        _active = true;
    }

    void stop() {
        _active = false;
    }

    bool isComplete() {
        if (!_active) return false;
        return (millis() - _startTime) >= _duration;
    }

    uint32_t elapsed() {
        return millis() - _startTime;
    }

    uint32_t remaining() {
        uint32_t e = elapsed();
        return (e >= _duration) ? 0 : (_duration - e);
    }
};
```

### Usage in Loop

```cpp
TimedOperation motorBurst;

void loop() {
    Bluefruit.update();  // Always service BLE first

    if (motorBurst.isComplete()) {
        deactivateMotor();
        motorBurst.stop();
        scheduleNextBurst();
    }
}

void activateMotorForDuration(uint32_t ms) {
    activateMotor();
    motorBurst.start(ms);
}
```

## Multi-Phase Timing

For operations with multiple timed phases (e.g., motor on → wait → next motor).

### Phase State Machine

```cpp
enum class TimingPhase {
    IDLE,
    MOTOR_ACTIVE,
    INTER_BURST_WAIT,
    SESSION_COMPLETE
};

class TherapyEngine {
private:
    TimingPhase _phase;
    uint32_t _phaseStartTime;
    uint32_t _burstDurationMs;
    uint32_t _interBurstIntervalMs;
    uint8_t _currentFinger;

public:
    void update() {
        if (_phase == TimingPhase::IDLE) return;

        uint32_t now = millis();
        uint32_t elapsed = now - _phaseStartTime;

        switch (_phase) {
            case TimingPhase::MOTOR_ACTIVE:
                if (elapsed >= _burstDurationMs) {
                    deactivateMotor(_currentFinger);
                    enterPhase(TimingPhase::INTER_BURST_WAIT);
                }
                break;

            case TimingPhase::INTER_BURST_WAIT:
                if (elapsed >= _interBurstIntervalMs) {
                    advanceToNextFinger();
                    if (_currentFinger < FINGER_COUNT) {
                        activateMotor(_currentFinger);
                        enterPhase(TimingPhase::MOTOR_ACTIVE);
                    } else {
                        enterPhase(TimingPhase::SESSION_COMPLETE);
                    }
                }
                break;
        }
    }

private:
    void enterPhase(TimingPhase phase) {
        _phase = phase;
        _phaseStartTime = millis();
    }
};
```

## Session Timeout Handling

Long-running sessions need timeout monitoring without blocking.

### Session Timer Pattern

```cpp
class SessionManager {
private:
    uint32_t _sessionStartTime;
    uint32_t _sessionDurationSec;
    bool _sessionActive;

public:
    void startSession(uint32_t durationSec) {
        _sessionStartTime = millis();
        _sessionDurationSec = durationSec;
        _sessionActive = true;
    }

    void update() {
        if (!_sessionActive) return;

        uint32_t elapsedSec = (millis() - _sessionStartTime) / 1000;

        if (elapsedSec >= _sessionDurationSec) {
            endSession();
        }
    }

    uint32_t getRemainingSeconds() {
        if (!_sessionActive) return 0;
        uint32_t elapsedSec = (millis() - _sessionStartTime) / 1000;
        return (_sessionDurationSec > elapsedSec) ?
               (_sessionDurationSec - elapsedSec) : 0;
    }

    float getProgressPercent() {
        if (!_sessionActive || _sessionDurationSec == 0) return 0.0f;
        uint32_t elapsedSec = (millis() - _sessionStartTime) / 1000;
        return (float)elapsedSec / (float)_sessionDurationSec * 100.0f;
    }
};
```

## Interval Scheduling

For operations that need to repeat at fixed intervals.

### Repeating Timer Pattern

```cpp
class IntervalTimer {
private:
    uint32_t _lastTrigger;
    uint32_t _intervalMs;
    bool _enabled;

public:
    void start(uint32_t intervalMs) {
        _intervalMs = intervalMs;
        _lastTrigger = millis();
        _enabled = true;
    }

    void stop() {
        _enabled = false;
    }

    bool shouldTrigger() {
        if (!_enabled) return false;

        uint32_t now = millis();
        if (now - _lastTrigger >= _intervalMs) {
            _lastTrigger = now;  // Reset for next interval
            return true;
        }
        return false;
    }

    void adjustInterval(uint32_t newIntervalMs) {
        _intervalMs = newIntervalMs;
    }
};
```

### Usage Example

```cpp
IntervalTimer heartbeatTimer;
IntervalTimer statusUpdateTimer;

void setup() {
    heartbeatTimer.start(1000);      // Every 1 second
    statusUpdateTimer.start(5000);   // Every 5 seconds
}

void loop() {
    Bluefruit.update();

    if (heartbeatTimer.shouldTrigger()) {
        sendHeartbeat();
    }

    if (statusUpdateTimer.shouldTrigger()) {
        sendStatusUpdate();
    }
}
```

## Microsecond Precision

For timing-critical operations requiring sub-millisecond precision.

### micros() for High Resolution

```cpp
class PrecisionTimer {
private:
    uint32_t _startMicros;
    uint32_t _durationMicros;
    bool _active;

public:
    void startMicros(uint32_t durationUs) {
        _startMicros = micros();
        _durationMicros = durationUs;
        _active = true;
    }

    bool isComplete() {
        if (!_active) return false;
        return (micros() - _startMicros) >= _durationMicros;
    }

    uint32_t elapsedMicros() {
        return micros() - _startMicros;
    }
};
```

### Caution with micros()
- `micros()` overflows every ~70 minutes (32-bit at 1MHz)
- Subtraction handles overflow correctly due to unsigned arithmetic
- Don't compare absolute values; always use elapsed time

## Debouncing Pattern

For input handling with timing-based debounce.

```cpp
class DebouncedInput {
private:
    uint32_t _lastChangeTime;
    uint32_t _debounceMs;
    bool _lastState;
    bool _stableState;

public:
    DebouncedInput(uint32_t debounceMs = 50)
        : _debounceMs(debounceMs), _lastState(false), _stableState(false) {}

    bool update(bool currentState) {
        uint32_t now = millis();

        if (currentState != _lastState) {
            _lastChangeTime = now;
            _lastState = currentState;
        }

        if ((now - _lastChangeTime) >= _debounceMs) {
            if (_stableState != _lastState) {
                _stableState = _lastState;
                return true;  // State changed
            }
        }

        return false;  // No change
    }

    bool getState() { return _stableState; }
};
```

## Timeout with Callback

For operations that need to execute code on timeout.

```cpp
typedef void (*TimeoutCallback)();

class TimeoutHandler {
private:
    uint32_t _startTime;
    uint32_t _timeoutMs;
    TimeoutCallback _callback;
    bool _active;
    bool _triggered;

public:
    void start(uint32_t timeoutMs, TimeoutCallback cb) {
        _startTime = millis();
        _timeoutMs = timeoutMs;
        _callback = cb;
        _active = true;
        _triggered = false;
    }

    void cancel() {
        _active = false;
    }

    void update() {
        if (!_active || _triggered) return;

        if ((millis() - _startTime) >= _timeoutMs) {
            _triggered = true;
            _active = false;
            if (_callback) _callback();
        }
    }

    void reset() {
        _startTime = millis();
        _triggered = false;
        _active = true;
    }
};
```

## Coordinated Multi-Device Timing

For synchronizing timing between PRIMARY and SECONDARY devices.

### Sync Adjustment Pattern

```cpp
struct SyncState {
    uint32_t localTime;
    int32_t offsetMs;      // Adjustment from primary
    bool synced;
};

uint32_t getSyncedTime(SyncState& sync) {
    return millis() + sync.offsetMs;
}

void applySyncAdjustment(SyncState& sync, int32_t adjustment) {
    sync.offsetMs += adjustment;
    sync.synced = true;
}

// PRIMARY sends: "SYNC:12345" (its millis())
// SECONDARY calculates offset and adjusts local timing
void handleSyncMessage(const char* msg, SyncState& sync) {
    uint32_t primaryTime;
    if (sscanf(msg, "SYNC:%lu", &primaryTime) == 1) {
        uint32_t localTime = millis();
        sync.offsetMs = (int32_t)primaryTime - (int32_t)localTime;
        sync.synced = true;
    }
}
```

## Common Timing Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| `delay()` in loop | Blocks BLE stack | millis()-based timing |
| Absolute time comparison | Overflow bugs | Always use elapsed time |
| Missing edge cases | Off-by-one timing | Test boundary conditions |
| No timeout on waits | Infinite hangs | Always have max timeout |
| Blocking I/O | Unpredictable delays | Use polling or interrupts |
| Mixed millis/micros | Unit confusion | Consistent time base per operation |
