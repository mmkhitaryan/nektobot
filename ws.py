#!/usr/bin/env python

import json
import asyncio
import websockets
import time
import random

class NektoRoulette():
    def __init__(self, myid, token) -> None:
        self.token=token
        self.myid=myid

    def get_message_id(self, user_id):
        getTime = int(time.time()*1000)

        return f'{user_id}_{getTime}'

    async def leave_dialog(self):
        leave_message = '42["action",{"action":"anon.leaveDialog","dialogId":'+self.dialog_id+'}]'
        await self.websocket.send(leave_message)

    async def send_message(self, answer_text):
        answer_message = '42["action",{"action":"anon.message","dialogId":'+self.dialog_id+',"message":"' + answer_text + '","randomId":"'+self.get_message_id(self.id_user)+'"}]'
        await self.websocket.send(answer_message)

    async def run(self):
        async with websockets.connect("wss://audio.nekto.me/websocket/?EIO=3&transport=websocket", ping_timeout=None) as websocket:
            async def pinger():
                try:
                    while websocket.open:
                        await websocket.send("2")
                        await asyncio.sleep(20)
                except (websockets.exceptions.ConnectionClosedError,
                        asyncio.exceptions.IncompleteReadError):
                    return

            resp = await websocket.recv() # 0{"sid":"f29c8293-feec-456f-a476-481361aae8bb","upgrades":["websocket"],"pingInterval":5000,"pingTimeout":5000}
            resp = await websocket.recv() # 40

            await websocket.send('42["event",{"type":"register","android":false,"version":15,"userId":"'+self.token+'"}]')

            resp = await websocket.recv()
            recaptchaSiteKey = json.loads(resp[2:])[1]['recaptchaSiteKey']
            assert json.loads(resp[2:])[1]['success'] == True

            asyncio.create_task(pinger())

            await websocket.send('42["event",{"type":"scan-for-peer","peerToPeer":true,"searchCriteria":{"peerSex":"ANY","group":0,"userSex":"ANY"},"token":null}]')

            while websocket.open:
                resp = await websocket.recv()

                if resp[0:2] == "42":
                    resp_json = json.loads(resp[2:])
                    content = resp_json[1]


                    message_type = content["type"]
                    if message_type=="search.success":
                        print("found")
                    
                    if message_type=="peer-connect":
                        print("peer-connect:"+str(content))
                        initiator = content["initiator"]
                        connectionId = content["connectionId"]

                        if initiator:
                            # generate offer
                            yield "offer"
                            await websocket.send('42["event",{"type":"answer","connectionId":"'+connectionId+'","answer":"'+self.sdp_offer+'"}"}]')
                        
                        if not initiator:
                            # just wait for offer, and answer to it
                            pass

                        # after webrtc connection
                        # 42["event",{"type":"stream-received","connectionId":"383914732"}]

                        # 42["event",{"type":"peer-disconnect","connectionId":"383914732"}]	


                    if message_type=="offer":
                        self.sdp_answer = content['offer']
                        yield "answer"

                    # 42["event",{"type":"peer-disconnect","connectionId":"383914732"}]                     

async def hello():
    first_nekto_client = NektoRoulette('marat', "6a7ef640-2369-4992-b249-173587930ab0")

    async for data in first_nekto_client.run():
        if data == "offer":
            first_nekto_client.sdp_offer = 'Hello' # json to string if json aiortc returns object
        if data == "answer":
            first_nekto_client.sdp_answer
            # set remote description
            breakpoint()


if __name__ == '__main__':
    asyncio.run(hello())
