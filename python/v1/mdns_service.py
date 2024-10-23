from zeroconf import Zeroconf, ServiceInfo
import socket

class MDNSService:
    def __init__(self, service_name, service_type, port, ip_address, properties=None):
        """
        初始化 mDNS 服務
        :param service_name: 服務的名稱 (如 "myserver")
        :param service_type: 服務類型 (如 "_rawsocket._tcp.local.")
        :param port: 服務的端口
        :param ip_address: 伺服器的 IP 地址
        :param properties: 服務的屬性描述
        """
        self.zeroconf = Zeroconf()
        self.info = ServiceInfo(
            service_type,
            f"{service_name}.{service_type}",
            addresses=[socket.inet_aton(ip_address)],
            port=port,
            properties=properties or {},
            server=f"{service_name}.local."
        )
        self.service_name = service_name

    def start(self):
        """啟動 mDNS 服務"""
        print(f"Registering service {self.service_name}.local.")
        self.zeroconf.register_service(self.info)

    def stop(self):
        """停止 mDNS 服務"""
        print(f"Unregistering service {self.service_name}.local.")
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
