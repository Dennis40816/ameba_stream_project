#include "AmebaMdnsManager.hpp"

#include <WiFi.h>
#include <lwip/sockets.h>
#include <lwip/ip_addr.h>
#include <lwip/igmp.h>
#include <arpa/inet.h>
#include <lwip/opt.h>
#include <lwip/errno.h>
#include <cerrno>
#include <cstring>

// 建構函數
MDNSManager::MDNSManager(bool enableMulticast, bool enableUnicast)
    : multicastEnabled(enableMulticast),
      unicastEnabled(enableUnicast),
      multicastSocket(-1),
      unicastSocket(-1),
      lastMulticastQueryTime(0),
      multicastQueryInterval(MDNS_MULTICAST_QUERY_INTERVAL),
      multicastRecvError(false),
      multicastReceiveCounter(0),
      multicastLastReceiveCounter(0),
      unicastRecvError(false),
      unicastReceiveCounter(0),
      unicastLastReceiveCounter(0),
      lastUnicastReplyIP(0)
{
  memset(multicastBuffer, 0, sizeof(multicastBuffer));
  memset(multicastOutput, 0, sizeof(multicastOutput));
}

// 初始化多播 socket
bool MDNSManager::initMulticast() { return initMulticastSocket(); }

// 初始化單播 socket
bool MDNSManager::initUnicast() { return initUnicastSocket(); }

// 初始化多播 socket 的私有方法
bool MDNSManager::initMulticastSocket()
{
  // 創建用於多播的 socket
  multicastSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  if (multicastSocket < 0)
  {
    Serial.println("Failed to create multicast socket");
    return false;
  }

  // 設置 socket 為非阻塞模式
  int flags = lwip_fcntl(multicastSocket, F_GETFL, 0);
  if (lwip_fcntl(multicastSocket, F_SETFL, flags | O_NONBLOCK) < 0)
  {
    Serial.println("Failed to set multicast socket to non-blocking mode");
    close(multicastSocket);
    multicastSocket = -1;
    return false;
  }

  // 綁定 socket 到 mDNS 埠
  struct sockaddr_in localAddr;
  memset(&localAddr, 0, sizeof(localAddr));
  localAddr.sin_family = AF_INET;
  localAddr.sin_addr.s_addr = htonl(INADDR_ANY);
  localAddr.sin_port = htons(MDNS_PORT);

  if (bind(multicastSocket, (struct sockaddr*)&localAddr, sizeof(localAddr)) <
      0)
  {
    Serial.println("Failed to bind multicast socket");
    close(multicastSocket);
    multicastSocket = -1;
    return false;
  }

  // 加入多播組
  struct ip_mreq mreq;
  mreq.imr_multiaddr.s_addr = inet_addr(MDNS_MULTICAST_GROUP);
  mreq.imr_interface.s_addr = htonl(INADDR_ANY);

  if (setsockopt(multicastSocket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq,
                 sizeof(mreq)) < 0)
  {
    Serial.println("Failed to join multicast group on multicast socket");
    close(multicastSocket);
    multicastSocket = -1;
    return false;
  }

  Serial.println("Joined multicast group, ready to receive mDNS packets.");
  return true;
}

// 初始化單播 socket 的私有方法
bool MDNSManager::initUnicastSocket()
{
  // 創建用於單播的 socket
  unicastSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  if (unicastSocket < 0)
  {
    Serial.println("Failed to create unicast socket");
    return false;
  }

  // 設置 socket 為非阻塞模式
  int flags = lwip_fcntl(unicastSocket, F_GETFL, 0);
  if (lwip_fcntl(unicastSocket, F_SETFL, flags | O_NONBLOCK) < 0)
  {
    Serial.println("Failed to set unicast socket to non-blocking mode");
    close(unicastSocket);
    unicastSocket = -1;
    return false;
  }

  Serial.println(
      "Unicast socket initialized successfully in non-blocking mode");
  return true;
}

