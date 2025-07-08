# System
from enum import Enum

class SMType(Enum):
    LIFECYCLE = 1
    SA = 2
    MA = 3

def snake(name: str) -> str:
    return name.replace(' ', '_')
