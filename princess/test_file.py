from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import time

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

pin_a = Pin(8, Pin.IN, Pin.PULL_UP)
# pin_b = Pin(22, Pin.IN, Pin.PULL_UP)

encoder_value = 0
last_state = pin_a.value()

# Button
button = Pin(9, Pin.IN, Pin.PULL_UP)

# Menu items
menu_items = ["Start HRV", "Stop", "Show Data"]
current_menu_index = 0


def read_encoder():
    global last_state

    current_state = pin_a.value()
#     changed = False
    direction = 0

    if current_state != last_state:
        if pin_a.value() != current_state:
            direction = 1
        else:
            direction = -1

#         encoder_value %= 4

#         changed = True

    last_state = current_state
    return direction
#encoder_value if changed else None


def show_menu():
    oled.fill(0)
    for index, item in enumerate(menu_items):
        if index == current_menu_index:
            oled.text("> " + item, 0, index * 10)
        else:
            oled.text("  " + item, 0, index * 10)
    oled.show()

# enumerate allows to loop over a list etc.:)

def main():
    global current_menu_index

# global means using the current "state" not a local onr
    while True:
        show_menu()

        # Read encoder
#         new_val = read_encoder()
#         if new_val is not None:
#             current_menu_index = new_val
        direction = read_encoder()
        if direction != 0:
            current_menu_index += direction
            current_menu_index %= len(menu_items)

        # Button press
        if button.value() == 0:
            time.sleep_ms(200)  # debounce

            if current_menu_index == 0:
                start_hrv()
            elif current_menu_index == 1:
                print("Stopped")
            elif current_menu_index == 2:
                print_hvr_data()
            elif current_menu_index == 3:
                break

        time.sleep_ms(5)


def start_hrv():
    print("Collecting HRV data for 30 seconds...")
    time.sleep(2)
    heart_rate_data = collect_heart_rate_data(30)
    calculate_hrv(heart_rate_data)


def collect_heart_rate_data(seconds=30):
    heart_rate_data = []
    start_time = time.time()

    while time.time() - start_time < seconds:
        heart_rate_data.append(60 + (time.time() % 3))
        time.sleep(0.5)

    return heart_rate_data


def calculate_hrv(data):
    n = len(data)
    avg_hr = sum(data) / n

    ppi = [60 / hr for hr in data]
    mean_ppi = sum(ppi) / len(ppi)

    rmssd = 0
    for i in range(1, len(ppi)):
        rmssd += (ppi[i] - ppi[i - 1]) ** 2
    rmssd = (rmssd / (len(ppi) - 1)) ** 0.5

    sdnn = (sum([(x - mean_ppi) ** 2 for x in ppi]) / len(ppi)) ** 0.5

    print(f"Mean HR: {avg_hr:.2f}")
    print(f"Mean PPI: {mean_ppi:.2f}")
    print(f"RMSSD: {rmssd:.2f}")
    print(f"SDNN: {sdnn:.2f}")

#NOT ACTUAL DATA, JUST MATH CAUSE I NEED PULSE SENSOR
def print_hvr_data():
    print("Displaying HRV data...")


main()