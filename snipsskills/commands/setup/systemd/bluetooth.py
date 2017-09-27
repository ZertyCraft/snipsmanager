# -*-: coding utf-8 -*-
"""The microphone setup command."""

import time

from ...base import Base
from ....utils.os_helpers import is_raspi_os, is_node_available, which
from ....utils.systemd import Systemd

from snipsskills import NODE_MODULES_PATH

from snipsskillscore import pretty_printer as pp

class SystemdBluetoothException(Exception):
    pass


class SystemdBluetooth(Base):

    SNIPSBLE_SERVICE_NAME = "snipsble"
    SNIPSBLE_SERVICE_UUID = "13EA4259-9D9E-42D1-A78B-638ED22CC768"
    SNIPSBLE_CHARACTERISTIC_UUID = "81D97A06-7A2D-4A98-A2E2-41688E3D8283"
    SNIPSBLE_MODULE_NAME = "snips-mqtt-relay"
    SNIPSBLE_SCRIPT = "{node_bin_path} {node_module_path}/{module_name}/index.js --serviceUUID={serviceUUID} --characteristicUUID={characteristicUUID} {mqtt_hostname} {mqtt_port}"

    def run(self):
        mqtt_host = self.options['--mqtt_host']
        mqtt_port = self.options['--mqtt_port']

        try:
            SystemdBluetooth.setup(mqtt_host, mqtt_port)
        except Exception as e:
            pp.perror(str(e))

    @staticmethod
    def setup(mqtt_hostname="localhost", mqtt_port=9898):
        if not is_raspi_os():
            raise SystemdBluetoothException("Bluetooth systemd configuration is only available on Raspberry Pi. Skipping systemd setup.")

        if not is_node_available():
            raise SystemdBluetoothException("Error: Bluetooth module must be installed. Run 'snipsskills install bluetooth' to setup Bluetooth.")

        contents = Systemd.get_template(SystemdBluetooth.SNIPSBLE_SERVICE_NAME)
        if contents is None:
            return

        node_bin_path = which('node')            
        command = SystemdBluetooth.SNIPSBLE_SCRIPT.format(
                node_bin_path=node_bin_path,
                node_module_path=NODE_MODULES_PATH,
                module_name=SystemdBluetooth.SNIPSBLE_MODULE_NAME,
                serviceUUID=SystemdBluetooth.SNIPSBLE_SERVICE_UUID,
                characteristicUUID=SystemdBluetooth.SNIPSBLE_CHARACTERISTIC_UUID,
                mqtt_hostname=mqtt_hostname,
                mqtt_port=mqtt_port
            )

        contents = contents.replace("{{SNIPSBLE_COMMAND}}", command)
        Systemd.write_systemd_file(SystemdBluetooth.SNIPSBLE_SERVICE_NAME, None, contents)
        Systemd.enable_service(None, SystemdBluetooth.SNIPSBLE_SERVICE_NAME)

        pp.psuccess("Successfully set up Bluetooth as a Systemd service.")
