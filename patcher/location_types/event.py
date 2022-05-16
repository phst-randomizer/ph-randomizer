import struct

from ndspy import bmg

from ._location import Location


class EventLocation(Location):
    """These locations represent items given to the player by game events.

    Most commonly, these take the form of NPCs giving Link an item during dialog.
    """

    # Class variable that tracks open BMG files. This is done for performance reasons; a single BMG
    # file can contain many item locations, and continously opening the same BMG file over and over
    # again causes slowdowns.
    _filename_to_bmg_mapping: dict[bmg.BMG, str] = {}

    def __init__(self, instruction_index: int, file_path: str, *args, **kwargs):
        self.instruction_index = instruction_index
        self.file_path = file_path
        self.bmg_file = bmg.BMG(self.__class__.ROM.getFileByName(self.file_path))
        EventLocation._filename_to_bmg_mapping[self.bmg_file] = self.file_path

    def set_location(self, value: int):
        self.bmg_file.instructions[self.instruction_index] = (
            self.bmg_file.instructions[self.instruction_index][:4]
            + struct.pack("<B", value)
            + self.bmg_file.instructions[self.instruction_index][5:]
        )

    @classmethod
    def save_all(cls):
        for bmg_file, filename in EventLocation._filename_to_bmg_mapping.items():
            cls.ROM.setFileByName(filename, bmg_file.save())
