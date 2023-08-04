import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# set up ultrasonic sensor
GPIO.setup(25,GPIO.OUT) # sending signal
GPIO.setup(27,GPIO.IN) # receiving signal

# set up buzzer
GPIO.setup(18,GPIO.OUT)
buzzer_pwm = GPIO.PWM(18, 100)

def distance():
    GPIO.output(25,1) 
    time.sleep(0.00001)
    GPIO.output(25,0)

    #measure pulse width (i.e. time of flight) at Echo
    StartTime=time.time()
    StopTime=time.time()
    
    while GPIO.input(27)==0:
        StartTime=time.time() #capture start of high pulse
        
    while GPIO.input(27)==1:
        StopTime=time.time() #capture end of high pulse
        
    ElapsedTime=StopTime-StartTime

    #compute distance in cm, from time of flight
    Distance=(ElapsedTime * 34300)/2
       #distance=time*speed of ultrasound,
       #/2 because to & fro
    return Distance

def scale_value(distance, min_dist, max_dist):
    '''
    scales distance value such that the lower the distance,
    the higher the scaled value will be for the buzzer
    '''
    scaled_value = (max_dist - distance) / max_dist * 100
    return scaled_value

def detect_object():
    dist = distance()
    buzzer_pwm.start(0)
            
    if 0.0 < dist <= 20.0:
        buzzer_value = scale_value(dist, 0.0, 20.0)
        buzzer_pwm.start(buzzer_value)
        print(f'Object detected at {dist:.3f}cm, Buzzer value: {buzzer_value:.3f}')

    time.sleep(.2)
    
'''  
try:
    while (True):
        detect_object() 
            
except KeyboardInterrupt:
    buzzer_pwm.start(0)
'''










        
