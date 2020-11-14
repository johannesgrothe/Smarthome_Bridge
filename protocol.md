# Smarthome ESP32 Communication Specification

## Serial Communication Frame Structure

`!r_p[<path: string>]_b[<body: json>]_\r\n`

## Body Structure

```json
{
  "sender": string,
  "receiver": string,
  "session_id": uint,
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
  "reset_option": string
}
```

Supported reset options:

- "erase"
- "complete"
- "config"
- "gadgets"

##### Response Payload

```json
{
  "ack": bool,
  <optional> "status_msg": string
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
  "ack": bool,
  <optional> "status_msg": string
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
  "param": string,
  "value": <value datatype>
}
```

##### Response Payload

```json
{
  "ack": bool,
  <optional> "status_msg": string
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
  "param": string
}
```

##### Response Payload

```json
{
  "value": <value datatype>
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
      "type": string,
      "name": string,
      "ports": {
        "port0": uint,
        "port1": uint,
        ...
        "port4": uint
      },
      "config": {},
      "codes": {},
      "remotes": {
        "gadget": uint,
        "code": uint,
        "event": uint
      }
    }
```

##### Response Payload

```json
{
  "ack": bool,
  <optional> "status_msg": string
}
```

## Remotes

Remotes are used store and sync information about the whole system.

### Gadget Remote

The gadget remote stores the status of all gadgets and provides the information to external clients like apple home or a own webinterface/app

#### Update status on the remote

##### Frame Info

| Sender | Receiver | Path                              |
|:------ |:--------:| ---------------------------------:|
| Master | Chip     | `smarthome/remotes/gadget/update` |

##### Request Payload

The request payload is just the complete gadget config as json.

```json
{
  "name": string,
  "type": uint,
  "characteristic": uint,
  "value": int
}
```

##### Response Payload

No response is sent.

#### Update status on the chip

##### Frame Info

| Sender | Receiver | Path                              |
|:------ |:--------:| ---------------------------------:|
| Master | Chip     | `smarthome/remotes/gadget/update` |

##### Request Payload

The request payload is just the complete gadget config as json.

```json
{
  "name": string,
  "type": uint,
  "characteristic": uint,
  "value": int
}
```

##### Response Payload

No response is sent.