// 發送 mDNS 多播查詢
void MDNSManager::sendMulticastQuery()
{
  if (multicastSocket == -1)
  {
    Serial.println("Multicast socket not initialized");
    return;
  }

  // 建立 mDNS 多播查詢封包
  uint8_t mdns_query[] = {
      0x00, 0x00,  // Transaction ID
      0x00, 0x00,  // Flags
      0x00, 0x01,  // Questions: 1
      0x00, 0x00,  // Answer RRs
      0x00, 0x00,  // Authority RRs
      0x00, 0x00,  // Additional RRs
      // Query: _rawsocket._tcp.local
      0x0A, '_', 'r', 'a', 'w', 's', 'o', 'c', 'k', 'e', 't',  // _rawsocket
      0x04, '_', 't', 'c', 'p',                                // _tcp
      0x05, 'l', 'o', 'c', 'a', 'l', 0x00,                     // local
      0x00, 0x0C,                                              // Type PTR
      0x00, 0x01                                               // Class IN, QM
  };

  struct sockaddr_in destAddr;
  memset(&destAddr, 0, sizeof(destAddr));
  destAddr.sin_family = AF_INET;
  destAddr.sin_port = htons(MDNS_PORT);
  destAddr.sin_addr.s_addr = inet_addr(MDNS_MULTICAST_GROUP);

  // 發送多播查詢
  ssize_t sentBytes = sendto(multicastSocket, mdns_query, sizeof(mdns_query), 0,
                             (struct sockaddr*)&destAddr, sizeof(destAddr));

  if (sentBytes < 0)
  {
    Serial.println("Failed to send multicast query");
  }
  else
  {
    Serial.println(
        "Sent Multicast Query for _rawsocket._tcp.local requesting Unicast "
        "Response");
  }
}

bool MDNSManager::isValidIpV4(String ipv4)
{
  struct sockaddr_in sa;
  int result = inet_pton(AF_INET, ipv4.c_str(), &(sa.sin_addr));
  return result == 1;
}

// 發送單播查詢
bool MDNSManager::sendUnicastQuery(const char* domain)
{
  if (unicastSocket == -1)
  {
    Serial.println("Unicast socket not initialized");
    return false;
  }

  // 建立單播查詢封包（根據 mDNS 規範構造）
  // DNS Header (12 bytes)
  uint8_t dnsHeader[12] = {
      0x00, 0x01,  // Transaction ID
      0x00, 0x00,  // Flags
      0x00, 0x01,  // Questions: 1
      0x00, 0x00,  // Answer RRs
      0x00, 0x00,  // Authority RRs
      0x00, 0x00   // Additional RRs
  };

  // 將域名轉換為 DNS 格式
  uint8_t dnsQuery[512];
  size_t pos = 0;
  memcpy(dnsQuery + pos, dnsHeader, sizeof(dnsHeader));
  pos += sizeof(dnsHeader);

  // 使用臨時緩衝區避免修改原始字串
  char domainCopy[256];
  strncpy(domainCopy, domain, sizeof(domainCopy) - 1);
  domainCopy[sizeof(domainCopy) - 1] = '\0';

  char* label = strtok(domainCopy, ".");
  while (label != NULL)
  {
    size_t len = strlen(label);
    if (len > 63)
    {  // 每個標籤最多 63 個字元
      Serial.println("Domain label too long");
      return false;
    }
    dnsQuery[pos++] = (uint8_t)len;
    memcpy(dnsQuery + pos, label, len);
    pos += len;
    label = strtok(NULL, ".");
  }
  dnsQuery[pos++] = 0x00;  // 結尾

  // Type PTR (0x000C) and Class IN (0x0001)
  dnsQuery[pos++] = 0x00;
  dnsQuery[pos++] = 0x01;  // Type A
  dnsQuery[pos++] = 0x80;  // QU
  dnsQuery[pos++] = 0x01;  // Class IN

  // 發送單播查詢到特定目標
  // 這裡假設目標 IP 為 "224.0.0.251"，根據實際需求調整
  struct sockaddr_in destAddr;
  memset(&destAddr, 0, sizeof(destAddr));
  destAddr.sin_family = AF_INET;
  destAddr.sin_port = htons(MDNS_PORT);
  destAddr.sin_addr.s_addr =
      inet_addr(MDNS_MULTICAST_GROUP);  // 可根據需求設置為特定 IP

  // 發送單播查詢
  ssize_t sentBytes = sendto(unicastSocket, dnsQuery, pos, 0,
                             (struct sockaddr*)&destAddr, sizeof(destAddr));

  if (sentBytes < 0)
  {
    Serial.println("Failed to send unicast query");
    return false;
  }
  else
  {
    Serial.println("Sent Unicast Query for domain discovery");
    return true;
  }
}

