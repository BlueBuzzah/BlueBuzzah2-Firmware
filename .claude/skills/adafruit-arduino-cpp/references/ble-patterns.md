# BLE Implementation Patterns for nRF52840

Detailed patterns for implementing robust BLE functionality using the Adafruit Bluefruit library.

## Static Dispatcher Pattern

The Bluefruit library requires C-style function pointers for callbacks, not C++ class methods. Use a global instance pointer to bridge this constraint.

### Complete Implementation

```cpp
// ble_manager.h
class BLEManager {
public:
    BLEManager();
    void begin();
    void handleConnect(uint16_t connHandle);
    void handleDisconnect(uint16_t connHandle, uint8_t reason);
    void handleRx(uint16_t connHandle);

private:
    BLEUart _bleuart;
};

// Global instance pointer - set in constructor
extern BLEManager* g_bleManager;

// ble_manager.cpp
BLEManager* g_bleManager = nullptr;

// Static callback functions that bridge to instance methods
static void _onPeriphConnect(uint16_t connHandle) {
    if (g_bleManager) g_bleManager->handleConnect(connHandle);
}

static void _onPeriphDisconnect(uint16_t connHandle, uint8_t reason) {
    if (g_bleManager) g_bleManager->handleDisconnect(connHandle, reason);
}

static void _onUartRx(uint16_t connHandle) {
    if (g_bleManager) g_bleManager->handleRx(connHandle);
}

BLEManager::BLEManager() {
    g_bleManager = this;  // Set global pointer
}

void BLEManager::begin() {
    Bluefruit.begin(1, 1);  // 1 peripheral, 1 central connection
    Bluefruit.setName("MyDevice");

    // Register static callbacks
    Bluefruit.Periph.setConnectCallback(_onPeriphConnect);
    Bluefruit.Periph.setDisconnectCallback(_onPeriphDisconnect);

    _bleuart.begin();
    _bleuart.setRxCallback(_onUartRx);
}
```

### Why This Pattern?
- Bluefruit callbacks are C function pointers, not `std::function` or member pointers
- Global pointer allows static functions to dispatch to instance methods
- Maintains OOP design while meeting library constraints
- Single instance enforced by design (only one BLE stack)

## EOT-Framed Message Protocol

BLE UART has MTU limitations (~20-247 bytes depending on negotiation). Use End-of-Transmission framing to handle message boundaries.

### Message Accumulation Pattern

```cpp
#define EOT_CHAR 0x04
#define RX_BUFFER_SIZE 256

struct Connection {
    uint16_t connHandle;
    char rxBuffer[RX_BUFFER_SIZE];
    uint16_t rxIndex;
    bool pendingIdentify;
    uint32_t identifyStartTime;
};

void BLEManager::handleRx(uint16_t connHandle) {
    Connection* conn = findConnection(connHandle);
    if (!conn) return;

    while (_bleuart.available()) {
        char c = _bleuart.read();

        if (c == EOT_CHAR) {
            // Message complete
            conn->rxBuffer[conn->rxIndex] = '\0';
            processCompleteMessage(conn, conn->rxBuffer);
            conn->rxIndex = 0;
        } else if (conn->rxIndex < RX_BUFFER_SIZE - 1) {
            conn->rxBuffer[conn->rxIndex++] = c;
        }
        // Silently drop overflow bytes
    }
}
```

### Sending with EOT

```cpp
void BLEManager::send(uint16_t connHandle, const char* message) {
    if (!Bluefruit.connected(connHandle)) return;

    _bleuart.write(message);
    _bleuart.write(EOT_CHAR);  // Terminate message
}
```

### Buffer Per Connection
Each connection needs its own receive buffer to prevent interleaving issues:

```cpp
Connection _connections[MAX_CONNECTIONS];

Connection* findConnection(uint16_t handle) {
    for (int i = 0; i < MAX_CONNECTIONS; i++) {
        if (_connections[i].connHandle == handle) {
            return &_connections[i];
        }
    }
    return nullptr;
}
```

## Connection Type Identification

When accepting multiple connection types (phone app, secondary device), use deferred identification with timeout.

### Identification Flow

```cpp
#define IDENTIFY_TIMEOUT_MS 1000

enum class ConnectionType {
    UNKNOWN,
    PHONE,
    SECONDARY_DEVICE
};

void BLEManager::handleConnect(uint16_t connHandle) {
    Connection* conn = allocateConnection(connHandle);
    conn->type = ConnectionType::UNKNOWN;
    conn->pendingIdentify = true;
    conn->identifyStartTime = millis();

    // Wait for IDENTIFY message to determine type
}

void BLEManager::update() {
    uint32_t now = millis();

    for (int i = 0; i < MAX_CONNECTIONS; i++) {
        Connection* conn = &_connections[i];
        if (!conn->pendingIdentify) continue;

        if (now - conn->identifyStartTime >= IDENTIFY_TIMEOUT_MS) {
            // No IDENTIFY received - assume phone
            conn->type = ConnectionType::PHONE;
            conn->pendingIdentify = false;
            onPhoneConnected(conn);
        }
    }
}

void BLEManager::processCompleteMessage(Connection* conn, const char* msg) {
    if (conn->pendingIdentify) {
        if (strncmp(msg, "IDENTIFY:SECONDARY", 18) == 0) {
            conn->type = ConnectionType::SECONDARY_DEVICE;
            conn->pendingIdentify = false;
            onSecondaryConnected(conn);
            return;
        }
    }

    // Route message based on connection type
    switch (conn->type) {
        case ConnectionType::PHONE:
            handlePhoneMessage(conn, msg);
            break;
        case ConnectionType::SECONDARY_DEVICE:
            handleSecondaryMessage(conn, msg);
            break;
    }
}
```

