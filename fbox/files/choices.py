from enum import IntEnum


class StatusChoice(IntEnum):
    waiting = 1
    complete = 2


class LevelChoice(IntEnum):
    visitor = 1
    red = 2


class UploadFailChoice(IntEnum):
    empty_file = 40001
    too_much_file = 40002
    big_file = 40003
    too_much_error = 40004
    too_fast = 40005
    invalid_name = 40006
    invalid_file = 40007
