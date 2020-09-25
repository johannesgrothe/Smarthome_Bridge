# Smarthome ESP32 Communication Specification

### Frame Structure

`!r_p[<path: string>]_b[<body: json>]_\r\n`

### Initialization

---
#### Broadcast

The broadcast is used to identify every chip in the network

###### Request Frame Info
| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/broadcast/req` | 

###### Request Payload
```json
{
  "session_id": <session_id>
}
```

###### Response Frame Info
| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/broadcast/res` | 

###### Response Payload
```json
{
  "chip_id": "<chip_id>",
  "session_id": <session_id>
}
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
{
  "receiver": "<chip id>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "id",
  "value": "<the new id>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
}
```
---
#### Wifi SSID

The SSID of the Wifi network the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/read` | 

###### Request Payload
```json
{
  "receiver": "<chip id>",
  "param": "wifi_ssid",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "value": "<wifi ssid>",
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "wifi_ssid",
  "value": "<the new ssid>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "wifi_pw",
  "value": "<the new password>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
}
```

---
#### MQTT IP

The IP of the mqtt broker the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/read` | 

###### Request Payload
```json
{
  "receiver": "<chip id>",
  "param": "mqtt_ip",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "value": "<mqtt ip>",
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "mqtt_ip",
  "value": "<the new ip>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
}
```

---
#### MQTT Port

The port of the mqtt broker the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/read` | 

###### Request Payload
```json
{
  "receiver": "<chip id>",
  "param": "mqtt_port",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "value": "<mqtt port>",
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "mqtt_port",
  "value": "<the new port>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
}
```

---
#### MQTT Username

The username used for the mqtt broker the chip should connect to

##### Read

###### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/read` | 

###### Request Payload
```json
{
  "receiver": "<chip id>",
  "param": "mqtt_user",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "value": "<mqtt username>",
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "mqtt_user",
  "value": "<the new username>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
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
  "receiver": "<chip id>",
  "param": "mqtt_pw",
  "value": "<the new password>",
  "session_id": <session_id>
}
```

###### Response Payload
```json
{
  "ack": true,
  "session_id": <session_id>
}
```