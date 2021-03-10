# VIRTUINO.py VIRTUINO CM driver 
#
# Released under the MIT licence
# Copyright (c) @ZolAnd 2021
# 01/01 creation
# 12/01 add asyncio v.3.0 server
#
# Based on userver.py Demo of simple uasyncio-based echo server
# Released under the MIT licence
# Copyright (c) Peter Hinch 2019-2020

import usocket as socket
import uasyncio as asyncio
import uselect as select

_verbose = True


################################################################## INTERNAL CONSTANTS
_CH_START = '!'
_CH_STOP  = '$'
_CH_ASK   = '?'
_CH_NONE  = ''

_VALUE   = 0
_CHANGED = 1


################################################################## CM:: CLASS
class CM():
    
    def __init__( self, cb=None, key=None, max_buf=256, host='0.0.0.0', port=8000, backlog=5, timeout=20, refresh = 1000 ):
        
        self.V_key = key
        # callback proc cb(pin,value,ask) - called when Vpin detected by _parser
        # ask = True if '?' received from VIRTUINO, Vpin[_VALUE]=old.value
        # if old.value != new.value, received from VIRTUINO, Vpin '_CHANGED' state True  
        # MUST return accepted value str type
        self.cb = cb if cb else self._cb # internal callback
        self.max_buf = max_buf
        self.answer = key if key else '' # start protocol ANSWER MESSAGE
        self.V = {} # ctreate VIRTUINO Virtual PINs dictionary PIN:value,changed,callback
        # async server parameters
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout # waiting read
        self.refresh = refresh # server refresh time


################################################################## CM::ERROR HANDLER

    def _info(self,*param):
        if len(param) == 2 :
            print('[{}] {}'.format(param[0],param[1]))
        else:
            print('[!] BAD PARAMETER')
        return True


################################################################## CM::_cb
    def _cb(self,owner,pin,value,ask):
        '''
        :> owner - client's IP
        :> pin   - index of V, string
        :> value - any type converted to string inside
        :> ask   - if VIRTUINO send '?' True
        <: accepted by user value
        '''
        if ask: # ask confirmation for the current value
            val = value
        return value


################################################################## CM::store
    def store(self,file_name):
        # upload DataBase content from memory to storage (FLASH or SD)
        file = open(file_name+'.dat','wb')
        file.write(repr(self.V))
        file.close()


################################################################## CM::restore
    def restore(self,file_name):
        # download DataBase content from storage (FLASH or SD) to memory
        try:
            file = open(file_name+'.dat','rb')
        except OSError: # createif not exist
            print('[i] VIRTUINO no saved data')
            return False
        else:
            obj = file.read()
            file.close()
            self.V = eval(obj.decode(), {})
        return True

################################################################## CM::changed
    def changed(self,pin):
        '''
        :> pin - index of V, string
        <: True/False
        '''
        return self.V[pin][_CHANGED]


################################################################## CM::__call__
    def __call__(self,pin,value=None):
        '''
        :> pin - index of V, string
        :> value - any type converted to string inside
        <: value in string represenrtation

        if no value - return current 'value' and _CHANGED = False
        if value - cpreate/set 'str(value)' to V register
        if value == '?' - uplate answer PAYLOAD to VIRTUINO and _CHANGED = False
        if value changed - flag _CHANGED set True
        '''
        value = _CH_NONE if value == None else str(value)
        
        if pin in self.V: 
            self.V[pin][_CHANGED] = False
        else: # create new Vpin
            self.V[pin] = [_CH_NONE if value == _CH_ASK else value,True]
            self._info('!','New V{'+pin+'} created '+value)

        if value == _CH_ASK: # ASK value
            self.answer += _CH_START+'V'+pin+'='+_CH_ASK+_CH_STOP
        elif value != _CH_NONE and self.V[pin][_VALUE] != value: # SET value
            self.V[pin] = [value,True]

        return self.V[pin][_VALUE]


