import math
import adxl345
from time import sleep
from RPi import GPIO

# set up ir sensor
GPIO.setmode(GPIO.BCM) #choose BCM mode
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.IN) # set GPIO 17 as input

# set up acclerometer
ADDRESS = 0x53
acc = adxl345.ADXL345(i2c_port=1,address=ADDRESS) #instantiate
acc.load_calib_value() #load calib. values in accel_calib
acc.set_data_rate(data_rate=adxl345.DataRate.R_100) #see datasheet
acc.set_range(g_range=adxl345.Range.G_16,full_res=True)
acc.measure_start()

# set threshold value
threshold: int = 0.5

print('starting...')
sleep(5) # to allow sensor time to stabilize

try:
       print('recording values...')
       while(True):
              x, y, z = acc.get_3_axis_adjusted()
              magnitude = math.sqrt(x**2 + y**2 + z**2)
              # print(magnitude)
              motion_detected: bool = not GPIO.input(17)
              
              if (magnitude > threshold) and motion_detected:
                     print('collision detected')
              else:
                     print('no collision')
              
              sleep(.2)
except KeyboardInterrupt:
       print('ended')
       
       
