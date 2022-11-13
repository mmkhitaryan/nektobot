import uvloop
import discord

from discord.sinks import Sink
import nekto_client

bot = discord.Bot()

nekto_instances = {

}

class MySubClassedSink(Sink):
    frames_buffer = []

    def send_all_frames(self):
        unique_speakers_in_buffer = len(
            set([user_id for user_id,_ in self.frames_buffer])
        )

        if unique_speakers_in_buffer==1:
            for _,raw_frame in self.frames_buffer:
                nekto_instances[self.vc.channel.id].frame_queue.put_nowait(raw_frame)
        else:
            print("multiple detected")
        
        self.frames_buffer.clear()

    def write(self, data, user):
        if len(data)!=3840:
            print("packet too big!")
        if len(self.frames_buffer)<=5: # flush periodically
            self.frames_buffer.append((user, data))
            self.send_all_frames()


def finished_callback(*args):
    print(args)

def custom_recv_decoded_audio(self, data):
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
