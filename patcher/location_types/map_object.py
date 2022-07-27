from collections import defaultdict

from ndspy import lz10, narc
from zed.common import Game
from zed.zmb import ZMB, MapObject

from . import Location


class MapObjectLocation(Location):
    """These locations represent items found "inside" a map object.

    For example, items found in chests or that drop from rolling into a tree.
    """

    # Class variables that track open ZMB files. This is done for performance reasons; a single ZMB
    # file can contain many item locations, and continously opening the same ZMB file over and over
    # again causes slowdowns.

    # maps filenames objects to ZMB objects
    _zmb_filename_mapping: dict[str, ZMB] = {}

    # maps NARC file objects to filenames
    _narc_filename_mapping: dict[narc.NARC, str] = {}

    # mapping between ZMB file names and their parent NARC files
    _narc_to_zmb_mapping: dict[narc.NARC, list[str]] = defaultdict(list)

    def __init__(self, child_index: int, file_path: str, is_tree_drop_item: bool = False):
        """
        Initialize the MapObjectLocation.

        Params:
            file_path: path to zmb file in ROM
            is_tree_drop_item: true if this location is a tree that drops an item when rolled into;
                               those locations are exceptions and require additional steps to set.
        """
        self.child_index = child_index
        self.file_path = file_path
        self.is_tree_drop_item = is_tree_drop_item
        self.zmb_file: ZMB | None = None

        # check if this zmb file is already open first
        for filename, zmb_file in MapObjectLocation._zmb_filename_mapping.items():
            if filename == self._zmb_filepath:
                self.zmb_file = zmb_file

        if self.zmb_file is None:
            narc_file = narc.NARC(
                lz10.decompress(self.__class__.ROM.getFileByName(self._narc_filepath))
            )
            MapObjectLocation._narc_filename_mapping[narc_file] = self._narc_filepath
            self.zmb_file = ZMB(
                game=Game.PhantomHourglass, data=narc_file.getFileByName(self._zmb_filepath)
            )
            MapObjectLocation._narc_to_zmb_mapping[narc_file].append(self._zmb_filepath)
            MapObjectLocation._zmb_filename_mapping[self._zmb_filepath] = self.zmb_file

    def set_location(self, value: int):
        assert self.zmb_file is not None
        zmb_child_element: MapObject = self.zmb_file.mapObjects[self.child_index]
        zmb_child_element.unk08 = value

        # Set most significant bit of the item id if this is an item that drops
        # from a tree when Link rolls into it. See `extend_RUPY_npc.c` in the
        # base code to see why we do this.
        if self.is_tree_drop_item:
            zmb_child_element.unk08 |= 0x8000

        MapObjectLocation._zmb_filename_mapping[self._zmb_filepath] = self.zmb_file

    @property
    def _narc_filepath(self):
        """Return the filepath of the NARC archive (ending with '.bin' extension) containing this ZMB file."""
        path: list[str] = []
        for part in self.file_path.split('/'):
            path.append(part)
            if '.' in part:
                return '/'.join(path)

    @property
    def _zmb_filepath(self):
        """Return the filepath of the ZMB file within its parent NARC archive."""
        index: int
        part: str
        for index, part in enumerate(self.file_path.split('/')):
            if '.' in part:
                return '/'.join(self.file_path.split('/')[index + 1 :])

    @classmethod
    def save_all(cls):
        for narc_file, zmb_filenames in MapObjectLocation._narc_to_zmb_mapping.items():
            for zmb_filename in zmb_filenames:
                narc_file.setFileByName(
                    zmb_filename,
                    MapObjectLocation._zmb_filename_mapping[zmb_filename].save(
                        game=Game.PhantomHourglass
                    ),
                )
            cls.ROM.setFileByName(
                MapObjectLocation._narc_filename_mapping[narc_file], lz10.compress(narc_file.save())
            )
