from typing import List

import docker
from docker.models.containers import Container
from docker.errors import NotFound
from docker.types import IPAMConfig, IPAMPool


class DockerService:
    def __init__(self):
        self.client = docker.from_env()
        self.network_names = []

    def ensure_network(self, name="stub_net", subnet="192.168.100.0/24", gateway="192.168.100.1"):
        self.network_names.append(name)
        try:
            self.client.networks.get(name)
            print(f"Network '{name}' already exists.")
        except NotFound:
            self.client.networks.create(
                name,
                driver="bridge",
                ipam=IPAMConfig(pool_configs=[IPAMPool(subnet=subnet, gateway=gateway)])
            )
            print(f"Network '{name}' created.")

    def build_image(self, dockerfile_path: str, tag: str):
        print(f"Building Docker image from {dockerfile_path} with tag {tag}")
        self.client.images.build(
            path=dockerfile_path,
            tag=tag
        )

    def run_container(self, image_name: str, name: str, env: dict, port_bindings: dict,
                      network_name: str = "stub_net", container_ip: str = None, detach: bool = True) -> Container:
        """
        Run a Docker container with specified port bindings and optional static IP.

        :param image_name: Docker image name
        :param name: Container name
        :param env: Environment variables
        :param port_bindings: {"5060/udp": 5060, "8080/tcp": 8080} style
        :param network_name: Docker bridge network name
        :param container_ip: Static IP to assign to container in the network
        :param detach: Run container in background
        """
        container = self.client.containers.create(
            image=image_name,
            name=name,
            environment=env,
            # ports=port_bindings,
            detach=True
        )

        network = self.client.networks.get(network_name)

        # Avoid reconnecting the same container to the same network
        connected_container_ids = [c['Name'] for c in network.attrs['Containers'].values()]
        if name not in connected_container_ids:
            network.connect(container, ipv4_address=container_ip)

        container.start()
        return container

    def stop_container(self, name: str):
        print(f"Stopping container {name}")
        container = self.client.containers.get(name)
        container.stop()

    def remove_container(self, name: str):
        print(f"Removing container {name}")
        container = self.client.containers.get(name)
        container.remove(force=True)

    def get_container_status(self, name: str) -> str:
        container = self.client.containers.get(name)
        return container.status

    def list_containers(self, all_containers: bool = False):
        return self.client.containers.list(all=all_containers)

    def cleanup_containers(self, name_prefix="stub_"):
        for container in self.client.containers.list(all=True):
            if container.name.startswith(name_prefix):
                container.remove(force=True)

    def remove_image(self, image_name: str):
        try:
            print(f"Removing image: {image_name}")
            self.client.images.remove(image=image_name, force=True)
        except docker.errors.ImageNotFound:
            pass
        except Exception as e:
            print(f"Error removing image {image_name}: {e}")

    def remove_dangling_images(self):
        try:
            dangling_images = self.client.images.list(filters={"dangling": True})
            for image in dangling_images:
                print(f"Removing dangling image: {image.id}")
                self.client.images.remove(image.id, force=True)
        except Exception as e:
            print(f"Error removing dangling images: {e}")

    def full_cleanup(self):
        # 1. Stop and remove all containers (created via this service)
        image_tags = []
        containers = self.list_containers(all_containers=True)

        for container in containers:
            try:
                image_tags.append(f"{container.name.replace('-', '').lower()}_image")
                print(f"Stopping container: {container.name}")
                container.stop()
                print(f"Removing container: {container.name}")
                container.remove(force=True)
            except Exception as e:
                print(f"Error stopping/removing container {container.name}: {e}")

        # 2. Remove custom networks (you can pass their names or filter by prefix)
        for network in self.client.networks.list():
            try:
                if network.name in self.network_names:
                    print(f"Removing network: {network.name}")
                    network.remove()
            except Exception as e:
                print(f"Error removing network {network.name}: {e}")

        # 3. Remove known images
        if image_tags:
            for tag in image_tags:
                try:
                    print(f"Removing image: {tag}")
                    self.client.images.remove(tag, force=True)
                except Exception:
                    pass

        # 4. Remove dangling images
        try:
            dangling_images = self.client.images.list(filters={"dangling": True})
            for image in dangling_images:
                print(f"Removing dangling image: {image.id}")
                self.client.images.remove(image.id, force=True)
        except Exception as e:
            print(f"Error removing dangling images: {e}")

        # 5. Optional: remove dangling volumes
        try:
            volumes = self.client.volumes.list(filters={"dangling": True})
            for volume in volumes:
                print(f"Removing volume: {volume.name}")
                volume.remove(force=True)
        except Exception as e:
            print(f"Error removing volumes: {e}")
