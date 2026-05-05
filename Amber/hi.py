from machine import ADC, Pin, I2C, PWM
from fifo import Fifo
from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from led import Led
import time

adc = ADC(Pin(26))

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
fifo = Fifo(500, typecode='i')

sample_rate = 250

previous_value = 0
current_value = 0
previous_direction = "down"
current_direction = "down"

MIN_PEAK_DIST = 130
MAX_PEAK_DIST = 250

smooth_buf = []
SMOOTH_N = 30

sample_counter = 0
last_peak = 0

signal = []
hr_buf = []
hr_buf_len = 10

tr = 0
ctr = 0


def handler(tid):
    raw_value = adc.read_u16()

    try:
        fifo.put(raw_value)
    except:
        fifo.get()
        fifo.put(raw_value)


timer = Piotimer(
    mode=Piotimer.PERIODIC,
    freq=sample_rate,
    callback=handler
)

def calc_mean(array):
    s = sum(array)
    mean = s / len(array)
    return mean
PPI = 0
BPM = 0
while True:
    while fifo.has_data():
        raw = fifo.get()
        sample_counter += 1

        smooth_buf.append(raw)

        if len(smooth_buf) > SMOOTH_N:
            smooth_buf.pop(0)

        current_value = sum(smooth_buf) // len(smooth_buf)

        signal.append(current_value)

        if len(signal) > 100:
            signal.pop(0)

        if previous_value < current_value:
            current_direction = "up"
        elif previous_value > current_value:
            current_direction = "down"
        else:
            current_direction = previous_direction

        if previous_direction == "up" and current_direction == "down":
            peak_value = previous_value
            peak_position = sample_counter - 1
            samples_since_peak = peak_position - last_peak

            if samples_since_peak >= MIN_PEAK_DIST:
                if len(signal) >= 50:
                    recent = signal[-50:]
                    tr = (max(recent) + min(recent)) // 2

                if peak_value > tr:
                    PPI = samples_since_peak * (1 / sample_rate * 1000)
                    BPM = 60 / (PPI / 1000)

                    if 40 <= BPM <= 200:
                        hr_buf.append(BPM)
                        if len(hr_buf) >= hr_buf_len:
                            hr_buf.pop(0)
                            #print(f"PPI: {PPI:.1f} BPM: {BPM:.1f} N:{samples_since_peak}")
                            print(f"PPI: {PPI:.1f} mean BPM: {calc_mean(hr_buf)} N:{samples_since_peak}")

                        last_peak = peak_position

        ctr += 1

        #if ctr % 50 == 0: #print(f"sample_cnt:{sample_counter} {current_value} {tr}")

        previous_value = current_value
        previous_direction = current_direction
#         print(PPI)
#         print(BPM)



