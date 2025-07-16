"""
This is for testing on a small grid, it will be deleted
"""

import board
import time
import busio
i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
ads = ADS.ADS1115(i2c)
while not i2c.try_lock():
    pass
i2c.unlock()

chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

chan0_initial = 0
chan1_initial = 0
chan2_initial = 0
chan3_initial = 0
time.sleep(1) #Allow voltage to stabilise through sensors
initial_time = time.time()

print("Inititalizing System")
print("Prepare to be impressed")
print("")
counter=0
#Calibrate initial values for each sensors for comparison
while (time.time()-initial_time)<10:
    chan0_initial = chan0_initial+chan0.voltage
    chan1_initial = chan1_initial+chan1.voltage
    chan2_initial = chan2_initial+chan2.voltage
    chan3_initial = chan3_initial+chan3.voltage
    counter=counter+1
    time.sleep(0.2)

chan0_initial = chan0_initial/counter
chan1_initial = chan1_initial/counter
chan2_initial = chan2_initial/counter
chan3_initial = chan3_initial/counter

chan_initial = [chan0_initial,chan1_initial,chan2_initial,chan3_initial]

dist_thresh = 0.1 #Change in voltage before system reacts
x_dist = 30 #distance between senors in mm

print("chan0 initial voltage: ", chan_initial[0])
print("chan1 initial voltage: ", chan_initial[1])
print("chan2 initial voltage: ", chan_initial[2])
print("chan3 initial voltage: ", chan_initial[3])
print("")


#Calibrate Max Values of Sensors
chan0_max = 0
chan1_max = 0
chan2_max = 0
chan3_max = 0
print("Place Magnet above sensor 0 to calibrate max")
print("")
time.sleep(5)
print("Calibrating")
counter=0
initial_time = time.time()
while (time.time()-initial_time)<5:
    chan0_max = chan0_max+chan0.voltage
    counter=counter+1
    time.sleep(0.2)
chan0_max = chan0_max/counter

print("Place Magnet above sensor 1 to calibrate max")
print("")
time.sleep(5)
print("Calibrating")
counter=0
initial_time = time.time()
while (time.time()-initial_time)<5:
    chan1_max = chan1_max+chan1.voltage
    counter=counter+1
    time.sleep(0.2)
chan1_max = chan1_max/counter

print("Place Magnet above sensor 2 to calibrate max")
print("")
time.sleep(5)
print("Calibrating")
counter=0
initial_time = time.time()
while (time.time()-initial_time)<5:
    chan2_max = chan2_max+chan2.voltage
    counter=counter+1
    time.sleep(0.2)
chan2_max = chan2_max/counter

print("Place Magnet above sensor 3 to calibrate max")
print("")
time.sleep(5)
print("Calibrating")
counter=0
initial_time = time.time()
while (time.time()-initial_time)<5:
    chan3_max = chan3_max+chan3.voltage
    counter=counter+1
    time.sleep(0.2)
chan3_max = chan3_max/counter

chan_max = [chan0_max,chan1_max,chan2_max,chan3_max]

volt_thresh = 0.1 #Change in voltage before system reacts
x_dist = 35 #distance between senors in mm

print("chan0 initial voltage: ", chan_initial[0])
print("chan1 initial voltage: ", chan_initial[1])
print("chan2 initial voltage: ", chan_initial[2])
print("chan3 initial voltage: ", chan_initial[3])
print("")

print("System Initialized")
print("")



def magnetDist(chan_initial,chan_max,chan0,chan1,chan2,chan3,x_dist,volt_thresh):
    #Check 3 largest sensor changes
    chan_changes = [chan0.voltage-chan_initial[0],chan0.voltage-chan_initial[1],chan0.voltage-chan_initial[2],chan0.voltage-chan_initial[3]] 
    

    return None

while True:
    chan_voltage = [chan0.voltage,chan1.voltage,chan2.voltage,chan3.voltage]
    print('Channel 0 ', 'Voltage: ', chan_voltage[0])
    print('Channel 1 ','Voltage: ', chan_voltage[1])
    print('Channel 2 ', 'Voltage: ', chan_voltage[2])
    print('Channel 3 ','Voltage: ', chan_voltage[3])
    print("")
    #print('Channel 2: ','Value: ',chan2.value, 'Voltage: ', chan2.voltage)
    #print('Channel 3: ','Value: ',chan3.value, 'Voltage: ', chan3.voltage)
    
    magnetDist(chan_initial,chan_max,chan0,chan1,chan2,chan3,x_dist,volt_thresh)