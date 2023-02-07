import json
import math
import time
from machine import Pin, PWM
from tm1637 import TM1637

PIN_DIO = 11
PIN_CLK = 12
PIN_LED_RED = 13
PIN_LED_YELLOW = 14
PIN_LED_GREEN = 15
PIN_BUTTON_GREEN = 16
PIN_BUTTON_RED = 17
PIN_RELAY = 18
PIN_BUZZER = 19

CONFIG_PATH = 'config.json'

with open(CONFIG_PATH) as config_file:
    config_data = json.load(config_file)

TIME_TO_COUNTDOWN_SECS = config_data['countdown_time_secs']
TIME_TO_COUNTDOWN_SECS_MIN = config_data['min_countdown_time_secs']
TIME_TO_COUNTDOWN_SECS_MAX = config_data['max_countdown_time_secs']
TIME_TO_INCREMENT_SECS = config_data['increment_time_secs']
TIME_RUNNING_OUT_SECS = config_data['running_out_time_secs']
DEBOUNCING_TIME_SECS = config_data['debouncing_time_secs']

relay = Pin(PIN_RELAY, Pin.OUT)
led_green = Pin(PIN_LED_GREEN, Pin.OUT)
led_yellow = Pin(PIN_LED_YELLOW, Pin.OUT)
led_red = Pin(PIN_LED_RED, Pin.OUT)
button_green = Pin(PIN_BUTTON_GREEN, Pin.IN, Pin.PULL_UP)
button_red = Pin(PIN_BUTTON_RED, Pin.IN, Pin.PULL_UP)
screen = TM1637(Pin(PIN_CLK), Pin(PIN_DIO))
buzzer = PWM(Pin(PIN_BUZZER))

button_green_state = False
button_red_state = False
both_clicked = False

programming_mode = False
proceed_countdown = False

is_buzzer_done = False

led_green.low()
led_yellow.low()
led_red.low()

buzzer.freq(1200)

time_start = 0
time_ellapsed = 0


while True:
    if not programming_mode:
        if not button_red.value() and not button_green.value():
            button_green_state = True
            button_red_state = True
            both_clicked = True
        if button_red.value() and button_green.value() and both_clicked:
            button_green_state = False
            button_red_state = False
            both_clicked = False
            programming_mode = True
            time.sleep(DEBOUNCING_TIME_SECS)
            continue
        if not button_green.value() and button_green_state is False:
            button_green_state = True
        if button_green.value() and button_green_state is True:
            button_green_state = False
            proceed_countdown = True
            time_start = time.time()
            time.sleep(DEBOUNCING_TIME_SECS)
        if not button_red.value() and button_red_state is False:
            button_red_state = True
        if button_red.value() and button_red_state is True:
            button_red_state = False
            proceed_countdown = False
            time.sleep(DEBOUNCING_TIME_SECS)

        if proceed_countdown:
            time_ellapsed = math.ceil(time.time() - time_start)
            time_to_countdown = TIME_TO_COUNTDOWN_SECS - time_ellapsed
        else:
            time_to_countdown = 0

        if time_to_countdown < 0:
            time_to_countdown = 0

        if time_to_countdown > TIME_RUNNING_OUT_SECS:
            is_buzzer_done = False
            if not led_green.value(): led_green.high()
            if not relay.value(): relay.high()
            if led_yellow.value(): led_yellow.low()
            if led_red.value(): led_red.low()
        elif time_to_countdown > 0:
            if not led_yellow.value(): led_yellow.high()
            if not relay.value(): relay.high()
            if led_green.value(): led_green.low()
            if led_red.value(): led_red.low()
            if not is_buzzer_done:
                for _ in range(3):
                    buzzer.duty_u16(65535)
                    time.sleep_ms(100)
                    buzzer.duty_u16(0)
                    time.sleep_ms(100)
                is_buzzer_done = True
        else:
            is_buzzer_done = False
            if not led_red.value(): led_red.high()
            if relay.value(): relay.low()
            if led_green.value(): led_green.low()
            if led_yellow.value(): led_yellow.low()

        mins_to_show = int(time_to_countdown / 60)
        secs_to_show = int(time_to_countdown % 60)

        screen.numbers(mins_to_show, secs_to_show)
    else:
        if led_green.value(): led_green.low()
        if led_yellow.value(): led_yellow.low()
        if led_red.value(): led_red.low()
        if relay.value(): relay.low()

        time_to_countdown = TIME_TO_COUNTDOWN_SECS

        mins_to_show = int(time_to_countdown / 60)
        secs_to_show = int(time_to_countdown % 60)

        if time.time() - time_start < 1: 
            screen.numbers(mins_to_show, secs_to_show)
        else:
            screen.show('    ')
            time.sleep(0.2)
            time_start = time.time()

        if not button_red.value() and not button_green.value():
            button_green_state = True
            button_red_state = True
            programming_mode = False
            config_data['countdown_time_secs'] = TIME_TO_COUNTDOWN_SECS
            with open(CONFIG_PATH, 'w') as config_file:
                json.dump(config_data, config_file)
            time_start = 0
            time.sleep(1)
            continue
        if not button_green.value() and button_green_state is False:
            button_green_state = True
            time.sleep(DEBOUNCING_TIME_SECS)
        if button_green.value() and button_green_state is True:
            button_green_state = False
            TIME_TO_COUNTDOWN_SECS += TIME_TO_INCREMENT_SECS
            if TIME_TO_COUNTDOWN_SECS > TIME_TO_COUNTDOWN_SECS_MAX:
                TIME_TO_COUNTDOWN_SECS = TIME_TO_COUNTDOWN_SECS_MAX
        if not button_red.value() and button_red_state is False:
            button_red_state = True
            time.sleep(DEBOUNCING_TIME_SECS)
        if button_red.value() and button_red_state is True:
            button_red_state = False
            TIME_TO_COUNTDOWN_SECS -= TIME_TO_INCREMENT_SECS
            if TIME_TO_COUNTDOWN_SECS < TIME_TO_COUNTDOWN_SECS_MIN:
                TIME_TO_COUNTDOWN_SECS = TIME_TO_COUNTDOWN_SECS_MIN
