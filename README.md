## 移植 ArduinoMDNS 到 Ameba Pro 2 (Abort)

修改處包含:

- ArduinoMDNS

  - MDNS.h:

    ```cpp
    #ifdef ARDUINO_AMBPRO2
    #include <wifi_Udp.h>
    #endif
    ```

- Ameba
  - wifi_Udp.h

    ```cpp
    // in public
    virtual int beginMulticast(IPAddress address, uint16_t p) = 0;
    ```

  - WiFiUdp.h

    ```cpp
    virtual int beginMulticast(IPAddress address, uint16_t p);
    ```
