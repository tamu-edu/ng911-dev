import ipaddress
import os
import platform
import stat
import threading
import time
import warnings

import psutil
import pyshark
import subprocess


class MonitoringService:
    def __init__(self,  local_host_ip, interface=None, remote_host=None, remote_port=22, remote_user=None, remote_password=None,
                 ssl_keys_file_path: str | None = None):
        self.local_host_ip = local_host_ip
        self.interface = interface or self._set_default_interface()
        if self.interface == "local":
            self.interface = self._find_interface_for_local_mon()
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.remote_user = remote_user
        self.remote_password = remote_password
        self.ssl_keys_file_path = ssl_keys_file_path
        self.capture = None
        self._capture_thread = None
        self.capture_files = []
        self.tshark_process = None

    @staticmethod
    def _set_default_interface():
        system = platform.system()
        if system == 'Windows':
            return 'Ethernet0'
        elif system == 'Darwin':
            return 'en0'
        else:
            return 'eth0'

    def set_sslkeylogfile(self, ssl_keys_file_path):
        self.ssl_keys_file_path = ssl_keys_file_path
        print(f"SSL key log file set to: {self.ssl_keys_file_path}")

    import pyshark
    import warnings

    def start_local_monitoring(self, interface=None, capture_filter=None, display_filter=None, output_file_path=None,
                               timeout=120):
        interface = interface or self.interface
        custom_params = []

        if self.ssl_keys_file_path:
            custom_params = ['-o', f'tls.keylog_file:{self.ssl_keys_file_path}']

        print(f"Starting capture on interface: {interface}")

        if output_file_path:
            output_dir = os.path.dirname(output_file_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

        self.capture = pyshark.LiveCapture(
            interface=self.interface,
            bpf_filter=capture_filter,
            display_filter=display_filter,
            custom_parameters=custom_params,
            output_file=output_file_path, debug=True
        )

        print(f"🟢 Starting async capture on: {self.interface}, file: {output_file_path}")

        # Start capture in a separate thread
        def sniff_packets():
            self.capture.sniff(timeout=timeout)
            print(f"✅ Capture completed and saved to {output_file_path}")

        self._capture_thread = threading.Thread(target=sniff_packets, daemon=True)
        self._capture_thread.start()

    def start_direct_tshark_capture(self, output_file_path: str, capture_filter: str = None, interface: str = None):
        interface = interface or self.interface

        print(f"🚀 Starting direct tshark capture on interface: {interface}, saving to: {output_file_path}")

        cmd = [
            "tshark",
            "-i", interface,
            "-w", output_file_path,
            "-q"  # Quiet mode (no console output)
        ]

        if capture_filter:
            cmd += ["-f", capture_filter]

        self.tshark_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Tshark capture started with PID: {self.tshark_process.pid}")

    def stop_direct_tshark_capture(self):
        if hasattr(self, 'tshark_process') and self.tshark_process:
            print(f"🛑 Stopping tshark process (PID {self.tshark_process.pid})...")
            self.tshark_process.terminate()
            try:
                self.tshark_process.wait(timeout=5)
                print("✅ Tshark process stopped cleanly.")
            except subprocess.TimeoutExpired:
                print("⚠️ Tshark did not stop in time, killing it...")
                self.tshark_process.kill()

    def start_multi_interface_monitoring(self, interfaces: list, capture_filter=None, timeout=60, output_dir="captures"):
        os.makedirs(output_dir, exist_ok=True)
        for iface in interfaces:
            output_path = os.path.join(output_dir, f"{iface}.pcap")
            self.start_local_monitoring(interface=iface, capture_filter=capture_filter, output_file_path=output_path, timeout=timeout)

    def concatenate_captures(self, merged_output_path="merged_capture.pcap"):
        if not self.capture_files:
            print("No captures available for merging.")
            return None

        print(f"Merging captures into {merged_output_path}")
        subprocess.run(["mergecap", "-w", merged_output_path, *self.capture_files], check=True)
        print("Merge completed.")
        return merged_output_path

    def start_remote_monitoring(self, remote_interface='eth0', capture_filter=None, display_filter=None,
                                output_file_path=None, timeout=60):
        if not self.remote_host or not self.remote_user or not self.remote_password:
            print("Remote monitoring configuration is incomplete.")
            return

        custom_params = []
        if self.ssl_keys_file_path:
            custom_params = ['-o', f'tls.keylog_file:{self.ssl_keys_file_path}']

        capture = pyshark.RemoteCapture(
            remote_host=self.remote_host,
            remote_interface=remote_interface,
            ssh_username=self.remote_user,
            ssh_password=self.remote_password,
            bpf_filter=capture_filter,
            display_filter=display_filter,
            custom_parameters=custom_params
        )

        if output_file_path:
            print(f"Capturing remotely to {output_file_path}")
            capture.sniff(timeout=timeout, output_file=output_file_path)
            self.capture_files.append(output_file_path)
        else:
            print(f"Starting remote monitoring on {self.remote_host}:{remote_interface}")
            capture.sniff(timeout=timeout)
        return capture

    def stop_monitoring(self):
        print(self.capture)
        if not self.capture:
            print("⚠️ No capture to stop.")
            return

        print("🛑 Stopping capture...")

        try:
            if self._capture_thread and self._capture_thread.is_alive():
                print("⌛ Waiting for capture thread to finish...")
                self._capture_thread.join(timeout=10)
                if self._capture_thread.is_alive():
                    print("⚠️ Warning: Capture thread still alive after timeout.")
                else:
                    print("✅ Capture thread joined and stopped.")
            else:
                print("ℹ️ Capture thread already not active.")
        except Exception as e:
            print(f"⚠️ Error while stopping capture thread: {e}")

    def close_capture(self):
        if self.capture:
            try:
                self.capture.close()  # ❌ This causes RuntimeError in running loops
                print("LiveCapture closed.")
            except Exception as e:
                print(f"[Warning] Could not close live capture: {e}")

    def switch_to_file_capture(self, output_file_path: str) -> None:
        print("🟡 Switching to FileCapture")

        def load_file_capture():
            self.capture = pyshark.FileCapture(input_file=output_file_path)

        thread = threading.Thread(target=load_file_capture)
        thread.start()
        thread.join()
        print(f"✅ Switched to FileCapture {self.capture}")

    def _find_interface_for_local_mon(self):
        """
        Checks "ip" config from the lab_config
        and looks for interface name matching its value
        :return: Name of network interface or None if not found
        """
        target_ip = ipaddress.IPv4Address(self.local_host_ip)

        for iface_name, iface_addresses in psutil.net_if_addrs().items():
            for addr in iface_addresses:
                if addr.family.name == 'AF_INET':
                    try:
                        iface_net = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
                        if target_ip in iface_net:
                            return iface_name
                    except Exception:
                        continue
        return None

    def get_capture(self):
        return self.capture
