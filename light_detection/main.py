import spidev #import SPI library
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#setting up the LED
GPIO.setup(24,GPIO.OUT)
led_pwm = GPIO.PWM(24, 100)

spi=spidev.SpiDev() #create SPI object
spi.open(0,0) #open SPI port 0, device (CS) 0

def readadc(adcnum):
    #read SPI data from the MCP3008, 8 channels in total
    if adcnum>7 or adcnum<0:
        return -1
    spi.max_speed_hz = 1350000
    r=spi.xfer2([1,8+adcnum<<4,0])
        #construct list of 3 items, before sending to ADC:
        #1(start), (single-ended+channel#) shifted left 4 bits, 0(stop)
        #see MCP3008 datasheet for details
    data=((r[1]&3)<<8)+r[2]
        #ADD first byte with 3 or 0b00000011 - masking operation
        #shift result left by 8 bits
        #OR result with second byte, to get 10-bit ADC result
    return data

def brightness_value(brightness, min_brig, max_brig):
    '''
    scales brightness value such that the lower the brightness,
    the higher the scaled value will be for the LED, ie darker area,
    LED becomes brighter
    '''
    brightness_value = ((max_brig - brightness) / (max_brig - min_brig)) * 100
    brightness_value = max(0, min(brightness_value, 100))
    return brightness_value
try:   
    while (True):
        LDR_value=readadc(0) #read ADC channel 0 i.e. LDR
        LED_value = brightness_value(LDR_value, 0 , 100)
        led_pwm.start(LED_value)
                
        sleep(.2)

except KeyboardInterrupt:
    led_pwm.start(0)


