"""
stepper.py

A module to control bipolar stepper motors.

Project:  ESPy32 (Stepper)
Board:    ESP32
Firmware: MicroPython 1.19.1

Author:   João Vítor Carvalho (eJoaoCarvalho)
E-mail:   ejoaocarvalho@gmail.com
Updated:  Oct 12, 2022
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

from math import ceil
from umachine import Pin, Signal
from utime import sleep_us


class Stepper:
    
    """
    Allows ESP32 to control bipolar stepper motors.
    
    ...
    
    Parameters
    ----------
    stp_pin : int
        Pin id connected to driver step (stp) input.
    dir_pin : int, optional
        Pin id connected to driver rot_dir (dir) input.
    en_pin : int, optional
        Pin id connected to driver enable (en) input.
    
    Attributes
    ----------
    FORWARD
        Set stepper rotation to clockwise
    REVERSE
        Set stepper rotation to counterclockwise
    HOLD
        Keep the stepper axis position after rotationf.initial_speed
        The minimum rpm that the stepper can rotate
    microsteps : {1, 2, 4, 8, 16, 32}
        Microstepping configuration for motor drive.
    rpm : int
        rpm value for define stepper velocity.
    _initial_step_us : int
        step_intervalo de temppo base.
    accel_rate: int
        Percent of steps to accelerate.
    
    Methods
    -------
    rotate_revs(n)
        Rotate the stepper axis n times.
    rotate_degs(n)
        Rotate the stepper axis n degrees.
    rotate_steps(n)
        Rotate the stepper axis n steps.
    
    Examples
    --------
    Basic use of this class
    
    >>> import Stepper
    >>> stepper_1 = Stepper(27, 26, 25)
    >>> stepper_1.rotate_revs(5)
    """
    
    FORWARD = 1
    REVERSE = 0
    HOLD = True
    
    def __init__(self, stp_pin: int, dir_pin: int = None, en_pin: int = None):
        """
        Setup the pins connected to Stepper driver.
        
        Parameters
        ----------
        stp_pin : int
            Pin id connected to driver step (stp) input
        dir_pin : int, optional
            Pin id connected to driver rot_dir (dir) input, by default None
        en_pin : int, optional
            Pin id connected to driver enable (en) input, by default None
        """
        self._stp_pin = Pin(stp_pin, Pin.OUT)
        
        if dir_pin is None:
            self._dir_pin = False
        else:
            self._dir_pin = Pin(dir_pin, Pin.OUT)
        
        if en_pin is None:
            self._en_pin = False
        else:
            # Signal class allows to abstract away active-[high/low] difference
            self._en_pin = Signal(Pin(en_pin, Pin.OUT), invert=True)
        
        self._microsteps = 1
        
        
        self._initial_speed = 200
        self._initial_step_us = self.get_step_us(self.initial_speed)
        
        self._target_speed = self._initial_speed
        self._target_step_us = self._initial_step_us              
        
        self._accel_rate = 0
    
    
    # Microsteps config
    @property
    def microsteps(self):
        return self._microsteps
    
    @microsteps.setter
    def microsteps(self, u_steps):
        """Set the microsteps with a valid number (described on datasheet)."""
        if u_steps in [1, 2, 4, 8, 16, 32]:
            self._microsteps = u_steps
    
    # Initial speed (rpm) config
    @property
    def initial_speed(self):
        return self._initial_speed
    
    @initial_speed.setter
    def initial_speed(self, new_speed):
        self._initial_speed = new_speed
        self._initial_step_us = self.get_step_us(self.initial_speed)
    
    # Target speed (rpm) config
    @property
    def target_speed(self):
        return self._target_speed
    
    @target_speed.setter
    def target_speed(self, new_speed):
        self._target_speed = new_speed
        self._target_step_us = self.get_step_us(self.target_speed)
        print(f"step_us setado: {self._target_step_us}")
    
    @property
    def accel_rate(self):
        return self._accel_rate
    
    @accel_rate.setter
    def accel_rate(self, percent):
        # 101 because range end is excluded
        if percent in range(101):
            # Half of accel is done in initial and another in ending
            self._accel_rate = percent/100
    

    def get_step_us(self, speed: int) -> int:
        """calculates the time (us) of each step."""
        return ceil((1.8 / (6 * speed * self.microsteps)) * pow(10, 6))
    
    def _rotate(to_steps):
        def mode(self, n: int, rot_dir: int = 1, hold: bool = False) -> None:
            """Rotate the motor and control acceleration."""
            steps = to_steps(self, n)
            # Original equation is: step_interval = (60s * 1.8°) / (rpm * 360° * microsteps)
            step_interval = int(self._target_step_us / 2)
            
            if self.accel_rate:
                steps_to_accel = (steps * self.accel_rate) / 2
                accel_point = steps_to_accel
                decel_point = (steps - 1) - steps_to_accel
                
                delta_accel = (self._initial_step_us - self._target_step_us) / 2
                increment = delta_accel / steps_to_accel
                
                step_interval = int(self._initial_step_us / 2)
            
            if self._dir_pin:
                self._dir_pin.value(rot_dir)
            
            if self._en_pin:
                self._en_pin.on()
            
            for step in range(steps):
                
                interval = int(step_interval)
                
                self._stp_pin.on()
                sleep_us(interval)
                self._stp_pin.off()
                sleep_us(interval)
                
                if self.accel_rate:
                    if step < accel_point:
                        step_interval-=increment
                    elif step >= decel_point:
                        step_interval+=increment
                
            if self._en_pin and not hold:
                self._en_pin.off()
        return mode
    
    @_rotate
    def rotate_degs(self, degs: int) -> int:
        """Do X and return a list.********************"""
        return (degs/360) * 200 * self.microsteps
    
    @_rotate
    def rotate_revs(self, revs: int) -> int:
        """Get the quantity of revolutions (revs) and return steps needed."""
        return revs * 200 * self.microsteps
    
    @_rotate
    def rotate_steps(self, steps: int) -> int:
        """Get the steps and send it to rotate."""
        return steps


def main():
    stepper = Stepper(25, 26, 27)
    stepper.rotate_revs(10)
    stepper.rotate_revs(5, Stepper.REVERSE)
    stepper.target_speed = 300
    stepper.accel_rate = 50
    stepper.rotate_revs(20)

if __name__ == '__main__':
    main()