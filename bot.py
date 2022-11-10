import discord
import asyncio

from discord.sinks import Sink, Filters
import nekto_client
from aiortc.codecs.opus import OpusDecoder

class MySubClassedSink(Sink):
    def write(self, data, user):
        nekto_client.frame_queue.put_nowait(data)

def finished_callback(*args):
    print(args)

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        nekto_client_instance = nekto_client.NektoRoulette('marat', "77d7bc3a-ba60-49d0-bf1d-ab97ed07cc42")
        
        voice_client = await client.guilds[0].voice_channels[2].connect()
        from discord.opus import Encoder
        voice_client.encoder = Encoder()
        print("encoder")
        nekto_client.voice_client = voice_client
        print("voice")
        custom_sink = MySubClassedSink()

        print("prerec")
        voice_client.start_recording(
            custom_sink,
            finished_callback,
            client.guilds[0].voice_channels[1],
        )
        print("rec")

        await nekto_client_instance.run()
        print("nekto")


intents = discord.Intents.default()

client = MyClient(intents=intents)
client.run('OTc5NjQ2MTc1MDU5ODA0MTkw.G_m_JZ._zlvvVhs044d_a_yR4n1hRE2O_g99-LjrwpmN8')
