from fifo import Fifo
from sampling import fifo

# created a list for the signal to go into and then read the data from the fifo and added it to the signal list
signal = []

while True:
    if fifo.has_data():
        data = fifo.get()
        signal.append(data)
    else:
        pass
