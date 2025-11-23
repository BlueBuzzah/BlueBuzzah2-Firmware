"""
BLE - Minimal Working Implementation
"""

import time

try:
    from adafruit_ble import BLERadio
    from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
    from adafruit_ble.advertising import Advertisement, LazyObjectField
    from adafruit_ble.services.nordic import UARTService
    import _bleio
except ImportError:
    BLERadio = None
    ProvideServicesAdvertisement = None
    Advertisement = None
    LazyObjectField = None
    UARTService = None
    _bleio = None


class BLEConnection:
    def __init__(self, name, ble_connection, uart_service):
        self.name = name
        self.ble_connection = ble_connection
        self.uart = uart_service
        self.connected_at = time.monotonic()
        self.last_seen = time.monotonic()

    def update_last_seen(self):
        self.last_seen = time.monotonic()

    def is_connected(self):
        try:
            return self.ble_connection.connected
        except:
            return False


class BLE:
    def __init__(self):
        if BLERadio is None:
            raise RuntimeError("BLE libraries not available")

        print("[BLE] Initializing BLE radio...")

        # Set default adapter name before creating BLERadio
        if _bleio:
            try:
                _bleio.adapter.name = "BlueBuzzah"
                print("[BLE] Set default adapter name to: BlueBuzzah")
            except Exception as e:
                print("[BLE] WARNING: Could not set default adapter name: {}".format(e))

        self.ble = BLERadio()
        self.uart_service = UARTService()
        self.advertisement = ProvideServicesAdvertisement(self.uart_service)
        self._connections = {}
        print("[BLE] BLE radio initialized")

        # Format MAC address
        mac_parts = []
        for b in self.ble.address_bytes:
            mac_parts.append("{:02x}".format(b))
        mac_addr = ":".join(mac_parts)
        print("[BLE] MAC address: {}".format(mac_addr))

    def advertise(self, name):
        print("[BLE] Setting name to '{}'".format(name))

        # Stop any existing advertising
        try:
            self.ble.stop_advertising()
        except:
            pass

        # CRITICAL: Set the adapter name BEFORE creating anything else
        # This affects the default advertising name
        if _bleio:
            try:
                _bleio.adapter.name = name
                print("[BLE] Set adapter name to: {}".format(_bleio.adapter.name))
            except Exception as e:
                print("[BLE] WARNING: Could not set adapter name: {}".format(e))

        # Now create BLE radio with the name already set
        self.ble = BLERadio()
        self.ble.name = name

        # Create UART service
        self.uart_service = UARTService()

        # Create advertisement with the service
        self.advertisement = ProvideServicesAdvertisement(self.uart_service)

        # CRITICAL: Manually inject the complete_name into the advertisement data buffer
        # The Advertisement class stores data in an internal buffer that gets transmitted
        try:
            # Build the complete_name field: Type (0x09) + Length + Name bytes
            name_bytes = name.encode('utf-8')
            name_len = len(name_bytes) + 1  # +1 for the type byte
            complete_name_field = bytes([name_len, 0x09]) + name_bytes

            # Append to the advertisement's internal data buffer
            if hasattr(self.advertisement, '_data'):
                # Get current data and append complete_name field
                current_data = bytes(self.advertisement._data)
                self.advertisement._data = bytearray(current_data + complete_name_field)
                print("[BLE] Injected complete_name '{}' into advertisement data".format(name))
            else:
                print("[BLE] WARNING: Cannot access advertisement _data buffer")
        except Exception as e:
            print("[BLE] WARNING: Could not inject advertisement complete_name: {}".format(e))

        print("[BLE] Starting advertising...")
        self.ble.start_advertising(self.advertisement)
        time.sleep(0.5)

        print("[BLE] *** ADVERTISING STARTED ***")
        print("[BLE] Radio name: {}".format(self.ble.name))
        try:
            print("[BLE] Advertisement name: {}".format(self.advertisement.complete_name))
        except:
            print("[BLE] Advertisement name: (unable to read)")
        print("[BLE] Radio advertising: {}".format(self.ble.advertising))
        print("[BLE] Look for '{}' in your BLE scanner NOW".format(name))

    def stop_advertising(self):
        if self.ble.advertising:
            self.ble.stop_advertising()
            print("[BLE] Stopped advertising")

    def set_identity_name(self, name):
        """
        Set BLE adapter identity name without advertising.

        This is used for SECONDARY devices that need to identify themselves
        but don't advertise (only scan and connect).

        Args:
            name: BLE identity name (e.g., "BlueBuzzah-Secondary")
        """
        print("[BLE] Setting identity name to '{}'".format(name))

        if _bleio:
            try:
                _bleio.adapter.name = name
                print("[BLE] Set adapter identity name to: {}".format(_bleio.adapter.name))
            except Exception as e:
                print("[BLE] WARNING: Could not set adapter identity name: {}".format(e))

        try:
            self.ble.name = name
            print("[BLE] Set radio identity name to: {}".format(self.ble.name))
        except Exception as e:
            print("[BLE] WARNING: Could not set radio identity name: {}".format(e))

    def wait_for_connection(self, conn_id, timeout=None):
        # If already connected, return immediately
        if conn_id in self._connections:
            return conn_id

        # Print waiting message only once
        if not hasattr(self, '_waiting_for'):
            self._waiting_for = set()

        if conn_id not in self._waiting_for:
            print(f"[BLE] Waiting for '{conn_id}'...")
            self._waiting_for.add(conn_id)

        start_time = time.monotonic()
        existing = set(c.ble_connection for c in self._connections.values())

        while True:
            if timeout and (time.monotonic() - start_time > timeout):
                return None

            # Check for NEW connections
            if self.ble.connected:
                for conn in self.ble.connections:
                    if conn not in existing:
                        ble_conn = BLEConnection(conn_id, conn, self.uart_service)
                        self._connections[conn_id] = ble_conn
                        self._waiting_for.discard(conn_id)
                        print(f"[BLE] *** {conn_id} CONNECTED *** (total: {len(self.ble.connections)})")
                        return conn_id

            time.sleep(0.01)

    def scan_and_connect(self, target, timeout=30.0, conn_id="primary"):
        start_time = time.monotonic()
        print(f"[BLE] Scanning for '{target}' (unfiltered)...")

        try:
            while time.monotonic() - start_time < timeout:
                # UNFILTERED scan - finds all BLE devices
                # This is necessary because injecting the name into PRIMARY's advertisement
                # breaks the ProvideServicesAdvertisement filter
                for advertisement in self.ble.start_scan(timeout=5.0):
                    # Check if name matches
                    if advertisement.complete_name == target:
                        print(f"[BLE] Found '{target}', connecting...")
                        self.ble.stop_scan()

                        try:
                            # Attempt connection and get UARTService
                            connection = self.ble.connect(advertisement)
                            uart = connection[UARTService]
                            ble_conn = BLEConnection(conn_id, connection, uart)
                            self._connections[conn_id] = ble_conn
                            print(f"[BLE] Connected to '{target}'")
                            return conn_id
                        except KeyError:
                            print(f"[BLE] WARNING: '{target}' found but no UARTService available")
                            return None
                        except Exception as e:
                            print(f"[BLE] Connection failed: {e}")
                            return None

                time.sleep(0.1)

            print(f"[BLE] Scan timeout")
            return None
        finally:
            try:
                self.ble.stop_scan()
            except:
                pass

    def send(self, conn_id, message):
        """
        Send message with EOT terminator.

        Appends 0x04 (EOT) to mark end of message for reliable framing.
        """
        if conn_id not in self._connections:
            return False

        conn = self._connections[conn_id]
        if not conn.is_connected():
            return False

        try:
            # Append EOT (0x04) terminator
            message_with_eot = message + '\x04'
            conn.uart.write(message_with_eot.encode('utf-8'))
            conn.update_last_seen()
            return True
        except:
            return False

    def receive(self, conn_id, timeout=None):
        """
        Receive message with EOT framing.

        Buffers incoming bytes until EOT (0x04) is received, then returns
        complete message without the EOT terminator.

        Returns:
            Complete message (str) without EOT, or None if timeout/error
        """
        if conn_id not in self._connections:
            return None

        conn = self._connections[conn_id]
        if not conn.is_connected():
            return None

        try:
            start_time = time.monotonic()
            buffer = ""

            while True:
                if timeout and (time.monotonic() - start_time > timeout):
                    return None  # Timeout - incomplete message

                if conn.uart.in_waiting > 0:
                    data = conn.uart.read()
                    if data:
                        chunk = data.decode('utf-8')
                        buffer += chunk

                        # Check for EOT terminator
                        if '\x04' in buffer:
                            # Extract message up to EOT
                            eot_index = buffer.index('\x04')
                            message = buffer[:eot_index]
                            conn.update_last_seen()
                            return message  # Return message without EOT

                time.sleep(0.01)
        except Exception as e:
            # Log decode errors if DEBUG enabled
            if hasattr(self, 'debug') and self.debug:
                print(f"[BLE] Receive error: {e}")
            return None

    def disconnect(self, conn_id):
        if conn_id in self._connections:
            try:
                self._connections[conn_id].ble_connection.disconnect()
            except:
                pass
            del self._connections[conn_id]

    def is_connected(self, conn_id):
        if conn_id not in self._connections:
            return False
        return self._connections[conn_id].is_connected()

    def get_all_connections(self):
        return list(self._connections.keys())

    def disconnect_all(self):
        for conn_id in list(self._connections.keys()):
            self.disconnect(conn_id)