################################################################## CM::PARSER
    def _parser( self, owner, payload ):
        '''
        format vs NO KEY - !V{0..255}={value}$ ... 
        format vs KEY    - {key}!V{0..255}={value}$ ... 

        there is only one type of vars - V[IRTUAL]
        if KEY wrong - return empty answer
        if V not defined - create new V with value 'None'
        
        There we just update answer payload, created by local calls V(pin,'?')
        If '?' received from Virtuino
        '''        
        cmd_set = payload.split(_CH_START)
        
        _verbose and print()
        _verbose and print('[D]          PAYLOAD ',cmd_set)

        if cmd_set[0] or self.V_key: # CHECK KEY
            _verbose and print('[D] RECEIVED KEY: ',cmd_set[0]) 
            if self.V_key == cmd_set[0]:
                self._info('X','CORRECT KEY {}'.format(self.V_key))
            else:
                self._info('X','WRONG KEY {}'.format(self.V_key))
                return ''
        del cmd_set[0] # remove unnessesary command

        ########################################################
        for cmd in cmd_set:
            if not '=' in cmd: continue # noise, wrong cmd

            parse = cmd[1:].split('=') # remove command type 'V'
            pin   = parse[0]           # index string
            sval  = parse[1][:-1]      # value string without _CH_CLOSE

            if not pin in self.V: # create new Vpin
                self.V[pin] = [_CH_NONE if sval == _CH_ASK else sval,True]
                self._info('!','New V{'+pin+'} created '+sval)

            if sval == _CH_ASK: # there is only old value and ask to update it
                value = self.cb( owner, pin, self.V[pin][_VALUE], True ) if self.cb else self.V[pin][_VALUE]
                sval = str(value)
                self.answer += _CH_START+'V'+pin+'='+sval+_CH_STOP # set ANSWER to VIRTUINO                
            else:
                value = self.cb( owner, pin, sval, False ) if self.cb else sval
                sval = str(value)

            if sval != self.V[pin][_VALUE]:
                self.V[pin] = [sval,True]
            else:
                self.V[pin][_CHANGED] = False

        _verbose and print('[D]          ANSWER  ',self.answer)
        _verbose and print()
        
        return self.answer


################################################################## CM::TCP CLIENT
    async def run_client(self, sreader, swriter):

        self.cid = (self.cid+1)%13 # limit num of connections
        _verbose and print('[D] Client {} start'.format(self.cid))
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(sreader.read(self.max_buf), self.timeout)
                except asyncio.TimeoutError:
                    payload = b''
                if payload == b'':
                    raise OSError
                res = payload.decode()
                addr = swriter.get_extra_info('peername')
                _verbose and print('[D] Received {} from client {}:{}'.format(res, self.cid, addr))
                swriter.write(self._parser(addr,res) )
                self.answer = self.V_key if self.V_key else '' # restart protocol ANSWER       
                await swriter.drain()  # Echo back
        except OSError:
            pass
#        _verbose and print('Client {} stop'.format(self.cid))
        await sreader.wait_closed()
#        _verbose and print('Client {} closed.'.format(self.cid))


################################################################## CM::close
    async def close(self):
        _verbose and print('[D] Closing server')
        self.server.close()
        await self.server.wait_closed()
        self._info('!','Server closed')


################################################################## CM::TCP SERVER
    async def run(self, u_proc=None, tms=0 ): # run server
        
        print('Awaiting client connection.')
        self.cid = 0
        #asyncio.create_task(sys_proc(u_proc,tms))
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)

        while True:
            await asyncio.sleep(self.refresh)


################################################################## RUN

def RUN(v):
    try:
        asyncio.run(v.run())
    except KeyboardInterrupt:
        print('Interrupted')  # This mechanism doesn't work on Unix build.
    finally:
        asyncio.run(v.close())
        _ = asyncio.new_event_loop()

