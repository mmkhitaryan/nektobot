#!/usr/bin/env python

import json
import asyncio
import websockets
import time
import random
import logging

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.contrib.signaling import object_to_string
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer
from aiortc.sdp import candidate_from_sdp

logger = logging.getLogger('HumioDemoLogger')

logger.setLevel(logging.DEBUG)


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
        audio, _ = create_local_tracks(
            "https://cdn.discordapp.com/attachments/447377030938361867/1032360514216525874/0-3011776416361.mp4", decode=True
        )

        async with websockets.connect("wss://audio.nekto.me/websocket/?EIO=3&transport=websocket", ping_timeout=None) as websocket:
            async def pinger():
                try:
                    while websocket.open:
                        await websocket.send("2")
                        await asyncio.sleep(3)
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
                        initiator = content["initiator"]
                        connectionId = content["connectionId"]

                        stun_url = content['stunUrl']
                        turn_data = json.loads(content['turnParams'])
                        # TODO: set stun/turn settings username and password
                        pc = RTCPeerConnection(
                            RTCConfiguration(iceServers=[
                                RTCIceServer(
                                    urls=turn_data["url"],
                                    username=turn_data["username"],
                                    credential=turn_data["credential"],
                                    credentialType="password"
                                )
                            ])
                        )
                        @pc.on("connectionstatechange")
                        async def on_connectionstatechange():
                            print("Connection state is %s" % pc.connectionState)
                            if pc.connectionState == "failed":
                                await pc.close()
                        
                        @pc.on("icegatheringstatechange")
                        async def on_connectionstatechange():
                            print("Connection state is %s" % pc.signalingState)

                        pc.addTrack(audio)
                        if initiator:
                            print("Init")
                            # generate offer
                            offer = await pc.createOffer()
                            sdp_offer = json.dumps({"sdp":offer.sdp, "type": offer.type}) # json to string if json aiortc returns object
                            await pc.setLocalDescription(offer)
                            await websocket.send('42["event",{"type":"peer-mute","connectionId":"'+connectionId+'","muted":false}]')
                            offer_msg = '42["event",'+json.dumps({"type":"offer","connectionId":connectionId,"offer":sdp_offer})+']'
                            await websocket.send(offer_msg)
                            print("offer"+offer_msg)

                        if not initiator:
                            # just wait for offer, and answer to it
                            await websocket.send('42["event",{"type":"peer-disconnect","connectionId":"'+connectionId+'"}]')
                            break

                    if message_type=="answer":
                        if initiator:
                            answer = RTCSessionDescription(sdp=json.loads(content["answer"])["sdp"], type=json.loads(content["answer"])["type"])
                            await pc.setRemoteDescription(answer)

                            for transceiver in pc.getTransceivers():
                                iceGatherer = transceiver.sender.transport.transport.iceGatherer
                                for candidate in iceGatherer.getLocalCandidates():
                                    candidate.sdpMid = transceiver.mid

                                   #                 42["event",{"type":"ice-candidate","connectionId":"                ","candidate":"{\"candidate\":{\"candidate\":\"candidate:3515631507 1 udp 41819903 95.217.200.121 58261 typ relay raddr 0.0.0.0 rport 0 generation 0 ufrag Op7o network-id 1 network-cost 10\",\"sdpMid\":\"0\",\"sdpMLineIndex\":0}}"}]
                                    candidate_jsoned = json.loads(object_to_string(candidate))
                                    candidate_jsoned['sdpMid'] = "0"
                                    candidate_jsoned['sdpMLineIndex'] = 0
                                    candidate_with_additionals_stringed = json.dumps({"candidate":candidate_jsoned})
                                                                             # candidate should be full string
                                    ice_candidate = '42["event",'+json.dumps({"candidate": candidate_with_additionals_stringed, "connectionId": connectionId, "type":"ice-candidate"})+']'

                                    await websocket.send(ice_candidate)
                        # after webrtc connection
                        # 42["event",{"type":"stream-received","connectionId":"383914732"}]

                        # 42["event",{"type":"peer-disconnect","connectionId":"383914732"}]	


                    # 42["event",{"type":"peer-disconnect","connectionId":"383914732"}]
                    if message_type=="ice-candidate":
                        candidate = candidate_from_sdp(json.loads(content['candidate'])['candidate']['candidate'])

                        info = json.loads(content['candidate'])['candidate']
                        candidate.sdpMid = info['sdpMid']
                        candidate.sdpMLineIndex = info['sdpMLineIndex']

                        await pc.addIceCandidate(candidate)

                
                print(content)

def create_local_tracks(play_from, decode):
    global relay, webcam

    if play_from:
        player = MediaPlayer(play_from, decode=decode)
        return player.audio, player.video
    else:
        options = {"framerate": "30", "video_size": "640x480"}
        if relay is None:
            if platform.system() == "Darwin":
                webcam = MediaPlayer(
                    "default:none", format="avfoundation", options=options
                )
            elif platform.system() == "Windows":
                webcam = MediaPlayer(
                    "video=Integrated Camera", format="dshow", options=options
                )
            else:
                webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            relay = MediaRelay()
        return None, relay.subscribe(webcam.video)

async def hello():
    first_nekto_client = NektoRoulette('marat', "6a7ef640-2369-4992-b249-173587930ab0")

    
    await first_nekto_client.run()

if __name__ == '__main__':
    asyncio.run(hello())
