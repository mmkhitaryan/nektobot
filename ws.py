#!/usr/bin/env python

import json
import asyncio
import websockets
import time
import random

def get_message_id(user_id):
    getTime = int(time.time()*1000)

    return f'{user_id}_{getTime}'

async def pinger(websocket):
    while True:
        await websocket.send("2")
        await asyncio.sleep(20)

async def hello():
    async with websockets.connect("wss://im.nekto.me/socket.io/?EIO=3&transport=websocket", ping_timeout=None) as websocket:
        resp = await websocket.recv()
        resp = await websocket.recv()
        await websocket.send('42["action",{"action":"auth.sendToken","token":"e94eee7259b432d4fccb599a0c1a10aac2b22836ad00dd82e4240af337ce8505"}]')
        resp = await websocket.recv()
        id_user = json.loads(resp[2:])[1]["data"]["id"]

        await websocket.send('42["action",{"myAge":[0,17],"mySex":"M","action":"search.run"}]')
        resp = await websocket.recv()

        data = json.loads(resp[2:])[1]['data']
        if data_id := data.get('id'):
            if data_id == 600:
                print("Каптчу выбило блять")
                # solve 42["action",{"action":"captcha.verify","solution":"03AGdBq2607oBhoB9O1IdZt5oqM2gDU5MxpfDYD7LFV7dDI7HFqe-tjPWD9-9bPHgyxuduvZysI0u6GbBw6VYgZgMPhhJ3NiRQE6fX6mmrXBOuuydlp10gRyMyf1zKcZJhGe-tzJJHGy47p8cl7xAHOOV4l_fud1709tNOVIMTTHXmc6X8EFYgs9kkxn8L11S7pyT4ssm5IV7UfkliPxoisAUJV4bTvNHbrHagUMOSS9Q5Xtqchuwf2sFztCBcQVVq4j2-nBvmsHXsWuGZaQaQr1gNxlTx7_7oxSkSsHxFx0mTr9cpXjjg7Rh_7IfrDzeYZNQlq2kNEoPubc9PeKfVdoiMkCp1H8z02yngnnC1wYbtlsNh8Vt5hgw47jKoCUgcEq1OMQ-lyDCo2dbINtnwBLrJ8pV0dqCo6rwQULN6ryRrmY6UoAaJA1WF4gHSthqfq1GtCzXibhMd","hard":false}]
                return

        resp = await websocket.recv()
        dialog_id = str(json.loads(resp[2:])[1]["data"]["id"])
        
        asyncio.create_task(pinger(websocket))

        while True:
            resp = await websocket.recv()
            if resp != "3": # если пинг ответ от сервера то нам пох
                data = json.loads(resp[2:])[1]
                if data_message := data.get('data'):
                    if is_typing := data_message.get("typing"):
                        # print(f"Пишет: {is_typing}")
                        pass

                    if read_messages := data_message.get("reads"): # лист айдишников прочитаных сообщений 
                        # print(f"Прочитал сообщение {read_messages}")
                        pass

                    if read_messages := data_message.get("close"): # лист айдишников прочитаных сообщений 
                        print(f"Диалог закрыт")
                        break
                
                    if message_text := data_message.get("message"):
                        if id_user!=data_message.get("senderId"):
                            incomming_message_id = data_message['id']
                            await websocket.send( # прочел типо
                               '42["action",{"action":"anon.readMessages","dialogId":' + dialog_id + ',"lastMessageId":' + str(incomming_message_id) + '}]'
                            )
                            await websocket.send( # пишу типо
                               '42["action",{"action":"dialog.setTyping","dialogId":' + dialog_id + ',"typing":true}]'
                            )
                            print(message_text)
                            await websocket.send( # написал типо
                               '42["action",{"action":"dialog.setTyping","dialogId":' + dialog_id + ',"typing":false}]'
                            )

                            answer_text = random.choice(["Привет", "Что делаешь", "Как дела?", "Чем займёмся?", "Давай о чем то пошлом", "Ты играешь в игры?", "У тебя есть телеграм?", "Давай пополшим?"])
                            
                            print(answer_text)
                            if answer_text=='пок':
                                leave_message = '42["action",{"action":"anon.leaveDialog","dialogId":'+dialog_id+'}]'
                                await websocket.send(leave_message)
                                print("Послал нах")
                                break
                            else:
                                answer_message = '42["action",{"action":"anon.message","dialogId":'+dialog_id+',"message":"' + answer_text + '","randomId":"'+get_message_id(id_user)+'"}]'
                                await websocket.send(answer_message)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(hello())