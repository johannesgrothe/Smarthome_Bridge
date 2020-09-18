# Smarthome ESP32 Serial Protocol

### Frame Structure
`!r_p[<path: string>]_b[<body: json>]_\r\n`

### Communication Secification

| Sender         | Direction    | Path               | Payload
| :------------- | :----------: | -----------:       | -----------:
| Chip           | PC           | `debug/register`   | `{"chip_id": "<chip_id>", "session_id": <session_id>}`
| PC             | Chip         | `debug/register`   | `{"pc_id": "<pc_id>", "session_id": <session_id>}`
| Chip           | PC           | `debug/register`   | `{"ack": true, "session_id": <session_id>}`