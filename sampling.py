from machine import ADC, Pin, I2C, PWM
from fifo import Fifo
from piotimer import Piotimer

adc = ADC(Pin(26)) # initialized adc pin

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
fifo = Fifo(500, typecode='i') # Initialized fifo

sample_rate = 250

# this is where we read the input from the sensor itself and put it in the fifo
def handler(tid):
    a = adc.read_u16()
    fifo.put(a)


tmr = Piotimer(mode=Piotimer.PERIODIC, freq=sample_rate, callback=handler) #this is the timer we use to constantly collect data











