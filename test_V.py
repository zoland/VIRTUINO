# test_V.py test VIRTUINO driver 
#
# @ZolAnd 01/2021
#
import uasyncio as asyncio

import WIFI
import VIRTUINO

tick = 10
V_INDICATOR = '10'
V_ANALOG    = '11'
V_BUTTON    = '12'


def update_V( pin, val, ask ):
    # just transfer value for the test
    print('---------- ask {}: V{}={} {} --------------------------'.format(tick,pin,val,ask))

    return val


async def daemon():
    global tick

    while True:
        tick = (tick+1)%10
        V(V_ANALOG,tick)
        V(V_INDICATOR,tick%3)
        if (V.changed(V_BUTTON)):
            print('BUTTON changed')
        print('                                                  sys_proc daemon',V(V_INDICATOR),V(V_ANALOG),V(V_BUTTON))                
        await asyncio.sleep_ms(2000)
        
########################################################

ch = WIFI.WIFI('AP','SM_BURNER','44444444')

V = VIRTUINO.CM(update_V)

V(V_INDICATOR,1)
V(V_ANALOG,  10)
V(V_BUTTON, '?')

asyncio.create_task(daemon())


try:
    asyncio.run(V.run())
except KeyboardInterrupt:
    print('Interrupted')  # This mechanism doesn't work on Unix build.
finally:
    asyncio.run(V.close())
    _ = asyncio.new_event_loop()

#VIRTUINO.RUN( V, user_proc )