// 獲取最後一次單播查詢的回覆者 IP 地址
String MDNSManager::getLastUnicastReplyIP() const
{
  if (lastUnicastReplyIP == 0)
  {
    return String("");
  }
  struct in_addr ipAddr;
  ipAddr.s_addr = lastUnicastReplyIP;
  return String(inet_ntoa(ipAddr));
}

// 重置最後一次單播查詢的回覆者 IP 地址
void MDNSManager::resetLastUnicastReplyIP() { lastUnicastReplyIP = 0; }

// 處理接收的多播數據
void MDNSManager::handleMulticastReceive()
{
  if (multicastSocket == -1) return;

  struct sockaddr_in sourceAddr;
  socklen_t sourceAddrLen = sizeof(sourceAddr);
  ssize_t bytesReceived =
      recvfrom(multicastSocket, multicastBuffer, sizeof(multicastBuffer) - 1, 0,
               (struct sockaddr*)&sourceAddr, &sourceAddrLen);

  if (bytesReceived > 0)
  {
    multicastBuffer[bytesReceived] = '\0';  // 確保字符串終止

    char* ptr = multicastOutput;
    int offset = 0;
    multicastReceiveCounter += 1;
    offset +=
        sprintf(ptr + offset,
                "Multicast Received %ld bytes from %s:%d\nPacket Count: %d\n",
                bytesReceived, inet_ntoa(sourceAddr.sin_addr),
                ntohs(sourceAddr.sin_port), multicastReceiveCounter);
    Serial.println(ptr);
  }
  else if (bytesReceived < 0 && errno != EAGAIN)
  {
    multicastRecvError = true;
    Serial.println("Error occurred while receiving multicast data");
  }
}

// 處理接收的單播數據
void MDNSManager::handleUnicastReceive()
{
  if (unicastSocket == -1) return;

  struct sockaddr_in sourceAddr;
  socklen_t sourceAddrLen = sizeof(sourceAddr);
  ssize_t bytesReceived =
      recvfrom(unicastSocket, multicastBuffer, sizeof(multicastBuffer) - 1, 0,
               (struct sockaddr*)&sourceAddr, &sourceAddrLen);

  if (bytesReceived > 0)
  {
    multicastBuffer[bytesReceived] = '\0';  // 確保字符串終止

    lastUnicastReplyIP = sourceAddr.sin_addr.s_addr;  // 獲取回覆者的 IP

    char* ptr = multicastOutput;
    int offset = 0;
    unicastReceiveCounter += 1;
    offset +=
        sprintf(ptr + offset,
                "Unicast Received %ld bytes from %s:%d\nPacket Count: %d\n",
                bytesReceived, inet_ntoa(sourceAddr.sin_addr),
                ntohs(sourceAddr.sin_port), unicastReceiveCounter);
    Serial.println(ptr);
  }
  else if (bytesReceived < 0 && errno != EAGAIN)
  {
    unicastRecvError = true;
    Serial.println("Error occurred while receiving unicast data");
  }
}

// 定期發送多播查詢
void MDNSManager::handleMulticastQuery()
{
  unsigned long currentTime = millis();
  if (currentTime - lastMulticastQueryTime >= multicastQueryInterval)
  {
    sendMulticastQuery();
    lastMulticastQueryTime = currentTime;
    Serial.print("Multicast Query Interval Passed. Receive Count: ");
    Serial.println(multicastReceiveCounter);
    Serial.println(multicastRecvError ? "Error occurred" : "No error");

    // 判斷 mDNS 服務是否中斷
    if (multicastLastReceiveCounter == multicastReceiveCounter)
    {
      Serial.println(
          "mDNS Multicast service may be dead. Restarting multicast socket...");
      closeSockets();
      if (initMulticastSocket())
      {
        sendMulticastQuery();
      }
      else
      {
        Serial.println("Failed to restart multicast socket");
      }
    }

    multicastLastReceiveCounter = multicastReceiveCounter;
  }
}

// 更新方法
void MDNSManager::update()
{
  if (multicastEnabled)
  {
    handleMulticastReceive();
    handleMulticastQuery();
  }

  if (unicastEnabled)
  {
    handleUnicastReceive();
  }
}

// 關閉所有 socket
void MDNSManager::closeSockets()
{
  if (multicastSocket != -1)
  {
    close(multicastSocket);
    multicastSocket = -1;
  }
  if (unicastSocket != -1)
  {
    close(unicastSocket);
    unicastSocket = -1;
  }
}

// 解構函數
MDNSManager::~MDNSManager() { closeSockets(); }