## Scanner Configuration

### Flood Prevention (Critical)

Without service UUID filtering, the scanner callback fires for EVERY BLE device in range. In busy environments (offices, public spaces), this can be 100+ callbacks per second, starving the main loop.

```cpp
void BLEManager::startScanning(const char* targetName) {
    Bluefruit.Scanner.restartOnDisconnect(false);

    // CRITICAL: Filter by UART service UUID
    // Without this, callback fires for EVERY device in range
    Bluefruit.Scanner.clearFilters();
    Bluefruit.Scanner.filterUuid(_clientUart.uuid);

    // Optional: Also filter by name for extra specificity
    if (targetName && strlen(targetName) > 0) {
        Bluefruit.Scanner.filterName(targetName);
    }

    Bluefruit.Scanner.setRxCallback(_onScanResult);
    Bluefruit.Scanner.start(0);  // 0 = scan forever
}
```

### Scanner Health Monitoring

The Bluefruit scanner mysteriously stops sometimes. Implement periodic health checks.

```cpp
#define SCAN_HEALTH_CHECK_INTERVAL 5000

uint32_t _lastScanCheck = 0;
bool _scannerAutoRestartEnabled = true;

void BLEManager::update() {
    uint32_t now = millis();

    // Scanner health check
    if (_scannerAutoRestartEnabled && (now - _lastScanCheck >= SCAN_HEALTH_CHECK_INTERVAL)) {
        _lastScanCheck = now;

        bool shouldBeScanning = (_role == DeviceRole::SECONDARY) &&
                               (getConnectionCount() == 0);

        if (shouldBeScanning && !Bluefruit.Scanner.isRunning()) {
            Serial.println("[BLE] Scanner stopped unexpectedly, restarting...");
            startScanning(_targetName);
        }
    }
}
```

## Multi-Connection Handling

The nRF52840 can maintain multiple simultaneous connections. Configure capacity at startup.

### Connection Capacity

```cpp
void BLEManager::begin() {
    // PRIMARY: 1 peripheral (phone) + 1 central (secondary glove)
    // SECONDARY: 1 central (to primary)

    if (_role == DeviceRole::PRIMARY) {
        Bluefruit.begin(1, 1);  // 1 periph, 1 central
    } else {
        Bluefruit.begin(0, 1);  // 0 periph, 1 central
    }
}
```

### Connection Tracking

```cpp
struct ConnectionInfo {
    uint16_t handle;
    ConnectionType type;
    bool active;
    char rxBuffer[RX_BUFFER_SIZE];
    uint16_t rxIndex;
};

ConnectionInfo _connections[MAX_CONNECTIONS];

uint8_t getConnectionCount() {
    uint8_t count = 0;
    for (int i = 0; i < MAX_CONNECTIONS; i++) {
        if (_connections[i].active) count++;
    }
    return count;
}

ConnectionInfo* getConnectionByType(ConnectionType type) {
    for (int i = 0; i < MAX_CONNECTIONS; i++) {
        if (_connections[i].active && _connections[i].type == type) {
            return &_connections[i];
        }
    }
    return nullptr;
}
```

## Callback Registration Pattern

Allow other modules to register for BLE events without circular dependencies.

```cpp
typedef void (*MessageCallback)(const char* message, uint16_t connHandle);

MessageCallback _phoneMessageCallback = nullptr;
MessageCallback _secondaryMessageCallback = nullptr;

void BLEManager::setPhoneMessageCallback(MessageCallback cb) {
    _phoneMessageCallback = cb;
}

void BLEManager::handlePhoneMessage(Connection* conn, const char* msg) {
    if (_phoneMessageCallback) {
        _phoneMessageCallback(msg, conn->connHandle);
    }
}
```

### Usage in main.cpp

```cpp
void onPhoneCommand(const char* cmd, uint16_t handle) {
    menuController.processCommand(cmd);
}

void setup() {
    bleManager.setPhoneMessageCallback(onPhoneCommand);
    bleManager.begin();
}
```

## Advertising Configuration

### Service Advertisement

```cpp
void BLEManager::startAdvertising() {
    Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
    Bluefruit.Advertising.addTxPower();
    Bluefruit.Advertising.addService(_bleuart);
    Bluefruit.Advertising.addName();

    Bluefruit.Advertising.restartOnDisconnect(true);
    Bluefruit.Advertising.setInterval(32, 244);  // Fast: 20ms, Slow: 152.5ms
    Bluefruit.Advertising.setFastTimeout(30);    // 30s of fast advertising
    Bluefruit.Advertising.start(0);              // 0 = advertise forever
}
```

### Name-Based Pairing
Use consistent naming for device pairing:

```cpp
void BLEManager::setDeviceName(DeviceRole role) {
    char name[32];
    snprintf(name, sizeof(name), "BlueBuzzah-%s",
             role == DeviceRole::PRIMARY ? "P" : "S");
    Bluefruit.setName(name);
}
```

## Common Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| No scanner filter | Main loop starvation, high CPU | Filter by service UUID |
| Missing EOT handling | Partial messages, data corruption | Frame all messages with EOT |
| Single RX buffer | Message interleaving | Buffer per connection |
| No identify timeout | Connection type never resolved | Default to phone after timeout |
| Scanner stops | Secondary can't reconnect | Health check with auto-restart |
