import discord
import struct
import nacl.secret

voice_client = None

def _decrypt_xsalsa20_poly1305_lite(data, secret_key, _lite_nonce):
    box = nacl.secret.SecretBox(bytes(secret_key))
    #breakpoint()
    try:
        breakpoint()

        print(data)
        box.decrypt(data[4:], bytes())

    except:
        pass

    #return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext + nonce[:4]

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        global voice_client
        voice_client = await client.guilds[0].voice_channels[2].connect()
        from discord.opus import Encoder
        voice_client.encoder = Encoder()
        rtp_packet = bytearray(b'')


    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

intents = discord.Intents.default()

client = MyClient(intents=intents)
#client.run('OTc5NjQ2MTc1MDU5ODA0MTkw.G_m_JZ._zlvvVhs044d_a_yR4n1hRE2O_g99-LjrwpmN8')
