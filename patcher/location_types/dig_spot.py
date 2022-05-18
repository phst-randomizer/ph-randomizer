from collections import defaultdict
from typing import Optional

from ndspy.lz10 import compress, decompress
from ndspy.narc import NARC
from zed.common import Game
from zed.zmb import ZMB, Actor

from ._location import Location


class DigSpotLocation(Location):
    """These locations represent items that can be dug up with the shovel."""

    # Class variables that track open ZMB files. This is done for performance reasons; a single ZMB
    # file can contain many item locations, and continously opening the same ZMB file over and over
    # again causes slowdowns.

    # maps filenames objects to ZMB objects
    _zmb_filename_mapping: dict[str, ZMB] = {}

    # maps NARC file objects to filenames
    _narc_filename_mapping: dict[NARC, str] = {}

    # mapping between ZMB file names and their parent NARC files
    _narc_to_zmb_mapping: dict[NARC, list[str]] = defaultdict(list)

    def __init__(self, actor_index: int, file_path: str, *args, **kwargs):
        self.actor_index = actor_index
        self.file_path = file_path
        self.zmb_file: Optional[ZMB] = None

        # check if this zmb file is already open first
        for filename, zmb_file in DigSpotLocation._zmb_filename_mapping.items():
            if filename == self._zmb_filepath:
                self.zmb_file = zmb_file

        if self.zmb_file is None:
            narc_file = NARC(decompress(self.__class__.ROM.getFileByName(self._narc_filepath)))
            DigSpotLocation._narc_filename_mapping[narc_file] = self._narc_filepath
            self.zmb_file = ZMB(
                game=Game.PhantomHourglass, data=narc_file.getFileByName(self._zmb_filepath)
            )
            DigSpotLocation._narc_to_zmb_mapping[narc_file].append(self._zmb_filepath)
            DigSpotLocation._zmb_filename_mapping[self._zmb_filepath] = self.zmb_file

    def set_location(self, value: int):
        assert self.zmb_file is not None
        zmb_actor: Actor = self.zmb_file.actors[self.actor_index]
        assert (
            zmb_actor.type == "DGTG"
        ), f"Error: DigSpotLocation with invalid actor type '{zmb_actor.type}'"
        zmb_actor.unk0C = value
        DigSpotLocation._zmb_filename_mapping[self._zmb_filepath] = self.zmb_file

    @property
    def _narc_filepath(self):
        """Return the filepath of the NARC archive (ending with '.bin' extension) containing this ZMB file."""
        path: list[str] = []
        for part in self.file_path.split("/"):
            path.append(part)
            if "." in part:
                return "/".join(path)

    @property
    def _zmb_filepath(self):
        """Return the filepath of the ZMB file within its parent NARC archive."""
        index: int
        part: str
        for index, part in enumerate(self.file_path.split("/")):
            if "." in part:
                return "/".join(self.file_path.split("/")[index + 1 :])

    @classmethod
    def save_all(cls):
        for narc_file, zmb_filenames in DigSpotLocation._narc_to_zmb_mapping.items():
            for zmb_filename in zmb_filenames:
                narc_file.setFileByName(
                    zmb_filename,
                    DigSpotLocation._zmb_filename_mapping[zmb_filename].save(
                        game=Game.PhantomHourglass
                    ),
                )
            cls.ROM.setFileByName(
                DigSpotLocation._narc_filename_mapping[narc_file], compress(narc_file.save())
            )
