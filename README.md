# VIRTUINO
 Visualisation HMI Virtuino ( http://virtuino.com/ ) API using Asyncio & MicroPython Virtuino_CM protocol
 
 V = VIRTUINO( key = None, cb = None, refresh = 1000, host = '0.0.0.0', port='8000', timeout=20)

	key - ключ, при несовпадении полученного и заданного возвращается пустая строка 

	cb( owner, pin, value, ask ) - функция, исполняемая после получения сообщения от owner - Клиента V-Пина pin со значением value в текстовом представлении перед его передачей обратно Клиенту

	ask - логическое значение, означающее наличие запроса от Клиента (телефона, планшета)

	refresh - период обновления (1 сек по умолчанию)

	host,port,timeout - параметру asyncio TCP-сервера

Помимио использования функции cb(), можно непосредственно получать значения и состояния V-пинов

v = V(pin)              - считать значение в текстовом формате
v = V(pin,value)    - записать значение в Vpin
if V.changed(pin): - проверить состояние, после создания/записи/обновления True, после считывания значения False

Дополнительно

V.store('filename')    - сохранить реестр V-пинов в filename.dat на FLASH
V.restore('filename') - восстановить реестр V-пинов из filename.dat на FLASH
