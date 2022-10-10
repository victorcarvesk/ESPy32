# Project:  Python module for Bipolar Stepper motors
# Board:    ESP32
# Firmware: MicroPython 1.19

# Author:   João Vítor Carvalho (eJoaoCarvalho)
# E-mail:   ejoaocarvalho@gmail.com
# Updated:  Oct 10, 2022
# License:  MIT


from machine import Pin, Signal
from time import sleep_us


class Stepper():
    
    FORWARD = 1
    REVERSE = 0
    
    _RPM_MIN = 250 # ~1200 us/step
    
    def __init__(self, step_pin, direction_pin=None, enable_pin=None):
        
        self.__step_pin = Pin(step_pin, Pin.OUT)
        
        if direction_pin is None:
            self.__direction_pin = False
        else:
            self.__direction_pin = Pin(direction_pin, Pin.OUT)
        
        if enable_pin is None:
            self.__enable_pin = False
        else:
            # Signal class allows to abstract away active-[high/low] difference
            self.__enable_pin = Signal(Pin(enable_pin, Pin.OUT), invert=True)
            
        self.microsteps = 1
        self.RPM = self._RPM_MIN
        self.base_period = None
        self.soft_factor = 0
    
    # To protect step_pin setup
    @property
    def step_pin(self):
        return self.__step_pin
    
    @step_pin.setter
    def step_pin(self, pin):
        if isinstance(pin, int):
            self.__step_pin = pin
    
    # To protect dir_pin setup
    @property
    def direction_pin(self):
        return self.__direction_pin
    
    @direction_pin.setter
    def direction_pin(self, pin):
        if isinstance(pin, int) or pin == False:
            self.__direction_pin = pin
    
    # To protect enable_pin setup
    @property
    def enable_pin(self):
        return self.__enable_pin
    
    @enable_pin.setter
    def enable_pin(self, pin):
        if isinstance(pin, int) or pin == False:
            self.__enable_pin = pin
    
    # Microsteps config
    @property
    def microsteps(self):
        return self.microsteps
    
    @microsteps.setter
    def microsteps(self, u_steps):
        """Set the microsteps with a valid number (described on datasheet)."""
        if u_steps in [1, 2, 4, 8, 16, 32]:
            self.microsteps = u_steps
    
    # RPM config
    @property
    def RPM(self):
        return self.RPM
        
    @RPM.setter
    def RPM(self, rpm):
        if isinstance(rpm, int):
            self.RPM = rpm
            self.base_period = self.get_period_from_rpm(self.RPM)
            # self.base_period = int(1.8 / (6 * self.RPM * self.microsteps))*10**6
            
            
    def get_period_from_rpm(self, rpm):
        
        return int((1.8 / (6 * self.RPM * self.microsteps))*10**6)
    
            
    def rotate(self, to_steps):
        def mode(units, direction=self.FORWARD, hold=False):
            steps = to_steps(units)
            # Adjustes to for loop
            steps *= 2
            print(steps)
            print(self.RPM)
            # Original equation is: period = (60s * 1.8°) / (RPM * 360° * microsteps)
            period = 800 #self.get_period_from_rpm(self.RPM)
            print(f"per : {period}")
            half_period = int(period/2)
            
            print(f"Intervalo: {half_period} us")
            
            if self.__direction_pin:
                self.__direction_pin.value(direction)
            
            if self.__enable_pin:
                self.__enable_pin.on()

            for i in range(steps):
                self.__step_pin.on()
                sleep_us(half_period)
                self.__step_pin.off()
                sleep_us(half_period)
            
            # Keep the motor position if hold required
            if self.__enable_pin and not hold:
                self.__enable_pin.off()
        return mode
    
        
    @rotate
    def rotate_degs(self, degs):        
        return (degs/360) * 200 * self.microsteps
    

    @rotate
    def rotate_revs(self, revs):        
        return revs * 200 * self.microsteps
    
    
    def rotate_accel(self, turns, percent, direction=FORWARD, hold=False):
        
        steps = turns * 400 * self.u_steps
        
        
        rpm_difference = self._RPM_MIN - self.RPM
        
        ramp_steps = steps * (percent/100) * 0.5 # The ramp need to be between 0.0~1.0
        var_us = self.get_period_from_rpm(rpm_difference) / ramp_steps
        us = self._RPM_MIN
        
        if self.__direction_pin:
            self.__direction_pin.value(direction)
        
        if self.__enable_pin:
            self.__enable_pin.on()
        
        for step in range(steps):
            
            #print(us)
            self.step.value(not self.step.value())
            
            if step < ramp_steps:
                us -= var_us
            elif step >= steps - ramp_steps:
                us += var_us
                
            sleep_us(int(us))
            
        # Keep the motor position if hold required
        if self.enable and not hold:
            self.enable.off()
        

if __name__ == '__main__':
    print("Running test...")
    stepper = Stepper(25, 26, 27)
    stepper.rotate_revs(20, Stepper.REVERSE)
    print("Test finished.")