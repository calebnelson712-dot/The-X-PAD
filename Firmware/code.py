import board
import busio
import digitalio
import storage

from kmk.kmk_keyboard import KMKKeyboard
from kmk.matrix import DiodeOrientation
from kmk.scanners import ioexpander
from kmk.handlers.sequences import send_string
from kmk.keys import KC
from kmk.modules.encoder import EncoderHandler
from kmk.modules.layers import Layers
from kmk.modules.rgb import RGB
from kmk.modules.media_keys import MediaKeys
from kmk.extensions.OLED import OLED, OledDisplayMode, OledReactionType

from adafruit_mcp230xx.mcp23017 import MCP23017

# --- I2C setup ---
i2c = busio.I2C(board.GP1, board.GP0)  # SCL: GP1, SDA: GP0 (swap if your wiring is different)
mcp = MCP23017(i2c, address=0x20)

# --- Key matrix setup via MCP23017 ---
# Rows: GPB0-B3, Cols: GPB4-B6, GPA0
ROW_PINS = [8, 9, 10, 11]  # MCP23017 GPB0-GPB3
COL_PINS = [12, 13, 14, 21]  # GPB4-GPB6, GPA0

# --- KMK Keyboard object ---
keyboard = KMKKeyboard()

keyboard.matrix = ioexpander.IOExpanderMatrix(
    mcp,
    row_pins=ROW_PINS,
    col_pins=COL_PINS,
    columns_to_anodes=True,
    diode_orientation=DiodeOrientation.COL2ROW,
)

keyboard.modules.append(Layers())
keyboard.modules.append(MediaKeys())

# --- RGB setup ---
rgb = RGB(pixel_pin=board.GP3, num_pixels=16, val_limit=80, hue_default=0)
keyboard.modules.append(rgb)

# --- OLED setup ---
oled_ext = OLED(
    i2c=i2c,  # Use same I2C bus as MCP23017
    addr=0x3C,
    flip=False,
    display_mode=OledDisplayMode.LAYER,
    timeout=60,
    reaction=OledReactionType.LAYER,
)
keyboard.extensions.append(oled_ext)

# --- Encoder setup (via MCP23017) ---
encoder_handler = EncoderHandler()
# Encoder 1: A1 (22), B1 (23), S1 (24) [GPA1-3]
# Encoder 2: A2 (25), B2 (26), S2 (27) [GPA4-6]
encoder_handler.pins = [
    (22, 23),  # Encoder 1 A/B
    (25, 26),  # Encoder 2 A/B
]
encoder_handler.swpins = [24, 27]  # Encoder 1/2 switch pins (S1/S2)
keyboard.modules.append(encoder_handler)

# --- Keymap ---
# Example multimedia pad layout
keyboard.keymap = [
    [KC.MPLY, KC.MPRV, KC.MNXT, KC.MSTP,
     KC.VOLU, KC.VOLD, KC.MUTE, KC.MUTE,
     KC.FAST_FWD, KC.REWIND, KC.PSCR, KC.CALC,
     KC.NO, KC.NO, KC.NO, KC.NO],
]

# --- Encoder Actions ---
@encoder_handler.handler
def encoder_callback(index, direction):
    if index == 0:
        # Encoder 1: Volume
        if direction == 1:
            keyboard.send(KC.VOLU)
        else:
            keyboard.send(KC.VOLD)
    elif index == 1:
        # Encoder 2: Scroll
        if direction == 1:
            keyboard.send(KC.PGDN)
        else:
            keyboard.send(KC.PGUP)

# Encoder switch actions
@encoder_handler.switch_handler
def encoder_switch_callback(index, pressed):
    if pressed:
        if index == 0:
            # Encoder 1 switch: mute/unmute
            keyboard.send(KC.MUTE)
        elif index == 1:
            # Encoder 2 switch: change RGB layer (cycles through, for demonstration)
            rgb.next_layer()

if __name__ == '__main__':
    keyboard.go()