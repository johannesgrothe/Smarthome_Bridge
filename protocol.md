# Smarthome ESP32 Communication Specification

### Serial Communication Frame Structure

`!r_p[<path: string>]_b[<body: json>]_\r\n`

### Body Structure

```json
{
  "sender": "<sender id>",
  "receiver": "<receiver id>",
  "session_id": <session_id>,
  "payload": {}
}
```

None of the keys are optional, but the `receiver` and `payload` can be `null` for broadcasts.

### Initialization

---

#### Broadcast

The broadcast is used to identify every chip in the network. The Request 

###### Request Frame Info

| Sender | Receiver | Path                      |
|:------ |:--------:| -------------------------:|
| Master | Chip     | `smarthome/broadcast/req` |

###### Request Payload

```json
null
```

###### Response Frame Info

| Sender | Receiver | Path                      |
|:------ |:--------:| -------------------------:|
| Chip   | Master   | `smarthome/broadcast/res` |

###### Response Payload

```json
null
```

---

#### Reset config

The request is used to reset the whole eeprom of the receiving chip

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/reset` |

###### Request Payload

```json
null
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### Chip ID

The chip ID can have a length between 1 and 20

##### Read

Reading the ID makes no sense since you need the ID to direct the request anyway.
Read all IDs on the bus by sending a broadcast.

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "id",
  "value": "<the new id>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### Wifi SSID

The SSID of the Wifi network the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                    |
|:------ |:--------:| -----------------------:|
| Master | Chip     | `smarthome/config/read` |

###### Request Payload

```json
{
  "param": "wifi_ssid"
}
```

###### Response Payload

```json
{
  "value": "<wifi ssid>"
}
```

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "wifi_ssid",
  "value": "<the new ssid>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### Wifi PW

The password of the Wifi network the chip should connect to

##### Read

Reading the password is not supported.

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "wifi_pw",
  "value": "<the new password>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### MQTT IP

The IP of the mqtt broker the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                    |
|:------ |:--------:| -----------------------:|
| Master | Chip     | `smarthome/config/read` |

###### Request Payload

```json
{
  "param": "mqtt_ip"
}
```

###### Response Payload

```json
{
  "value": "<mqtt ip>"
}
```

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "mqtt_ip",
  "value": "<the new ip>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### MQTT Port

The port of the mqtt broker the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                    |
|:------ |:--------:| -----------------------:|
| Master | Chip     | `smarthome/config/read` |

###### Request Payload

```json
{
  "param": "mqtt_port"
}
```

###### Response Payload

```json
{
  "value": "<mqtt port>"
}
```

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "mqtt_port",
  "value": "<the new port>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### MQTT Username

The username used for the mqtt broker the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                    |
|:------ |:--------:| -----------------------:|
| Master | Chip     | `smarthome/config/read` |

###### Request Payload

```json
{
  "param": "mqtt_user"
}
```

###### Response Payload

```json
{
  "value": "<mqtt username>"
}
```

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "mqtt_user",
  "value": "<the new username>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```

---

#### MQTT Password

The password used for the mqtt broker the chip should connect to

##### Read

Reading the password is not supported.

##### Write

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

###### Request Payload

```json
{
  "param": "mqtt_pw",
  "value": "<the new password>"
}
```

###### Response Payload

```json
{
  "ack": true
}
```