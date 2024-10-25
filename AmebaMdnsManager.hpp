#ifndef MDNS_MANAGER_HPP
#define MDNS_MANAGER_HPP

#include "stdint.h"
#include <Arduino.h>

// 定義 mDNS 多播組地址和埠
#define MDNS_MULTICAST_GROUP "224.0.0.251"
#define MDNS_PORT            5353

// 定義查詢間隔（毫秒）
#define MDNS_MULTICAST_QUERY_INTERVAL 2000

class MDNSManager
{
 public:
  // 建構函數：決定是否啟用多播和單播功能
  MDNSManager(bool enableMulticast = true, bool enableUnicast = false);

  // 初始化多播服務
  bool initMulticast();

  // 初始化單播服務
  bool initUnicast();

  // 發送 mDNS 多播查詢
  void sendMulticastQuery();

  // 發送單播查詢
  bool sendUnicastQuery(const char* domain);

  // 獲取最後一次單播查詢的回覆者 IP 地址
  String getLastUnicastReplyIP() const;

  // 重置最後一次單播查詢的回覆者 IP 地址
  void resetLastUnicastReplyIP();

  bool isValidIpV4(String ipv4);

  // 在 Arduino 的 loop() 中呼叫
  void update();

  // 關閉所有 socket
  void closeSockets();

  // 解構函數
  ~MDNSManager();

 private:
  // Socket 成員
  int multicastSocket;
  int unicastSocket;

  // 配置標記
  bool multicastEnabled;
  bool unicastEnabled;

  // 多播查詢相關
  unsigned long lastMulticastQueryTime;
  const unsigned long multicastQueryInterval;
  char multicastBuffer[1024];
  char multicastOutput[1024];
  bool multicastRecvError;
  int multicastReceiveCounter;
  int multicastLastReceiveCounter;

  // 單播查詢相關
  bool unicastRecvError;
  int unicastReceiveCounter;
  int unicastLastReceiveCounter;
  uint32_t lastUnicastReplyIP;

  // 私有方法
  bool initMulticastSocket();
  bool initUnicastSocket();
  void handleMulticastReceive();
  void handleUnicastReceive();
  void handleMulticastQuery();
};

#endif  // MDNS_MANAGER_HPP
