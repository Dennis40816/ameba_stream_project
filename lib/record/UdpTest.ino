// #include <WiFi.h>          // Arduino 的 WiFi 庫
// #include <WiFiUdp.h>       // Arduino 的 UDP 庫
// #include <lwip/sockets.h>  // lwIP 的 sockets API
// #include <lwip/ip_addr.h>
// #include <lwip/igmp.h>

// char* ssid = "CHT061975";
// char* password = "24577079";

// #define MDNS_GROUP "224.0.0.251"  // mDNS 多播組地址
// #define MDNS_PORT 5353            // mDNS 使用的端口

// int udp_socket;

// void setup() {
//   Serial.begin(115200);

//   // 連接到 WiFi
//   WiFi.begin(ssid, password);
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }
//   Serial.println("Connected to WiFi");

//   // 創建 UDP socket
//   udp_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
//   if (udp_socket < 0) {
//     Serial.println("Failed to create socket");
//     return;
//   }

//   // 綁定 socket 到指定的端口和接口
//   struct sockaddr_in localAddr;
//   memset(&localAddr, 0, sizeof(localAddr));
//   localAddr.sin_family = AF_INET;
//   localAddr.sin_addr.s_addr = htonl(INADDR_ANY);  // 綁定到所有接口
//   localAddr.sin_port = htons(MDNS_PORT);

//   if (bind(udp_socket, (struct sockaddr*)&localAddr, sizeof(localAddr)) < 0)
//   {
//     Serial.println("Failed to bind socket");
//     close(udp_socket);
//     return;
//   }

//   // 設置多播組
//   struct ip_mreq mreq;
//   mreq.imr_multiaddr.s_addr = inet_addr(MDNS_GROUP);  // 多播地址
//   mreq.imr_interface.s_addr = htonl(INADDR_ANY);      // 本地接口

//   if (setsockopt(udp_socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq,
//                  sizeof(mreq)) < 0) {
//     Serial.println("Failed to join multicast group");
//     close(udp_socket);
//     return;
//   }

//   Serial.println("Joined multicast group, ready to receive mDNS packets.");
// }

// void loop() {
//   char buffer[512];
//   struct sockaddr_in sourceAddr;
//   socklen_t sourceAddrLen = sizeof(sourceAddr);

//   // 接收來自多播組的數據
//   int bytesReceived = recvfrom(udp_socket, buffer, sizeof(buffer), 0,
//                                (struct sockaddr*)&sourceAddr,
//                                &sourceAddrLen);
//   if (bytesReceived > 0) {
//     char buffer[100];  // Define a buffer for formatted output

//     snprintf(buffer, sizeof(buffer), "Received %d bytes from %s:%d\n",
//              bytesReceived, inet_ntoa(sourceAddr.sin_addr),
//              ntohs(sourceAddr.sin_port));

//     Serial.print(buffer);          // Output the formatted string
//     buffer[bytesReceived] = '\0';  // Null terminate for printing
//     Serial.println("Data received:");
//     Serial.println(buffer);
//   }

//   delay(100);  // 延遲以避免過於頻繁的接收
// }

////////////////////////////////////////////////////////////////////////////////

// #include <WiFi.h>
// #include <WiFiUdp.h>

// WiFiUDP udp;
// char* ssid = "CHT061975";
// char* password = "24577079";
// IPAddress multicastIP(224, 0, 0, 251);  // mDNS 的多播地址
// const int MDNS_PORT = 5353;

// void sendMulticastQuery() {
//     // 建立 mDNS 多播查詢封包，查詢 ic-ameba.local 的 A 記錄，並請求單播回應
//     // uint8_t mdns_query[] = {
//     //     0x00, 0x00,                                      // Transaction ID
//     //     0x00, 0x00,                                      // Flags
//     //     0x00, 0x01,                                      // Questions: 1
//     //     0x00, 0x00,                                      // Answer RRs
//     //     0x00, 0x00,                                      // Authority RRs
//     //     0x00, 0x00,                                      // Additional RRs
//     //     0x08, 'i', 'c', '-', 'a', 'm', 'e', 'b', 'a',    // Hostname:
//     ic-ameba
//     //     0x05, 'l', 'o', 'c', 'a', 'l', 0x00,             // Domain: local
//     //     0x00, 0x01,                                      // Type A (Host
//     Address)
//     //     0x80, 0x01                                       // Class IN, with
//     the unicast-response bit set
//     // };

