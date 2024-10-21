#include "WiFi.h"
#include "StreamIO.h"
#include "VideoStream.h"
#include "RTSP.h"
#include <WiFiClient.h>

#define CHANNEL     0
#define RTSP_FPS    (30)
#define RTSP_PORT   554                // Standard RTSP port
#define SERVER_IP   "192.168.153.129"  // Replace with your server's IP
#define SERVER_PORT 12345

/* >> DISABLE THIS WHEN YOU WANT DIRECTLY SHOW RTSP << */
// #define START_STREAM_ONLY_AFTER_CONNECT_TO_SERVER

// Default preset configurations for each video channel:
// Channel 0 : 1920 x 1080 30FPS H264
// Channel 1 : 1280 x 720  30FPS H264
// Channel 2 : 1280 x 720  30FPS MJPEG

// VideoSetting config(CHANNEL);
// // Custom FPS
VideoSetting config(VIDEO_FHD, RTSP_FPS, VIDEO_HEVC, 0);

RTSP rtsp;
WiFiClient client;
StreamIO videoStreamer(1, 1);  // 1 Input Video -> 1 Output RTSP

// char ssid[] = "Frank";     // your network SSID (name)
// char pass[] = "24577079";  // your network password
char ssid[] = "a52s";      // your network SSID (name)
char pass[] = "11111111";  // your network password

int status = WL_IDLE_STATUS;
unsigned long previousMillis = 0;
const long interval = 10000;  // 10 seconds

#ifdef START_STREAM_ONLY_AFTER_CONNECT_TO_SERVER
bool enable_camera_stream = false;
#endif

void sendDeviceInfo(WiFiClient& client, const char* serverIP,
                    uint16_t serverPort, uint16_t rtspPort)
{
  if (client.connect(serverIP, serverPort) && client.connected())
  {
    /**
     * @brief example:
     * "AA:BB:CC:DD:EE:FF,192.168.1.10,554"
     */

    Serial.println("Connected to server");

    // Get MAC address
    uint8_t mac[6];
    WiFi.macAddress(mac);

    // Convert MAC address to string
    char macStr[18];  // 6*2 hex digits + 5 colons + 1 null terminator
    sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2],
            mac[3], mac[4], mac[5]);

    // Get IP address and manually convert to string
    IPAddress ip = WiFi.localIP();
    char ipStr[16];  // Max length of an IP address in the form xxx.xxx.xxx.xxx
    sprintf(ipStr, "%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);

    // Create dataToSend string
    String dataToSend =
        String(macStr) + "," + String(ipStr) + "," + String(rtspPort);

    // Send data to server
    client.println(dataToSend);

/* enable camera */
#ifdef START_STREAM_ONLY_AFTER_CONNECT_TO_SERVER
    if (!enable_camera_stream)
    {
      Camera.channelBegin(CHANNEL);
      enable_camera_stream = true;
      Serial.println("\n\n\nCamera channel begin\n\n\n");
    }
#endif
  }
  else
  {
    Serial.println("Connection to server failed");

#ifdef START_STREAM_ONLY_AFTER_CONNECT_TO_SERVER
    if (enable_camera_stream)
    {
      Camera.channelEnd(CHANNEL);
      enable_camera_stream = false;
      Serial.println("\n\n\nCamera channel end\n\n\n");
    }
#endif
  }
}

void setup()
{
  Serial.begin(115200);

  // attempt to connect to Wifi network:
  while (status != WL_CONNECTED)
  {
    Serial.print("Attempting to connect to WPA SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);

    // wait 2 seconds for connection:
    delay(2000);
  }

  // Configure camera video channel with video format information
  // Adjust the bitrate based on your WiFi network quality
  config.setBitrate(4 * 1024 * 1024);  // Recommend to use 2Mbps for RTSP
  // config.setJpegQuality(25);
  // streaming to prevent network congestion
  Camera.configVideoChannel(CHANNEL, config);
  Camera.videoInit();

  // Configure RTSP with identical video format information
  rtsp.configVideo(config);
  rtsp.begin();  // Start RTSP server on specified port

  // Configure StreamIO object to stream data from video channel to RTSP
  videoStreamer.registerInput(Camera.getStream(CHANNEL));
  videoStreamer.registerOutput(rtsp);
  if (videoStreamer.begin() != 0)
  {
    Serial.println("StreamIO link start failed");
  }

#ifndef START_STREAM_ONLY_AFTER_CONNECT_TO_SERVER
  // Start data stream from video channel
  Camera.channelBegin(CHANNEL);
#endif

  delay(1000);
  printInfo();

  // Connect to Python TCP server
  sendDeviceInfo(client, SERVER_IP, SERVER_PORT, RTSP_PORT);
}

void loop()
{
  unsigned long currentMillis = millis();

  if (!client.connected())
  {
    Serial.println("Disconnected from server, attempting to reconnect");
    sendDeviceInfo(client, SERVER_IP, SERVER_PORT, RTSP_PORT);
  }

  if (currentMillis - previousMillis >= interval)
  {
    previousMillis = currentMillis;
    if (client.connected())
    {
      client.println("AliveHeartBeat");
    }
    else
    {
      Serial.println("Cannot send heartbeat, not connected to server");
    }
  }
}

void printInfo(void)
{
  Serial.println("------------------------------");
  Serial.println("- Summary of Streaming -");
  Serial.println("------------------------------");
  Camera.printInfo();

  IPAddress ip = WiFi.localIP();

  Serial.println("- RTSP -");
  Serial.print("rtsp://");
  Serial.print(ip);
  Serial.print(":");
  rtsp.printInfo();
}
