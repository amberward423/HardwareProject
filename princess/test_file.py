from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from fifo import Fifo
import time


i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)


clk = Pin(10, Pin.IN, Pin.PULL_UP)
dt = Pin(11, Pin.IN, Pin.PULL_UP)
button = Pin(12, Pin.IN, Pin.PULL_UP)


fifo = Fifo(250)

#Menu
menu_items = ["Start HRV", "Stop", "Show Data"]
current_menu_index = 0

#Button debounce
last_button_time = 0

hrv_results = None

def encoder_turn_ISR(pin):
    if dt.value() == clk.value():
        fifo.put(1)   # clockwise
    else:
        fifo.put(-1)  # counter-clockwise


def encoder_button_ISR(pin):
    global last_button_time
    now = time.ticks_ms()
# global means using the current "state" not a local one

    if time.ticks_diff(now, last_button_time) > 150:
        fifo.put(0)  # button press
        last_button_time = now


# Attach interrupts
clk.irq(handler=encoder_turn_ISR, trigger=Pin.IRQ_RISING)
button.irq(handler=encoder_button_ISR, trigger=Pin.IRQ_FALLING)




def show_menu():
    oled.fill(0)
    for i, item in enumerate(menu_items):
        if i == current_menu_index:
            oled.text("> " + item, 0, i * 10)
        else:
            oled.text("  " + item, 0, i * 10)
    oled.show()
# enumerate allows to loop over a list etc.:)

# def start_hrv():
#     print("Collecting HRV data...")
# 
# 
# def print_hvr_data():
#     print("Showing HRV data...")
def show_results(results):
    oled.fill(0)

    oled.text("HRV Results:", 0, 0)
    oled.text(f"HR:{results['mean_hr']:.1f}", 0, 10)
    oled.text(f"PPI:{results['mean_ppi']:.2f}", 0, 20)
    oled.text(f"RMSSD:{results['rmssd']:.2f}", 0, 30)
    oled.text(f"SDNN:{results['sdnn']:.2f}", 0, 40)

oled.show()

def collect_heart_rate_data(seconds=10):
    data = []
    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < seconds * 1000:
        #replace with sensor later
        hr = 60 + (time.ticks_ms() % 300) / 100
        data.append(hr)
        time.sleep(0.5)

    return data


def calculate_hrv(data):
    n = len(data)
    mean_hr = sum(data) / n

    ppi = [60 / hr for hr in data]
    mean_ppi = sum(ppi) / len(ppi)

    rmssd = 0
    for i in range(1, len(ppi)):
        rmssd += (ppi[i] - ppi[i - 1]) ** 2
    rmssd = (rmssd / (len(ppi) - 1)) ** 0.5

    sdnn = (sum([(x - mean_ppi) ** 2 for x in ppi]) / len(ppi)) ** 0.5

    return {
        "mean_hr": mean_hr,
        "mean_ppi": mean_ppi,
        "rmssd": rmssd,
        "sdnn": sdnn
    }


def start_hrv():
    global hrv_results

    oled.fill(0)
    oled.text("Measuring...", 0, 20)
    oled.show()

    data = collect_heart_rate_data(10)
    hrv_results = calculate_hrv(data)

    print(hrv_results)


def print_hvr_data():
    if hrv_results:
        show_results(hrv_results)
        time.sleep(3)
    else:
        oled.fill(0)
        oled.text("No Data Yet", 0, 20)
        oled.show()
        time.sleep(2)

def main():
    global current_menu_index

    while True:
        show_menu()

        while not fifo.empty():
            event = fifo.get()

            if event == 1:
                current_menu_index += 1

            elif event == -1:
                current_menu_index -= 1

            elif event == 0:
                # Button pressed, select
                if current_menu_index == 0:
                    start_hrv()
                elif current_menu_index == 1:
                    print("Stopped")
                elif current_menu_index == 2:
                    print("Collecting data...")

            #index in range
            current_menu_index %= len(menu_items)

        time.sleep_ms(10)


main()