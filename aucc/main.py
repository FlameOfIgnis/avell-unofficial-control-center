"""
Copyright (c) 2019, Rodrigo Gomes.
Distributed under the terms of the MIT License.
The full license is in the file LICENSE, distributed with this software.
Created on May 22, 2019
@author: @rodgomesc
"""
import argparse
import sys, os
from aucc.core.handler import DeviceHandler
import time
from aucc.core.colors import (get_mono_color_vector,
                         get_h_alt_color_vector,
                         get_v_alt_color_vector,
                         _colors_available)


#                   ?      ?                                
# style template: (0x08, 0x02, STYLE_ID, DELAY_TIME, 0x24, 0x08, 0x00, 0x00)
light_style = {
    'rainbow':  0x05,
    'reactive': 0x04,
    'raindrop': 0x0A,
    'marquee':  0x09, 
    'aurora':   0x0E, 
    'pulse':    0x02, 
    'wave':     0x03, 
    'drop':     0x06, 
    'firework': 0x11
}

# keybpoard brightness have 4 variations 0x08,0x16,0x24,0x32
brightness_map = {
    1: 0x08,
    2: 0x16,
    3: 0x24,
    4: 0x32
}


class ControlCenter(DeviceHandler):
    def __init__(self, vendor_id, product_id):
        super(ControlCenter, self).__init__(vendor_id, product_id)
        self.brightness = None

    def disable_keyboard(self):
        self.ctrl_write(0x08, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)

    def keyboard_style(self,style,delay, rotation, brightness):
        self.ctrl_write(0x08, 0x02, light_style[style], delay, brightness, 0x08, rotation, 0x00)

    def adjust_brightness(self, brightness=None):
        if brightness:
            self.brightness = brightness
            self.ctrl_write(0x08, 0x02, 0x33, 0x00,
                            brightness_map[self.brightness], 0x00, 0x00, 0x00)
        else:
            self.adjust_brightness(4)

    def color_scheme_setup(self):
        self.ctrl_write(0x12, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00)

    def mono_color_setup(self, color_scheme):

        if self.brightness:
            self.color_scheme_setup()
            color_vector = get_mono_color_vector(color_scheme)
            self.bulk_write(times=8, payload=color_vector)
        else:
            self.adjust_brightness()
            self.mono_color_setup(color_scheme)

    def h_alt_color_setup(self, color_scheme_a, color_scheme_b):

        self.color_scheme_setup()
        color_vector = get_h_alt_color_vector(color_scheme_a, color_scheme_b)
        self.bulk_write(times=8, payload=color_vector)

    def v_alt_color_setup(self, color_scheme_a, color_scheme_b):

        self.color_scheme_setup()
        color_vector = get_v_alt_color_vector(color_scheme_a, color_scheme_b)
        self.bulk_write(times=8, payload=color_vector)


def main():
    from elevate import elevate

    if not os.geteuid() == 0:
        elevate()

    control = ControlCenter(vendor_id=0x048d, product_id=0xce00)

    parser = argparse.ArgumentParser(
        description="Supply at least one of the options [-c|-H|-V|-s|-d]. "
        "Colors available: "
        "[red|green|blue|teal|pink|purple|white|yellow|orange]")
    parser.add_argument('-c', '--color', help='Single color')
    parser.add_argument('-b', '--brightness', help='1, 2, 3 or 4')
    parser.add_argument('-H', '--h-alt', nargs=2,
                        help='Horizontal alternating colors')
    parser.add_argument('-V', '--v-alt', nargs=2,
                        help='Vertical alternating colors')
    parser.add_argument('-s', '--style',
                        help='one of (rainbow, reactive, raindrop, marquee, aurora)')
    parser.add_argument('-S', '--speed',
                        help='style speed, only to be used with -s (0-5)')
    parser.add_argument('-r', '--rotation',
                        help='style rotation, only to be used with -s, (1-4)')
    parser.add_argument('-sd', '--styleDebug',
                        help='style byte directly from parameter')
    parser.add_argument('-d', '--disable', action='store_true',
                        help='turn keyboard backlight off'),

    parsed = parser.parse_args()
    if parsed.disable:
        control.disable_keyboard()
    if parsed.brightness:
        control.adjust_brightness(int(parsed.brightness))
    if parsed.color:
        control.mono_color_setup(parsed.color)
    elif parsed.h_alt:
        control.h_alt_color_setup(*parsed.h_alt)
    elif parsed.v_alt:
        control.v_alt_color_setup(*parsed.v_alt)
    elif parsed.style:
        speed=3
        brightness=0x32
        rotation=1
        if parsed.speed and int(parsed.speed) <=5 and int(parsed.speed) >=0:
            speed=5-int(parsed.speed)
        if parsed.rotation and int(parsed.rotation) <=4 and int(parsed.rotation) >=0:
            rotation=int(parsed.rotation)          
        if parsed.brightness and int(parsed.brightness) <=4 and int(parsed.brightness) >=1:
            brightness=brightness_map[int(parsed.brightness)]


        control.keyboard_style(parsed.style,speed,rotation, brightness)
    elif parsed.styleDebug:
        control.keyboard_styleDebug(parsed.styleDebug)
    else:
        print("Invalid or absent command")


if __name__ == "__main__":
    main()
