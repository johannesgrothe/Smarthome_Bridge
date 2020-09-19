# Smarthome ESP32 Serial Protocol

### Frame Structure

`!r_p[<path: string>]_b[<body: json>]_\r\n`

### Communication Secification

#### Initialization

##### Broadcast

The request is used to identify every chip in the network

| Sender | Receiver | Path                        | Payload                                                 |
|:------ |:--------:| ---------------------------:| -------------------------------------------------------:|
| Master | Chip     | `smarthome/broadcast/req`   | `{"session_id": <session_id>}`                          |
| Chip   | Master   | `smarthome/broadcast/res`   | `{"chip_id": "<chip_id>", "session_id": <session_id>}`  |

#### ID

The chip ID can have a length between 1 and 20

##### Write

| Sender | Receiver | Path                        | Payload                                                                             |
|:------ |:--------:| ---------------------------:| -----------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write/id` | `{"receiver": "<chip id>", "value": "<the new id>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write/id` | `{"ack": true, "session_id": <session_id>}`                                         |

#### Wifi SSID

The SSID of the Wifi network the chip should connect to

##### Write

| Sender | Receiver | Path                               | Payload                                                                             |
|:------ |:--------:| ----------------------------------:| -----------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write/wifi_ssid` | `{"receiver": "<chip id>", "value": "<the new ssid>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write/wifi_ssid` | `{"ack": true, "session_id": <session_id>}`                                         |

##### Read

| Sender | Receiver | Path                               | Payload                                                                             |
|:------ |:--------:| ----------------------------------:| -----------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/read/wifi_ssid` | `{"session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/read/wifi_ssid` | `{"value": "<wifi ssid>", "session_id": <session_id>}`                                         |

#### Wifi PW

The password of the Wifi network the chip should connect to

##### Write

| Sender | Receiver | Path                               | Payload                                                                             |
|:------ |:--------:| ----------------------------------:| -----------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write/wifi_pw` | `{"receiver": "<chip id>", "value": "<the new pw>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write/wifi_pw` | `{"ack": true, "session_id": <session_id>}`                                         |
