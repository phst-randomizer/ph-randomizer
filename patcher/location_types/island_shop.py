from ndspy import code

from . import Location

GD_MODELS = {
    0x00: None,
    0x01: 'key',
    0x02: 'rupee_g',
    0x03: 'swA',
    0x04: 'shA',
    0x05: '',  # TODO: what is this?
    0x06: 'force_y',  # TODO: find force gem model
    0x07: 'bomb',
    0x08: 'bow',
    0x09: 'rupee_g',
    0x0A: 'heart_utu',
    0x0B: '',  # TODO: what is this?
    0x0C: 'boomerang',
    0x0D: 'scp',
    0x0E: 'bomchu',
    0x0F: 'bosskey',
    0x10: 'rev_bin',
    0x11: '',  # TODO: what is this?
    0x12: '',  # TODO: what is this?
    0x13: 'mapSea',
    0x14: 'mapSea',
    0x15: 'mapSea',
    0x16: 'mapSea',
    0x17: '',  # TODO: what is this?
    0x18: 'rupee_b',
    0x19: 'rupee_r',
    0x1A: 'rupee_r',
    0x1B: 'rupee_go',
    0x1C: 'force_y',  # NOTE: Used in multiplayer mode only
    0x1D: 'force_r',  # NOTE: Used in multiplayer mode only
    0x1E: 'force_b',  # NOTE: Used in multiplayer mode only
    0x1F: 'ham',
    0x20: 'rope',
    0x21: 'cstl_c',
    0x22: 'cstl_s',
    0x23: 'cstl_t',
    0x24: 'fp',
    0x25: 'ship',  # TODO: ship or ship02?
    0x26: 'key_su',
    0x27: '',  # TODO: what is this?
    0x28: 'arrowpodL',  # TODO: arrowpod or arrowpodL?
    0x29: 'bmbagL',  # TODO: bmbag or bmbagL or bmbagM?
    0x2A: 'bcbagL',  # TODO: bcbag or bcbagL or bcbagM?
    0x2B: '',  # TODO: what is this?
    0x2C: 'key_ki',
    0x2D: 'minaP',
    0x2E: 'minaC',
    0x2F: 'minaY',
    0x30: 'sango',
    0x31: 'perlA',
    0x32: 'perlB',
    0x33: 'uroko',
    0x34: 'mineral',
    0x35: 'crown',
    0x36: 'wing',
    0x37: 'ring',
    0x38: 'key_gh',
    0x39: 'tic_tada',
    0x3A: 'tic_ohome',
    0x3B: 'tic_rare',
    0x3C: 'neckl',
    0x3D: 'slvarm',
    0x3E: '',  # TODO: find id for hero"s new clothes
    0x3F: 'telescope',
    0x40: 'notebook',
    0x41: 'letter',
    0x42: 'card',
    0x43: 'marron',
    0x44: '',  # TODO: what is this?
    0x45: '',  # TODO: what is this?
    0x46: '',  # TODO: what is this?
    0x47: '',  # TODO: what is this?
    0x48: '',  # TODO: what is this?
    0x49: '',  # TODO: what is this?
    0x4A: '',  # TODO: what is this?
    0x4B: 'mapTakara',
    0x4C: 'mapTakara',
    0x4D: 'mapTakara',
    0x4E: 'mapTakara',
    0x4F: 'mapTakara',
    0x50: 'mapTakara',
    0x51: 'mapTakara',
    0x52: 'mapTakara',
    0x53: 'mapTakara',
    0x54: 'mapTakara',
    0x55: 'mapTakara',
    0x56: 'mapTakara',
    0x57: 'mapTakara',
    0x58: 'mapTakara',
    0x59: 'mapTakara',
    0x5A: 'mapTakara',
    0x5B: 'mapTakara',
    0x5C: 'mapTakara',
    0x5D: 'mapTakara',
    0x5E: 'mapTakara',
    0x5F: 'mapTakara',
    0x60: 'mapTakara',
    0x61: 'mapTakara',
    0x62: 'mapTakara',
    0x63: 'mapTakara',
    0x64: 'mapTakara',
    0x65: 'mapTakara',
    0x66: 'mapTakara',
    0x67: 'mapTakara',
    0x68: 'mapTakara',
    0x69: 'mapTakara',
    0x6A: 'mapTakara',
    0x6B: '',  # TODO: what is this?
    0x6C: '',  # TODO: what is this?
    0x6D: '',  # TODO: what is this?
    0x6E: '',  # TODO: what is this?
    0x6F: '',  # TODO: what is this?
    0x70: '',  # TODO: what is this?
    0x71: '',
    0x72: 'hagaH',
    0x73: 'hagaK',
    0x74: 'hagaS',
    0x75: 'rev_bin',
    0x76: 'rev_binP',
    0x77: 'rev_binY',
    0x78: 'sand_m',
    0x79: 'ship',  # TODO: ship or ship02?
    0x7A: 'ship',  # TODO: ship or ship02?
    0x7B: 'ship',  # TODO: ship or ship02?
    0x7C: 'ship',  # TODO: ship or ship02?
    0x7D: '',  # TODO: what to do for random treasure?
    0x7E: '',  # TODO: what to do for random ship part?
    0x7F: '',  # TODO: find warp tablet model
    0x80: '',  # TODO: find bait model
    0x81: 'rupee_bb',
    0x82: 'rupee_bb',
    0x83: '',  # TODO: what is this?
    0x84: '',  # TODO: what is this?
    0x85: '',  # TODO: what to do for random ship part?
    0x86: '',  # TODO: what to do for random treasure?
    0x87: '',  # TODO: what to do for random ship part?
    # TODO: are there any more items?
}


