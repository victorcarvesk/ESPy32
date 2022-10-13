"""
buzzer.py

A module to control Buzzers.

Project:  ESPy32 (Buzzer)
Board:    ESP32
Firmware: MicroPython 1.19.1

Author:   João Vítor Carvalho (eJoaoCarvalho)
E-mail:   ejoaocarvalho@gmail.com
Updated:  Oct 13, 2022
License:  MIT
...

MIT License

Copyright (c) 2019-2022 João Vítor de Carvalho Côrtes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from machine import Pin, PWM
from time import sleep_ms
import re


class Buzzer(PWM):
    """
    Buzzer module to sing notes or melodies

    Args:
        PWM (_type_): _description_

    Returns:
        _type_: _description_
    """

    _BASE_NOTES = {
        'C': 16.35,
        'C#': 17.32,
        'D': 18.35,
        'D#': 19.45,
        'E': 20.60,
        'F': 21.83,
        'F#': 23.12,
        'G': 24.50,
        'G#': 25.96,
        'A': 27.50,
        'A#': 29.14,
        'B': 30.87
        }
        
    
    def __init__(self, pin: int) -> None:
        """_summary_

        Parameters
        ----------
        pin : int
            Pin id connected to buzzer positive terminal
        """
        super().__init__(Pin(pin))
        self.freq(self.get_note('A4'))
        self.duty(0)
        self.volume = 100
        
        
    def sing(self, source: list, bpm: int, compasso: str = '4/4') -> None:
        """_summary_

        Parameters
        ----------
        source : list
            _description_
        bpm : int
            _description_
        compasso : str, optional
            _description_, by default '4/4'
        """
        try:
            with open(source) as file:
                buffer = ''
                for line in file:
                    buffer += line
                source = buffer
        except:
            pass
            
        # '[/#]+[ ]?[A-Za-z0-9 ]+' -> Remover Python or C++ comments
        # '[^A-Za-z0-9-#]' -> remove unnecessary charatcers
        # '[A-Za-z]+[_]' -> remove 'NOTE_' prefix text if exists
        # The three rules are applied with '|' (or) logic
        regex = re.compile(
            '[/#]+[ ]?[A-Za-z0-9 ]+|[^A-Za-z0-9-#]|[A-Za-z]+[_]')
        raw_melody = re.sub(regex, ' ', source)
        melody = raw_melody.split()

        
        notes = [i for i in melody if melody.index(i)%2==0]
        times = [int(j) for j in melody if melody.index(j)%2==1]

        whole_note = (60_000 * int(compasso[-1])) / bpm # 1 min = 60_000 ms
        duration = 0
        
        steps = list(zip(notes, times))
                
        for note_label, time in steps:
            
            duration = whole_note / time   # common notes (standart time)
            
            # Dotted notes (represent by negative numbers) must lasts 1.5 times
            if time < 0:
                duration *= -1.5
            
            # Pauses has no sound
            if note_label=='REST':
                self.pause(duration)
                continue
            
            note = self.get_note(note_label)
            
            self.tone(note, duration)
            
            
    def get_note(self, note_label: str) -> int:
        """Receive a note_label and the int frequence on base notes dict."""        
        # Conversion to official note notation
        if note_label.upper().find('S')!=-1:
            note_label = f"{note[0]}{note[2]}#"
        
        # Each note can be found by a exponential equation
        exp = int(note_label[1])
        note_label = re.sub('[0-9]', '', note_label)
        note = self._BASE_NOTES[note_label] * pow(2, exp)
        
        return int(note)
        
        
    def tone(self, note: int, duration: float = 0) -> None:
        """ PLays a single tone."""        
        loud = int(duration*0.9)
        quiet = int(duration*0.1)
        
        if duration != 0:            
            # play a note with duration
            self.freq(note)
            self.duty(self.volume)
            sleep_ms(loud)
            self.duty(0)
            sleep_ms(quiet)
            
        else:            
            self.pin.freq(note)
            self.duty(self.volume)
        
        
    def pause(self, duration: float) -> None:
        """ Do a pause on the music execution."""
        duration = int(duration)
        sleep_ms(duration)
        
        
    def no_tone(self) -> None:
        """ Mute the buzzer."""
        self.PWM.duty(0)

# Ode to Joy - Beethoven's Symphony No. 9
ode_to_joy = """
        
    E4, 4, E4, 4, F4, 4, G4, 4,
    G4, 4, F4, 4, E4, 4, D4, 4,
    C4, 4, C4, 4, D4, 4, E4, 4,
    E4, -4, D4, 8, D4, 2,
    
    E4, 4, E4, 4, F4, 4, G4, 4,
    G4, 4, F4, 4, E4, 4, D4, 4,
    C4, 4, C4, 4, D4, 4, E4, 4,
    D4, -4, C4, 8, C4, 2,
    
    D4, 4, D4, 4, E4, 4, C4, 4,
    D4, 4, E4, 8, F4, 8, E4, 4, C4, 4,
    D4, 4, E4, 8, F4, 8, E4, 4, D4, 4,
    C4, 4, D4, 4, G3, 2,
    
    E4, 4, E4, 4, F4, 4, G4, 4,
    G4, 4, F4, 4, E4, 4, D4, 4,
    C4, 4, C4, 4, D4, 4, E4, 4,
    D4, -4, C4, 8, C4, 2
    
    """


def main():
    buzzer = Buzzer(4)
    buzzer.sing(ode_to_joy, 120)

if __name__ == '__main__':
    main()