//     uint8_t mdns_query[] = {
//         0x00, 0x00,  // Transaction ID
//         0x00, 0x00,  // Flags
//         0x00, 0x01,  // Questions: 1
//         0x00, 0x00,  // Answer RRs
//         0x00, 0x00,  // Authority RRs
//         0x00, 0x00,  // Additional RRs
//         0x0A, '_', 'r', 'a', 'w', 's', 'o', 'c', 'k', 'e', 't',  // Service
//         name: _rawsocket 0x04, '_', 't', 'c', 'p', // Protocol: _tcp 0x05,
//         'l', 'o', 'c', 'a', 'l', 0x00,                     // Domain: local
//         0x00, 0x0C,  // Type PTR (to find all instances of the service)
//         0x00, 0x01   // Class IN
//     };

//     udp.beginPacket(multicastIP, MDNS_PORT);  // 發送到多播地址
//     udp.write(mdns_query, sizeof(mdns_query));
//     udp.endPacket();

//     Serial.println("Sent Multicast Query for ic-ameba.local requesting
//     Unicast Response");
// }

// void setup() {
//     Serial.begin(115200);
//     WiFi.begin(ssid, password);
//     while (WiFi.status() != WL_CONNECTED) {
//         delay(500);
//         Serial.print(".");
//     }
//     Serial.println("Connected to WiFi");

//     udp.begin(MDNS_PORT);  // 綁定本地端口
//     sendMulticastQuery();  // 發送多播查詢
// }

// void loop() {
//     int packetSize = udp.parsePacket();
//     if (packetSize) {
//         uint8_t buffer[512];
//         udp.read(buffer, packetSize);

//         // 使用 sprintf 格式化輸出
//         char output[1024];
//         char* ptr = output;
//         int offset = 0;

//         sprintf(ptr, "Received response:\n");
//         ptr += strlen(ptr);

//         for (int i = 0; i < packetSize; i++) {
//             offset += sprintf(ptr + offset, "%02X ", buffer[i]);
//             if ((i + 1) % 16 == 0) {
//                 offset += sprintf(ptr + offset, "\n");  // 每 16 字節換行
//             }
//         }
//         Serial.println(output);
//     }
//     delay(1000);  // 每秒查詢一次
// }

////////////////////////////////////////////////////////////////////////////////
// #include <WiFi.h>
// #include <lwip/sockets.h>
// #include <lwip/ip_addr.h>
// #include <lwip/igmp.h>
// #include <cerrno>

// char* ssid = "CHT061975";
// char* password = "24577079";

// #define MDNS_GROUP "224.0.0.251"  // mDNS 多播組地址
// #define MDNS_PORT 5353            // mDNS 使用的端口

// int udp_socket;
// unsigned long lastQueryTime = 0;  // 上次發送查詢的時間
// const unsigned long queryInterval = 5000;  // 查詢間隔時間（毫秒）
// char buffer[1024];
// char output[1024];

// void sendMulticastQuery() {
//   // This is OK
//     uint8_t mdns_query[] = {
//         0x00, 0x00,  // Transaction ID
//         0x00, 0x00,  // Flags
//         0x00, 0x01,  // Questions: 1
//         0x00, 0x00,  // Answer RRs
//         0x00, 0x00,  // Authority RRs
//         0x00, 0x00,  // Additional RRs
//         0x0A, '_', 'r', 'a', 'w', 's', 'o', 'c', 'k', 'e', 't',  // Service
//         name: _rawsocket 0x04, '_', 't', 'c', 'p', // Protocol: _tcp 0x05,
//         'l', 'o', 'c', 'a', 'l', 0x00,                     // Domain: local
//         0x00, 0x0C,  // Type PTR (to find all instances of the service)
//         0x00, 0x01   // Class IN
//     };

//     struct sockaddr_in destAddr;
//     memset(&destAddr, 0, sizeof(destAddr));
//     destAddr.sin_family = AF_INET;
//     destAddr.sin_port = htons(MDNS_PORT);
//     destAddr.sin_addr.s_addr = inet_addr(MDNS_GROUP);

//     sendto(udp_socket, mdns_query, sizeof(mdns_query), 0, (struct
//     sockaddr*)&destAddr, sizeof(destAddr));

//     Serial.println("Sent Multicast Query for _rawsocket._tcp.local requesting
//     Unicast Response");
// }

// void setup() {
//     Serial.begin(115200);

//     WiFi.begin(ssid, password);
//     while (WiFi.status() != WL_CONNECTED) {
//         delay(500);
//         Serial.print(".");
//     }
//     Serial.println("\nConnected to WiFi");

//     udp_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
//     if (udp_socket < 0) {
//         Serial.println("Failed to create socket");
//         return;
//     }

//     struct sockaddr_in localAddr;
//     memset(&localAddr, 0, sizeof(localAddr));
//     localAddr.sin_family = AF_INET;
//     localAddr.sin_addr.s_addr = htonl(INADDR_ANY);
//     localAddr.sin_port = htons(MDNS_PORT);