class IslandShopLocation(Location):
    """These locations represent items that can be purchased at island shops."""

    _overlay_table: dict[int, code.Overlay] = {}

    def __init__(self, overlay_number: int, item_id_index: int):
        self.overlay_number = overlay_number
        self.item_id_index = item_id_index

    def set_location(self, new_item_id: int):
        # Load arm9.bin and overlay table
        arm9_executable = bytearray(
            code.MainCodeFile(self.__class__.ROM.arm9, 0x02000000).save(compress=False)
        )
        overlay_table = self.__class__.ROM.loadArm9Overlays()

        # Get current values of the items we're about to change
        original_item_id: int = overlay_table[self.overlay_number].data[self.item_id_index]
        original_model_name = f'gd_{GD_MODELS[original_item_id]}'

        # Set the item id to the new one. This changes the "internal" item representation,
        # but not the 3D model that is displayed prior to purchasing the item
        overlay_table[self.overlay_number].data[self.item_id_index] = new_item_id

        # The name of the NSBMD/NSBTX model we're changing to
        new_model_name = f'gd_{GD_MODELS[new_item_id]}'

        offset = arm9_executable.index(f'Player/get/{original_model_name}.nsbmd'.encode('ascii'))
        new_data = bytearray(f'Player/get/{new_model_name}.nsbmd'.encode('ascii') + b'\x00')
        arm9_executable = (
            arm9_executable[:offset] + new_data + arm9_executable[offset + len(new_data) :]
        )

        offset = arm9_executable.index(f'Player/get/{original_model_name}.nsbtx'.encode('ascii'))
        new_data = bytearray(f'Player/get/{new_model_name}.nsbtx'.encode('ascii') + b'\x00')
        arm9_executable = (
            arm9_executable[:offset] + new_data + arm9_executable[offset + len(new_data) :]
        )

        try:
            offset = overlay_table[self.overlay_number].data.index(
                original_model_name.encode('ascii')
            )
            new_data = bytearray(new_model_name.encode('ascii') + b'\x00')
            overlay_table[self.overlay_number].data = (
                overlay_table[self.overlay_number].data[:offset]
                + new_data
                + overlay_table[self.overlay_number].data[offset + len(new_data) :]
            )
            # Pad remaining non-NULL chars to 0. If this isn't done and there are characters
            # left from the previous item, the game will crash.
            for i in range(offset + len(new_data), offset + 16):
                overlay_table[self.overlay_number].data[i] = 0x0
        except ValueError:
            # Random treasure items (which should be fixed to Pink Coral in our hacked base rom)
            # are an exception and do not require this step.
            assert original_item_id == 0x30

        self.__class__.ROM.files[overlay_table[self.overlay_number].fileID] = overlay_table[
            self.overlay_number
        ].save(compress=False)
        self.__class__.ROM.arm9OverlayTable = code.saveOverlayTable(overlay_table)
        self.__class__.ROM.arm9 = arm9_executable

    @classmethod
    def save_all(cls):
        pass
