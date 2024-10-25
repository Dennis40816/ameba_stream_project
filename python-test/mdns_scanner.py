from zeroconf import Zeroconf, ServiceBrowser, ServiceListener

class MyListener(ServiceListener):
    def add_service(self, zeroconf, service_type, name):
        print(f"Service {name} added, type: {service_type}")

    def update_service(self, zeroconf, service_type, name):
        print(f"Service {name} updated, type: {service_type}")

    def remove_service(self, zeroconf, service_type, name):
        print(f"Service {name} removed, type: {service_type}")

# 創建 Zeroconf 實例
zeroconf = Zeroconf()
listener = MyListener()

# 瀏覽指定的 raw socket 服務
browser = ServiceBrowser(zeroconf, "_rawsocket._tcp.local.", listener)

try:
    input("Press enter to exit...\n")
finally:
    zeroconf.close()
