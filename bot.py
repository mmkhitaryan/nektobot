import uvloop
import discord

from discord.sinks import Sink
from discord.opus import DecodeManager
import nekto_client
import threading
import time
import gc

bot = discord.Bot()

nekto_instances = {

}

class MySubClassedSink(Sink):
    frames_buffer = []

    def init(self, vc):  # called under listen
        self.vc = vc

        #thread = threading.Thread(target=self.send_all_frames_periodically)
        #thread.start()

    def send_all_frames_periodically(self):
        while not self.finished:
            if len(self.frames_buffer)!=0:
                self.send_all_frames()
                time.sleep(0.1)

    def send_all_frames(self):
        unique_speakers_in_buffer = len(
            set([user_id for user_id,_ in self.frames_buffer])
        )

        if unique_speakers_in_buffer==1:
            nekto_instances[self.vc.channel.id].frame_queue.put_nowait(self.frames_buffer)
        else:
            print("multiple detected")
        
        self.frames_buffer.clear()

    def write(self, data, user):
        if len(data)!=3840:
            print("packet too big!")
            return

        #self.frames_buffer.append((user, data))
        nekto_instances[self.vc.channel.id].frame_queue.put_nowait(data)


def finished_callback(*args):
    print(args)

def custom_stop(self):
    while self.decoding:
        time.sleep(0.1)
        self.decoder = {}
        gc.collect()
        print("Decoder Process Killed")
        break
    self._end_thread.set()
DecodeManager.stop = custom_stop

def custom_recv_decoded_audio(self, data):
    while data.ssrc not in self.ws.ssrc_map:
        time.sleep(0.05)
    self.sink.write(data.decoded_data, self.ws.ssrc_map[data.ssrc]["user_id"])

@bot.command()
async def start(ctx: discord.ApplicationContext):
    nekto_client_instance = nekto_client.NektoRoulette('marat', "77d7bc3a-ba60-49d0-bf1d-ab97ed07cc42")

    voice = ctx.author.voice

    if not voice:
        return await ctx.respond("You're not in a vc right now")

    voice_client = await voice.channel.connect()
    discord.voice_client.VoiceClient.recv_decoded_audio = custom_recv_decoded_audio

    nekto_client_instance.voice_client = voice_client
    custom_sink = MySubClassedSink()

    nekto_instances[ctx.author.voice.channel.id]=nekto_client_instance

    voice_client.start_recording(
        custom_sink,
        finished_callback,
        ctx.channel,
    )
    await ctx.respond("Conversation started")
    await nekto_client_instance.run()

    voice_client.stop_recording()
    await voice_client.disconnect()

uvloop.install()
bot.run('OTc5NjQ2MTc1MDU5ODA0MTkw.G_m_JZ._zlvvVhs044d_a_yR4n1hRE2O_g99-LjrwpmN8')
