# Smarthome ESP32 Communication Specification

## Serial Communication Frame Structure

`!r_p[<path: string>]_b[<body: json>]_\r\n`

## Body Structure

```json
{
  "sender": "<sender id>",
  "receiver": "<receiver id>",
  "session_id": <session_id>,
  "payload": {}
}
```

None of the keys are optional, but the `receiver` and `payload` can be `null` for broadcasts.

## Special Messages

### Broadcast

The broadcast is used to identify every chip in the network. 

##### Request Frame Info

| Sender | Receiver | Path                      |
|:------ |:--------:| -------------------------:|
| Master | Chip     | `smarthome/broadcast/req` |

##### Request Payload

```json
null
```

##### Response Frame Info

| Sender | Receiver | Path                      |
|:------ |:--------:| -------------------------:|
| Chip   | Master   | `smarthome/broadcast/res` |

##### Response Payload

```json
null
```

---

### Reset config

The request is used to reset the whole eeprom of the receiving chip.

##### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/reset` |

##### Request Payload

```json
{
  "reset_option": <reset_option>
}
```

Supported reset options:

- erase
- complete
- config
- gadgets

##### Response Payload

```json
{
  "ack": true
}
```

---

### Reboot Chip

The request is used to reboot the chip.

##### Frame Info

| Sender | Receiver | Path            |
|:------ |:--------:| ---------------:|
| Master | Chip     | `smarthome/sys` |

##### Request Payload

```json
{
  "subject": "reboot"
}
```

##### Response Payload

```json
{
  "ack": true
}
```

---

## Write Settings

### Possible Params to Write

| Param Name | Value Datatype |
|:---------- |:--------------:|
| id         | int            |
| wifi_ssid  | string         |
| wifi_pw    | string         |
| mqtt_ip    | string         |
| mqtt_port  | string         |
| mqtt_user  | string         |
| mqtt_pw    | string         |

##### Frame Info

| Sender | Receiver | Path                     |
|:------ |:--------:| ------------------------:|
| Master | Chip     | `smarthome/config/write` |

##### Request Payload

```json
{
  "param": "<param_name>",
  "value": "<param_value>"
}
```

##### Response Payload

```json
{
  "ack": true
}
```

---

## Read Settings

### Possible Params to Read

| Param Name | Value Datatype |
|:---------- |:--------------:|
| wifi_ssid  | string         |
| mqtt_ip    | string         |
| mqtt_port  | string         |
| mqtt_user  | string         |

##### Frame Info

| Sender | Receiver | Path                    |
|:------ |:--------:| -----------------------:|
| Master | Chip     | `smarthome/config/read` |

##### Request Payload

```json
{
  "param": "<param_name>"
}
```

##### Response Payload

```json
{
  "value": "<param_value>"
}
```

### Gadgets

Gadgets are the implementation of all kind of smarthome hardware. Gadgets are uploaded one at a time, checking if their name and ports are unique.

#### Read

tdb

#### Write

##### Frame Info

| Sender | Receiver | Path                   |
|:------ |:--------:| ----------------------:|
| Master | Chip     | `smarthome/gadget/add` |

##### Request Payload

The request payload is just the complete gadget config as json.

```json
    {
      "type": "<gadget_type>",
      "name": "<gadget_name>",
      "ports": {
        "port0": 2,
        "port1": 3,
        ...
        "port4": 3
      },
      "config": {},
      "codes": {},
      "remotes": {
        "gadget": 1,
        "code": 1,
        "event": 1
      }
    }
```

##### Response Payload

```json
{
  "ack": true,
  "status_msg": "a string explaning what failed if a failure occurred"
}
```