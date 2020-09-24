# Smarthome ESP32 Serial Protocol

### Frame Structure

`!r_p[<path: string>]_b[<body: json>]_\r\n`

### Communication Secification

#### Initialization

##### Broadcast

The request is used to identify every chip in the network

| Sender | Receiver | Path                      | Payload                                                |
|:------ |:--------:| -------------------------:| ------------------------------------------------------:|
| Master | Chip     | `smarthome/broadcast/req` | `{"session_id": <session_id>}`                         |
| Chip   | Master   | `smarthome/broadcast/res` | `{"chip_id": "<chip_id>", "session_id": <session_id>}` |

##### Reset config

The request is used to reset the whole eeprom of the receiving chip

| Sender | Receiver | Path                     | Payload                                     |
|:------ |:--------:| ------------------------:| -------------------------------------------:|
| Master | Chip     | `smarthome/config/reset` | `{"session_id": <session_id>}`              |
| Chip   | Master   | `smarthome/config/reset` | `{"ack": true, "session_id": <session_id>}` |

#### ID

The chip ID can have a length between 1 and 20

##### Write

| Sender | Receiver | Path                     | Payload                                                                                         |
|:------ |:--------:| ------------------------:| -----------------------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write` | `{"receiver": "<chip id>", "param": "id", "value": "<the new id>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write` | `{"ack": true, "session_id": <session_id>}`                                                     |

#### Wifi SSID

The SSID of the Wifi network the chip should connect to

##### Read

| Sender | Receiver | Path                    | Payload                                                |
|:------ |:--------:| -----------------------:| ------------------------------------------------------:|
| Master | Chip     | `smarthome/config/read` | `{"session_id": <session_id>}`                         |
| Chip   | Master   | `smarthome/config/read` | `{"value": "<wifi ssid>", "session_id": <session_id>}` |

##### Write

| Sender | Receiver | Path                     | Payload                                                                                                  |
|:------ |:--------:| ------------------------:| --------------------------------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write` | `{"receiver": "<chip id>", "param": "wifi_ssid", "value": "<the new ssid>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write` | `{"ack": true, "session_id": <session_id>}`                                                              |

#### Wifi PW

The password of the Wifi network the chip should connect to

##### Write

| Sender | Receiver | Path                     | Payload                                                                                              |
|:------ |:--------:| ------------------------:| ----------------------------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write` | `{"receiver": "<chip id>", "param": "wifi_pw", "value": "<the new pw>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write` | `{"ack": true, "session_id": <session_id>}`                                                          |

#### MQTT IP

The IP of the mqtt broker the chip should connect to

##### Read

| Sender | Receiver | Path                    | Payload                                              |
|:------ |:--------:| -----------------------:| ----------------------------------------------------:|
| Master | Chip     | `smarthome/config/read` | `{"session_id": <session_id>}`                       |
| Chip   | Master   | `smarthome/config/read` | `{"value": "<mqtt ip>", "session_id": <session_id>}` |

##### Write

| Sender | Receiver | Path                     | Payload                                                                                              |
|:------ |:--------:| ------------------------:| ----------------------------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write` | `{"receiver": "<chip id>", "param": "mqtt_ip", "value": "<the new ip>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write` | `{"ack": true, "session_id": <session_id>}`                                                          |

#### MQTT Port

The port of the mqtt broker the chip should connect to

##### Read

| Sender | Receiver | Path                    | Payload                                                |
|:------ |:--------:| -----------------------:| ------------------------------------------------------:|
| Master | Chip     | `smarthome/config/read` | `{"session_id": <session_id>}`                         |
| Chip   | Master   | `smarthome/config/read` | `{"value": "<mqtt port>", "session_id": <session_id>}` |

##### Write

| Sender | Receiver | Path                     | Payload                                                                                                  |
|:------ |:--------:| ------------------------:| --------------------------------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write` | `{"receiver": "<chip id>", "param": "mqtt_port", "value": "<the new port>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write` | `{"ack": true, "session_id": <session_id>}`                                                              |

#### MQTT Username

The username used for the mqtt broker the chip should connect to

##### Read

| Sender | Receiver | Path                    | Payload                                                    |
|:------ |:--------:| -----------------------:| ----------------------------------------------------------:|
| Master | Chip     | `smarthome/config/read` | `{"session_id": <session_id>}`                             |
| Chip   | Master   | `smarthome/config/read` | `{"value": "<mqtt username>", "session_id": <session_id>}` |

##### Write

| Sender | Receiver | Path                     | Payload                                                                                                      |
|:------ |:--------:| ------------------------:| ------------------------------------------------------------------------------------------------------------:|
| Master | Chip     | `smarthome/config/write` | `{"receiver": "<chip id>", "param": "mqtt_user", "value": "<the new username>", "session_id": <session_id>}` |
| Chip   | Master   | `smarthome/config/write` | `{"ack": true, "session_id": <session_id>}`                                                                  |

#### MQTT Password

The password used for the mqtt broker the chip should connect to

##### Read
Reading the password is not supported.

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` | 

###### Payload
```json
{
    "receiver": "<chip id>",
    "param": "mqtt_user",
    "value": "<the new username>",
    "session_id": <session_id>
}
```