//     if (bind(udp_socket, (struct sockaddr*)&localAddr, sizeof(localAddr)) <
//     0) {
//         Serial.println("Failed to bind socket");
//         close(udp_socket);
//         return;
//     }

//     struct ip_mreq mreq;
//     mreq.imr_multiaddr.s_addr = inet_addr(MDNS_GROUP);
//     mreq.imr_interface.s_addr = htonl(INADDR_ANY);

//     if (setsockopt(udp_socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq,
//     sizeof(mreq)) < 0) {
//         Serial.println("Failed to join multicast group");
//         close(udp_socket);
//         return;
//     }

//     Serial.println("Joined multicast group, ready to receive mDNS packets.");
//     // sendMulticastQuery();  // 首次發送多播查詢
//     lastQueryTime = millis();  // 記錄發送時間
// }

// void loop() {
//     int bytesReceived = 0;

//     struct sockaddr_in sourceAddr;
//     socklen_t sourceAddrLen = sizeof(sourceAddr);

//     bytesReceived = recvfrom(udp_socket, buffer, sizeof(buffer), 0, (struct
//     sockaddr*)&sourceAddr, &sourceAddrLen);

//     if (bytesReceived > 0) {

//         char* ptr = output;
//         int offset = 0;

//         offset += sprintf(ptr + offset, "Received %d bytes from %s:%d\n",
//         bytesReceived, inet_ntoa(sourceAddr.sin_addr),
//         ntohs(sourceAddr.sin_port));

//         for (int i = 0; i < bytesReceived; i++) {
//             offset += sprintf(ptr + offset, "%02X ", (uint8_t)buffer[i]);
//             if ((i + 1) % 16 == 0) {
//                 offset += sprintf(ptr + offset, "\n");
//             }
//         }
//         Serial.println(output);
//     }
//         // 定期發送多播查詢
//     if (millis() - lastQueryTime >= queryInterval) {
//         // sendMulticastQuery();
//         lastQueryTime = millis();
//         Serial.print("Alive ");
//         Serial.println(bytesReceived);
//     }

//     // delay(100); // -> will crash the server (remove this still crash? why)
// }

#include <WiFi.h>
#include <lwip/sockets.h>
#include <lwip/ip_addr.h>
#include <lwip/igmp.h>
#include <lwip/opt.h>
#include <lwip/errno.h>
#include <cerrno>

char* ssid = "CHT061975";
char* password = "24577079";

#define MDNS_GROUP "224.0.0.251"  // mDNS 多播組地址
#define MDNS_PORT 5353            // mDNS 使用的端口

int send_socket = 0;                       // 用於發送的 socket
int recv_socket;                           // 用於接收的 socket
unsigned long lastQueryTime = 0;           // 上次發送查詢的時間
const unsigned long queryInterval = 2000;  // 查詢間隔時間（毫秒）
char buffer[1024];
char output[1024];
int recv_from_error_occur = 0;
int counter = 0;
int last_counter = 0;

void sendMulticastQuery() {
  // // 建立 mDNS 多播查詢封包
  // uint8_t mdns_query[] = {
  //     0x00, 0x00,  // Transaction ID
  //     0x00, 0x00,  // Flags
  //     0x00, 0x01,  // Questions: 1
  //     0x00, 0x00,  // Answer RRs
  //     0x00, 0x00,  // Authority RRs
  //     0x00, 0x00,  // Additional RRs
  //     0x0A, '_', 'r', 'a', 'w', 's', 'o', 'c', 'k', 'e', 't',  // Service
  //     name: _rawsocket 0x04, '_', 't', 'c', 'p', // Protocol: _tcp 0x05, 'l',
  //     'o', 'c', 'a', 'l', 0x00,                     // Domain: local 0x00,
  //     0x0C,  // Type PTR (to find all instances of the service) 0x80, 0x01 //
  //     Class IN
  // };

  uint8_t mdns_query[] = {
      0x00, 0x00,                                      // Transaction ID
      0x00, 0x00,                                      // Flags
      0x00, 0x01,                                      // Questions: 1
      0x00, 0x00,                                      // Answer RRs
      0x00, 0x00,                                      // Authority RRs
      0x00, 0x00,                                      // Additional RRs
      0x08, 'i',  'c', '-', 'a', 'm', 'e',  'b', 'a',  // Hostname: ic-ameba
      0x05, 'l',  'o', 'c', 'a', 'l', 0x00,            // Domain: local
      0x00, 0x01,                                      // Type A (Host Address)
      0x80, 0x01  // Class IN with unicast-response bit set
  };

  struct sockaddr_in destAddr;
  memset(&destAddr, 0, sizeof(destAddr));
  destAddr.sin_family = AF_INET;
  destAddr.sin_port = htons(MDNS_PORT);
  destAddr.sin_addr.s_addr = inet_addr(MDNS_GROUP);

  // 使用專用的發送 socket 發送多播查詢
  sendto(send_socket, mdns_query, sizeof(mdns_query), 0,
         (struct sockaddr*)&destAddr, sizeof(destAddr));

  Serial.println(
      "Sent Multicast Query for _rawsocket._tcp.local requesting Unicast "
      "Response");
}

