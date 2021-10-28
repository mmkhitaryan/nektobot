#!/usr/bin/env python

import json
import asyncio
import websockets
import time
import random

class NektoRoulette():
    def __init__(self, myid, token, who_to_send_instance=None) -> None:
        self.who_to_send_instance = who_to_send_instance
        self.token=token
        self.myid=myid

    def get_message_id(self, user_id):
        getTime = int(time.time()*1000)

        return f'{user_id}_{getTime}'

    async def pinger(self):
        while True:
            await self.websocket.send("2")
            await asyncio.sleep(20)

    async def leave_dialog(self):
        leave_message = '42["action",{"action":"anon.leaveDialog","dialogId":'+self.dialog_id+'}]'
        await self.websocket.send(leave_message)

    async def send_message(self, answer_text):
        answer_message = '42["action",{"action":"anon.message","dialogId":'+self.dialog_id+',"message":"' + answer_text + '","randomId":"'+self.get_message_id(self.id_user)+'"}]'
        await self.websocket.send(answer_message)

    async def new_dialog(self):
        async with websockets.connect("wss://im.nekto.me/socket.io/?EIO=3&transport=websocket", ping_timeout=None) as websocket:
            self.websocket = websocket

            resp = await self.websocket.recv()
            resp = await self.websocket.recv()
            await self.websocket.send('42["action",{"action":"auth.sendToken","token":"'+self.token+'"}]')
            resp = await self.websocket.recv()
            self.id_user = json.loads(resp[2:])[1]["data"]["id"]

            # 42["action",{"isAdult":true,"myAge":[18,29],"mySex":"M","wishAge":[[18,29]],"action":"search.run"}]
            # 42["action",{"myAge":[0,17],"mySex":"M","action":"search.run"}]
            await self.websocket.send('42["action",{"myAge":[0,17],"mySex":"M","action":"search.run"}]')

            resp = await self.websocket.recv()

            data = json.loads(resp[2:])[1]['data']
            if data_id := data.get('id'):
                if data_id == 600:
                    # https://rucaptcha.com/in.php?key=f01d5fb2f18efbf68f3e49719cbdf553&method=userrecaptcha&googlekey=6LdOeRgUAAAAAPasL5PFtQ_sfet2JVhaeH01I_o2&pageurl=https://nekto.me/chat#/anon
                    # OK|50978343107

                    # https://rucaptcha.com/res.php?key=f01d5fb2f18efbf68f3e49719cbdf553&json=1&&action=get&id=50978343107
                    # {"status":1,"request":"03AGdBq25YENfyvXE0j-XM5xOr9kfGuYYb1MAtn8CxbFr36EN_YxMa6VlomFp5YQrl-tE3SXCT7ZO5vQXVsBFK6w6xWix-DhCLLlQa4D3wpbAAsUfF0iIyHj7H6JPPYKh_GbYRgETt98k5_VK0ffl4g9SnywG98KKdCsMGBMUhRr7Hob6JY6o-Ifns2UrJEbWnuup4K2QEon3vflWxHgvmHm7y_7J6Ya0qjQWp5AQ1wTs6bTEjy8N-6d92158GQ9rTDyJE4orRT5evplZSIwi-uxHxLW8z365RiahixYLQA_UU1Y_uxEVPDvPfjpQXX3BV_nZXm2b_Gf_PEHquO2lh8oFe-otjHa2VojDD1eBREQ3gSBeiGZuzhRH-2MbOlTRGEun-moMpNoFhOjKMEzUFsUGoXA_532m0A3ymIOR-Yd46bUj69XAihD-OtguFEAnUEEVXznCKWSqSYXTTgbp3eNjfYWWfyDXjmCa7Iq5Dmi7y_vt7F4rEPgZkbfbHefAFBr1gJ1ekY9aM5v45j7dL9RSWVDWB4vKsZA"}
                    print("Каптчу выбило блять")
                    # solve 42["action",{"action":"captcha.verify","solution":"03AGdBq2607oBhoB9O1IdZt5oqM2gDU5MxpfDYD7LFV7dDI7HFqe-tjPWD9-9bPHgyxuduvZysI0u6GbBw6VYgZgMPhhJ3NiRQE6fX6mmrXBOuuydlp10gRyMyf1zKcZJhGe-tzJJHGy47p8cl7xAHOOV4l_fud1709tNOVIMTTHXmc6X8EFYgs9kkxn8L11S7pyT4ssm5IV7UfkliPxoisAUJV4bTvNHbrHagUMOSS9Q5Xtqchuwf2sFztCBcQVVq4j2-nBvmsHXsWuGZaQaQr1gNxlTx7_7oxSkSsHxFx0mTr9cpXjjg7Rh_7IfrDzeYZNQlq2kNEoPubc9PeKfVdoiMkCp1H8z02yngnnC1wYbtlsNh8Vt5hgw47jKoCUgcEq1OMQ-lyDCo2dbINtnwBLrJ8pV0dqCo6rwQULN6ryRrmY6UoAaJA1WF4gHSthqfq1GtCzXibhMd","hard":false}]
                    await self.websocket.close()

            resp = await self.websocket.recv()
            self.dialog_id = str(json.loads(resp[2:])[1]["data"]["id"])

            asyncio.create_task(self.pinger())

            while True:
                resp = await self.websocket.recv()
                if resp != "3": # если это просто понг
                    data = json.loads(resp[2:])[1]
                    if data_message := data.get('data'):
                        if is_typing := data_message.get("typing"):
                            # print(f"Пишет: {is_typing}")
                            pass

                        if read_messages := data_message.get("reads"): # лист айдишников прочитаных сообщений 
                            # print(f"Прочитал сообщение {read_messages}")
                            pass

                        if dialog_closed := data_message.get("close"):
                            print(f"Диалог закрыт ливаю")
                            await self.who_to_send_instance.leave_dialog()
                            await self.websocket.close()
                    
                        if message_text := data_message.get("message"):
                            if self.id_user!=data_message.get("senderId"):
                                incomming_message_id = data_message['id']
                                await self.websocket.send( # прочел типо
                                '42["action",{"action":"anon.readMessages","dialogId":' + self.dialog_id + ',"lastMessageId":' + str(incomming_message_id) + '}]'
                                )

                                await self.websocket.send( # пишу типо
                                '42["action",{"action":"dialog.setTyping","dialogId":' + self.dialog_id + ',"typing":true}]'
                                )
                                print(f'{self.myid}: {message_text}')

                                await self.who_to_send_instance.send_message(message_text)

                                await self.websocket.send( # написал типо
                                '42["action",{"action":"dialog.setTyping","dialogId":' + self.dialog_id + ',"typing":false}]'
                                )

                                if False:
                                    if answer_text:
                                        print(answer_text)
                                        if answer_text=='пок':
                                            leave_message = '42["action",{"action":"anon.leaveDialog","dialogId":'+dialog_id+'}]'
                                            await self.websocket.send(leave_message)
                                            print("Послал нах")
                                            break
                                        else:
                                            answer_message = '42["action",{"action":"anon.message","dialogId":'+dialog_id+',"message":"' + answer_text + '","randomId":"'+self.get_message_id(id_user)+'"}]'
                                            await self.websocket.send(answer_message)

async def hello():
    first_nekto_client = NektoRoulette('marat', "e94eee7259b432d4fccb599a0c1a10aac2b22836ad00dd82e4240af337ce8505")
    second_nekto_client = NektoRoulette('softer', "65191928a660f87a33c460893ac58d21249d19971ebda6e01838eb39a1feeac4", first_nekto_client)
    first_nekto_client.who_to_send_instance = second_nekto_client

    await asyncio.gather(
        *(
            first_nekto_client.new_dialog(), 
            second_nekto_client.new_dialog()
        )
    )



if __name__ == '__main__':
    asyncio.run(hello())
