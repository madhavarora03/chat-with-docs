from enum import Enum


class Role(str, Enum):
    USER = "USER"
    CHATBOT = "CHATBOT"
