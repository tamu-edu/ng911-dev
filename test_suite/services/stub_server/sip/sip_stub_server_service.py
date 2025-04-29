import subprocess



class SIPServerService:
    def __init__(self, ip: str, port: int, role: str, scenario_file: str = None, target_uri: str = None):
        self.ip = ip
        self.port = port
        self.role = role
        self.scenario_file = scenario_file
        self.target_uri = target_uri
        self.process = None

    def start_server(self):
        if self.role.upper() == "RECEIVER":
            self.process = subprocess.Popen([
                "sipp", "-i", self.ip,
                "-t", "t1",  # TODO - make transport configurable
                "-p", str(self.port),
                "-m", "0",  # just one call to keep it simple
                "-d", "10000",
                str(self.target_uri).replace("sip:", "")
                # "-bg"
            ])
        elif self.role.upper() == "SENDER":
            if not self.scenario_file or not self.target_uri:
                raise ValueError("Sender role requires scenario_file and target_uri.")
            ip, port = self._parse_target_uri()
            self.process = subprocess.Popen([
                "sipp", "-sf", self.scenario_file,
                "-t", "t1",  # TODO - make transport configurable
                ip, "-s", "",  # no specific user
                "-i", self.ip,
                "-p", str(self.port),
                "-m", "1",
                # "-bg"
            ])
        elif self.role.upper() == "IUT":
            self.process = subprocess.Popen([
                "-i", self.ip,
                "-p", str(self.port),
                "-m", "0",
                "-d", "10000",
                # "-bg"
            ])
        else:
            raise ValueError(f"Unsupported role: {self.role.upper()}")

        print(f"[SIPServerService] {self.role.upper()} started on {self.ip}:{self.port}")

    def stop_server(self):
        if self.process:
            self.process.terminate()
            print(f"[SIPServerService] {self.role} stopped.")
            self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def _parse_target_uri(self):
        try:
            uri_parts = self.target_uri.split(":")
            return uri_parts[1], int(uri_parts[2])
        except (IndexError, ValueError):
            raise ValueError("target_uri must be in 'sip:<ip>:<port>' format")