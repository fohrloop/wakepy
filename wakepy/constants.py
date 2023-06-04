import enum

class SystemName(str, enum.Enum):
    """The names of supported systems. The corresponding
    implementations are at wakepy._implementations._{system}"""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


SUPPORTED_SYSTEMS = list(x.value for x in SystemName.__members__.values())
