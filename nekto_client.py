#!/usr/bin/env python

import json
import asyncio
import websockets
import time
import random
import logging
import fractions

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay, PlayerStreamTrack, AudioStream
from aiortc.contrib.signaling import object_to_string
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer
from aiortc.sdp import candidate_from_sdp
from aiortc.contrib.media import MediaPlayer, MediaRecorder
from aiortc.mediastreams import AUDIO_PTIME, MediaStreamError, AudioStreamTrack
from aiortc.codecs.opus import OpusEncoder, SAMPLES_PER_FRAME, TIME_BASE, SAMPLE_RATE
from aiortc.codecs._opus import ffi, lib

from av import AudioFrame, AudioResampler
import av

logger = logging.getLogger('HumioDemoLogger')

logger.setLevel(logging.DEBUG)

frame_queue = asyncio.Queue()
opus_stream_file = open('test.opus', 'wb')

class CustomAudioStreamTrack(AudioStreamTrack):
    _timestamp = 0
    async def recv(self):
        global frame_queue

        print("fasdf7a7dsyfa8s")

        raw_data = await frame_queue.get()

        print("frame creating")
        opus_stream_file.write(raw_data)

        frame = AudioFrame(format="s16", layout="stereo", samples=SAMPLES_PER_FRAME)
        print("instance created")

        try:
            frame.planes[0].update(raw_data)
            print("plane set")
        except Exception as e:
            print(e)

        frame.pts = self._timestamp
        self._timestamp += SAMPLES_PER_FRAME
        print(self._timestamp)

        print("timestamp set")
        frame.sample_rate = SAMPLE_RATE
        print("SAMPLE_RATE set")
        frame.time_base = TIME_BASE
        print("TIME_BASE set")

        print("FRAME SENT")

        frame_queue.task_done()
        return frame

voice_client = None
discord_stream = CustomAudioStreamTrack()

async def custom_run_track(track):
    global voice_client

    while True:
        try:
            frame = await track.recv()
            for plane in frame.planes:
                packet = bytes(plane)
                voice_client.send_audio_packet(packet)
        except MediaStreamError:
            return


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
        assert voice_client != None
        print("start run")
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

                        turn_data = json.loads(content['turnParams'])

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
                            if pc.connectionState == "failed":
                                await pc.close()
                            if pc.connectionState == "connected":
                                await websocket.send('42["event",{"type":"peer-connection","connection":true,"connectionId":"'+connectionId+'"}]')
                        
                        @pc.on("track")
                        async def on_track(track):
                            #if track.kind == "video":
                            #    recorder.addTrack(track)
                            if track.kind == "audio":

                                asyncio.create_task(custom_run_track(track))

                                await websocket.send('42["event",{"type":"stream-received","connectionId":"'+connectionId+'"}]')

                        if initiator:
                            # generate offer
                            pc.addTrack(discord_stream)
                            offer = await pc.createOffer()
                            sdp_offer = json.dumps({"sdp":offer.sdp, "type": offer.type}) # json to string if json aiortc returns object
                            await pc.setLocalDescription(offer)
                            await websocket.send('42["event",{"type":"peer-mute","connectionId":"'+connectionId+'","muted":false}]')
                            offer_msg = '42["event",'+json.dumps({"type":"offer","connectionId":connectionId,"offer":sdp_offer})+']'
                            await websocket.send(offer_msg)

                        if not initiator:
                            # just wait for offer, and answer to it
                            pass

                    if message_type=="offer":
                        if not initiator:
                            remote_offer = RTCSessionDescription(sdp=json.loads(content["offer"])["sdp"], type=json.loads(content["offer"])["type"])
                            await pc.setRemoteDescription(remote_offer)

                            pc.addTrack(discord_stream)
                            
                            localAnswer = await pc.createAnswer()
                            await pc.setLocalDescription(localAnswer)


                            sdp_offer = json.dumps({"sdp":localAnswer.sdp, "type": localAnswer.type}) 

                            offer_msg = '42["event",'+json.dumps({"type":"answer","connectionId":connectionId,"answer":sdp_offer})+']'

                            await websocket.send(offer_msg)


                            for transceiver in pc.getTransceivers():
                                iceGatherer = transceiver.sender.transport.transport.iceGatherer
                                for candidate in iceGatherer.getLocalCandidates():
                                    candidate.sdpMid = transceiver.mid

                                    candidate_jsoned = json.loads(object_to_string(candidate))
                                    candidate_jsoned['sdpMid'] = "0"
                                    candidate_jsoned['sdpMLineIndex'] = 0
                                    candidate_with_additionals_stringed = json.dumps({"candidate":candidate_jsoned})
                                                                             # candidate should be full string
                                    ice_candidate = '42["event",'+json.dumps({"candidate": candidate_with_additionals_stringed, "connectionId": connectionId, "type":"ice-candidate"})+']'

                                    await websocket.send(ice_candidate)

                    if message_type=="answer":
                        if initiator:
                            answer = RTCSessionDescription(sdp=json.loads(content["answer"])["sdp"], type=json.loads(content["answer"])["type"])
                            await pc.setRemoteDescription(answer)

                            for transceiver in pc.getTransceivers():
                                iceGatherer = transceiver.sender.transport.transport.iceGatherer
                                for candidate in iceGatherer.getLocalCandidates():
                                    candidate.sdpMid = transceiver.mid

                                    candidate_jsoned = json.loads(object_to_string(candidate))
                                    candidate_jsoned['sdpMid'] = "0"
                                    candidate_jsoned['sdpMLineIndex'] = 0
                                    candidate_with_additionals_stringed = json.dumps({"candidate":candidate_jsoned})
                                                                             # candidate should be full string
                                    ice_candidate = '42["event",'+json.dumps({"candidate": candidate_with_additionals_stringed, "connectionId": connectionId, "type":"ice-candidate"})+']'

                                    await websocket.send(ice_candidate)

                    # 42["event",{"type":"peer-disconnect","connectionId":"383914732"}]
                    if message_type=="ice-candidate":
                        candidate = candidate_from_sdp(json.loads(content['candidate'])['candidate']['candidate'])

                        info = json.loads(content['candidate'])['candidate']
                        candidate.sdpMid = info['sdpMid']
                        candidate.sdpMLineIndex = info['sdpMLineIndex']

                        await pc.addIceCandidate(candidate)

                    if message_type=="peer-disconnect":
                        await pc.close()
                        await websocket.close()
                        await websocket.wait_closed()
                        print("Left")
                        break
