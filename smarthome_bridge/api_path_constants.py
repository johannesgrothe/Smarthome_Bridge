import enum


class ApiPathConstants(enum.IntEnum):
    """A number identifier for every path constant"""
    PATH_CLIENT_SYSTEM_CONFIG_WRITE = 0
    PATH_CLIENT_EVENT_CONFIG_WRITE = 1
    PATH_CLIENT_GADGET_CONFIG_WRITE = 2
    PATH_CLIENT_CONFIG_WRITE = 3
    PATH_CLIENT_CONFIG_DELETE = 4
    PATH_HEARTBEAT = 5
    PATH_INFO_BRIDGE = 6
    PATH_INFO_CLIENTS = 7
    PATH_INFO_GADGETS = 8
    PATH_SYNC_GADGET = 9
    PATH_UPDATE_GADGET = 10
    PATH_SYNC_CLIENT = 11
    PATH_CLIENT_REBOOT = 12
    PATH_SYNC_REQUEST = 13
    PATH_SYNC_EVENT = 14
    PATH_TEST_ECHO = 15


def api_path_identifier_to_str(in_ident: ApiPathConstants) -> str:
    """translates enum identifier to string identifier"""
    switcher = {
        ApiPathConstants.PATH_CLIENT_SYSTEM_CONFIG_WRITE: "config/system/write",
        ApiPathConstants.PATH_CLIENT_EVENT_CONFIG_WRITE: "config/event/write",
        ApiPathConstants.PATH_CLIENT_GADGET_CONFIG_WRITE: "config/gadget/write",
        ApiPathConstants.PATH_CLIENT_CONFIG_WRITE: "config/write",
        ApiPathConstants.PATH_CLIENT_CONFIG_DELETE: "config/delete",
        ApiPathConstants.PATH_HEARTBEAT: "heartbeat",
        ApiPathConstants.PATH_INFO_BRIDGE: "info/bridge",
        ApiPathConstants.PATH_INFO_CLIENTS: "info/clients",
        ApiPathConstants.PATH_INFO_GADGETS: "info/gadgets",
        ApiPathConstants.PATH_SYNC_GADGET: "sync/gadget",
        ApiPathConstants.PATH_UPDATE_GADGET: "update/gadget",
        ApiPathConstants.PATH_SYNC_CLIENT: "sync/client",
        ApiPathConstants.PATH_CLIENT_REBOOT: "reboot/client",
        ApiPathConstants.PATH_SYNC_REQUEST: "sync",
        ApiPathConstants.PATH_SYNC_EVENT: "sync/event",
        ApiPathConstants.PATH_TEST_ECHO: "echo"
    }
    return switcher.get(in_ident, "heartbeat")


def str_to_api_path_constants(in_ident: str) -> ApiPathConstants:
    """Translates a string identifier to a enum identifier"""
    switcher = {
        "config/system/write": ApiPathConstants.PATH_CLIENT_SYSTEM_CONFIG_WRITE,
        "config/event/write": ApiPathConstants.PATH_CLIENT_EVENT_CONFIG_WRITE,
        "config/gadget/write": ApiPathConstants.PATH_CLIENT_GADGET_CONFIG_WRITE,
        "config/write": ApiPathConstants.PATH_CLIENT_CONFIG_WRITE,
        "config/delete": ApiPathConstants.PATH_CLIENT_CONFIG_DELETE,
        "heartbeat": ApiPathConstants.PATH_HEARTBEAT,
        "info/bridge": ApiPathConstants.PATH_INFO_BRIDGE,
        "info/clients": ApiPathConstants.PATH_INFO_CLIENTS,
        "info/gadgets": ApiPathConstants.PATH_INFO_GADGETS,
        "sync/gadget": ApiPathConstants.PATH_SYNC_GADGET,
        "update/gadget": ApiPathConstants.PATH_UPDATE_GADGET,
        "sync/client": ApiPathConstants.PATH_SYNC_CLIENT,
        "reboot/client": ApiPathConstants.PATH_CLIENT_REBOOT,
        "sync": ApiPathConstants.PATH_SYNC_REQUEST,
        "sync/event": ApiPathConstants.PATH_SYNC_EVENT,
        "echo": ApiPathConstants.PATH_TEST_ECHO
    }
    return switcher.get(in_ident, ApiPathConstants.PATH_HEARTBEAT)