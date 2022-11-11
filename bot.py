import discord
import asyncio

from discord.sinks import Sink, Filters
import nekto_client
from aiortc.codecs.opus import OpusDecoder

bot = discord.Bot()

class MySubClassedSink(Sink):
    def write(self, data, user):
        nekto_client.frame_queue.put_nowait(data)

def finished_callback(*args):
    print(args)

@bot.command()
async def start(ctx: discord.ApplicationContext):
    nekto_client_instance = nekto_client.NektoRoulette('marat', "77d7bc3a-ba60-49d0-bf1d-ab97ed07cc42")

    voice = ctx.author.voice

    if not voice:
        return await ctx.respond("You're not in a vc right now")

    voice_client = await voice.channel.connect()
    from discord.opus import Encoder
    voice_client.encoder = Encoder()

    nekto_client.voice_client = voice_client

    custom_sink = MySubClassedSink()

    voice_client.start_recording(
        custom_sink,
        finished_callback,
        ctx.channel,
    )

    await nekto_client_instance.run()
    await ctx.respond("Conversation started")

    voice_client.stop_recording()

bot.run('OTc5NjQ2MTc1MDU5ODA0MTkw.G_m_JZ._zlvvVhs044d_a_yR4n1hRE2O_g99-LjrwpmN8')