bool init_send_socket() {
  if (send_socket) {
    close(send_socket);
  }

  // 創建用於發送的 socket
  send_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  if (send_socket < 0) {
    Serial.println("Failed to create send socket");
    return false;
  }

  // 設置 socket 為非阻塞模式
  int flags = lwip_fcntl(send_socket, F_GETFL, 0);
  if (lwip_fcntl(send_socket, F_SETFL, flags | O_NONBLOCK) < 0) {
    Serial.println("Failed to set socket to non-blocking mode");
    close(send_socket);
    return false;
  }

  Serial.println("Send socket initialized successfully in non-blocking mode");
  return true;
}

void setup() {
  Serial.begin(115200);

  // 連接到 WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  init_send_socket();

  // 創建用於接收的 socket
  recv_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  if (recv_socket < 0) {
    Serial.println("Failed to create recv socket");
    close(send_socket);  // 清理發送 socket
    return;
  }

  // 綁定接收 socket 到 mDNS 埠以便接收數據
  struct sockaddr_in localAddr;
  memset(&localAddr, 0, sizeof(localAddr));
  localAddr.sin_family = AF_INET;
  localAddr.sin_addr.s_addr = htonl(INADDR_ANY);
  localAddr.sin_port = htons(MDNS_PORT);

  if (bind(recv_socket, (struct sockaddr*)&localAddr, sizeof(localAddr)) < 0) {
    Serial.println("Failed to bind recv socket");
    close(send_socket);
    close(recv_socket);
    return;
  }

  // 設置接收 socket 加入多播組
  struct ip_mreq mreq;
  mreq.imr_multiaddr.s_addr = inet_addr(MDNS_GROUP);
  mreq.imr_interface.s_addr = htonl(INADDR_ANY);

  if (setsockopt(recv_socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq,
                 sizeof(mreq)) < 0) {
    Serial.println("Failed to join multicast group on recv socket");
    close(send_socket);
    close(recv_socket);
    return;
  }

  Serial.println("Joined multicast group, ready to receive mDNS packets.");
  sendMulticastQuery();
  lastQueryTime = millis();  // 記錄發送時間
}

void loop() {
  int bytesReceived = 0;
  struct sockaddr_in sourceAddr;
  socklen_t sourceAddrLen = sizeof(sourceAddr);

  // 接收來自多播組的數據
  // XXX: change from recv_socket to send_socket
  bytesReceived = recvfrom(send_socket, buffer, sizeof(buffer), 0,
                           (struct sockaddr*)&sourceAddr, &sourceAddrLen);

  if (bytesReceived > 0) {
    // Serial.print("Received bytes: ");
    // Serial.println(bytesReceived);

    // Disable below print works fine
    char* ptr = output;
    int offset = 0;
    counter += 1;
    offset += sprintf(ptr + offset,
                      "Received %d bytes from %s:%d\nCurrent packet: %d\n",
                      bytesReceived, inet_ntoa(sourceAddr.sin_addr),
                      ntohs(sourceAddr.sin_port), counter);
    Serial.println(ptr);

    // for (int i = 0; i < bytesReceived; i++) {
    //     offset += sprintf(ptr + offset, "%02X ", (uint8_t)buffer[i]);
    //     if ((i + 1) % 16 == 0) {
    //         offset += sprintf(ptr + offset, "\n");
    //     }
    // }
    // Serial.println(output);
  } else if (bytesReceived < 0 && errno != EAGAIN) {
    recv_from_error_occur = 1;
  }

  // 定期發送多播查詢
  if (millis() - lastQueryTime >= queryInterval) {
    sendMulticastQuery();
    lastQueryTime = millis();
    Serial.print("Alive, last received bytes: ");
    Serial.println(bytesReceived);
    Serial.println(recv_from_error_occur);

    // determine socket dead or not
    if (last_counter == counter) {
      Serial.println("mDNS service found dead. Restart the socket");
      // init_send_socket();
      bytesReceived = recvfrom(recv_socket, buffer, sizeof(buffer), 0,
                               (struct sockaddr*)&sourceAddr, &sourceAddrLen);
    }

    // assume we can get resopond in next loop
    last_counter = counter;
  }

  // clean recv_socket (avoid lwip crash)
}
