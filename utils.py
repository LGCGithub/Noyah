
import discord
from discord.utils import get
import requests
import io

import cv2
from scipy.interpolate import UnivariateSpline
import numpy as np
from PIL import Image, ImageOps, ImageFilter

import ffmpeg
import asyncio

def getImgUrl(messages_in_channel):
    for msg in messages_in_channel:
        try:
            strUrl = msg.attachments[0].url.lower()
            print(strUrl)
            if strUrl.endswith(".jpg") or strUrl.endswith(".png"):
                url = msg.attachments[0].url
                break
        except IndexError:
            continue
    try:
        return url
    except UnboundLocalError:
        return None


# PIL image
async def downloadImg(url):
    response = requests.get(url)
    return Image.open(io.BytesIO(response.content))


# PIL image
async def uploadImg(img, channel):
    with io.BytesIO() as image_binary:
        img.save(fp=image_binary, format="PNG")
        image_binary.seek(0)
        await channel.send(file=discord.File(fp=image_binary, filename="image.PNG"))


def pil_to_cv(pil_img):
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def cv_to_pil(cv_img):
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def check_image_size(img):
    if img.size[0]*img.size[1] > 1920*1080:
        new_width  = img.size[0]/2
        new_height = img.size[1]/2
        new_width  = int(new_height * img.size[0] / img.size[1])
        new_height = int(new_width * img.size[1] / img.size[0]) 

        return img.resize((new_width, new_height))
    else:
        return img

def spreadLookupTable(x, y):
  spline = UnivariateSpline(x, y)
  return spline(range(256))

def coldImage(image):
    increaseLookupTable = spreadLookupTable([0, 64, 128, 256], [0, 80, 160, 256])
    decreaseLookupTable = spreadLookupTable([0, 64, 128, 256], [0, 50, 100, 256])
    red_channel, green_channel, blue_channel = cv2.split(image)
    red_channel = cv2.LUT(red_channel, increaseLookupTable).astype(np.uint8)
    blue_channel = cv2.LUT(blue_channel, decreaseLookupTable).astype(np.uint8)
    return cv2.merge((red_channel, green_channel, blue_channel))


def warmImage(image):
    increaseLookupTable = spreadLookupTable([0, 64, 128, 256], [0, 80, 160, 256])
    decreaseLookupTable = spreadLookupTable([0, 64, 128, 256], [0, 50, 100, 256])
    red_channel, green_channel, blue_channel = cv2.split(image)
    red_channel = cv2.LUT(red_channel, decreaseLookupTable).astype(np.uint8)
    blue_channel = cv2.LUT(blue_channel, increaseLookupTable).astype(np.uint8)
    return cv2.merge((red_channel, green_channel, blue_channel))


async def cHelp(ctx, client):
    await ctx.channel.send("""
            Commands:
            **$help** -- Mostra todos os comandos
            **$gray** -- Aplica tons de cinza à última imagem enviada no chat
            **$warm** -- Aplica um "filtro quente" à última imagem enviada no chat
            **$cold** -- Aplica um "filtro frio" à última imagem enviada no chat
            **$blur {número inteiro}** -- Borra a última imagem enviada no chat
            **$play {link / título do video}** -- Toca o audio de um video do youtube
            **$p {link / título do video}** -- Toca o audio de um video do youtube
            **$skip** -- Pula a música atual e vai direto pra próxima da fila
            **$stop** -- Para de tocar música e reseta a playlist
            **$gui** -- banana segredinho 
        """)

async def cGray(ctx, client):
    messages_in_channel = []
    async for msg in ctx.channel.history(limit=10):
        messages_in_channel.append(msg)
            
    url = getImgUrl(messages_in_channel)

    if url == None:
        return
        
    #get img from url, resize if too big, grayscale, upload
    img = await downloadImg(url)
    img = check_image_size(img)
    img = ImageOps.grayscale(img)
    await uploadImg(img, ctx.channel)

async def cBlur(ctx, client):
    args = ctx.content.split()
    
    try:
        r = int(args[1])
    except:
        await ctx.channel.send("Exemplo de uso do commando: $blur 10")
        return



    # get the last url in the messages, hopefully a image
    messages_in_channel = []
    async for msg in ctx.channel.history(limit=10):
        messages_in_channel.append(msg)

    url = getImgUrl(messages_in_channel)

    if url == None:
        return

    #get img from url, resize if too big, blur, upload
    img = await downloadImg(url)
    img = check_image_size(img)
    img = img.filter(ImageFilter.GaussianBlur(radius=r))
    await uploadImg(img, ctx.channel)

async def cWarm(ctx, client):
    # get the last url in the messages, hopefully a image
    messages_in_channel = []
    async for msg in ctx.channel.history(limit=10):
        messages_in_channel.append(msg)

    url = getImgUrl(messages_in_channel)

    if url == None:
        return

    #get img from url, resize if too big, warm filter, upload
    img = await downloadImg(url)
    img = check_image_size(img)
    img = cv_to_pil(warmImage(pil_to_cv(img)))
    await uploadImg(img, ctx.channel)

async def cCold(ctx, client):
    # get the last url in the messages, hopefully a image
    messages_in_channel = []
    async for msg in ctx.channel.history(limit=10):
        messages_in_channel.append(msg)

    url = getImgUrl(messages_in_channel)

    if url == None:
        return

    #get img from url, resize if too big, cold filter, upload
    img = await downloadImg(url)
    img = check_image_size(img)
    img = cv_to_pil(coldImage(pil_to_cv(img)))
    await uploadImg(img, ctx.channel)

async def cGui(ctx, client):
    img = Image.open("images/gui.jpg")
    await ctx.channel.send("ALWAYS REMEMBER 8 OF JANEIRO, O DIA QUE O GUI DEU UM GOLPE NA REPUBLICA")
    await uploadImg(img, ctx.channel)

playlist = {}

async def cPlay(ctx, client):
    channel = ctx.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)

    # connect
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    if ctx.guild not in playlist:
        playlist[ctx.guild] = []

    url = ' '.join(ctx.content.split()[1:])
    print(url)
    # Retrieve URLs of videos from playlist
    
    if url == "":
        await ctx.channel.send("Se acha que eu tenho cara de vidente? oque é pra eu tocar caralho?")
        return
        
    music = await ffmpeg.YTDLSource.from_url(url, loop=client.loop)
    await ctx.channel.send("Adicionando {} na playlist!".format(music.title))
    playlist[ctx.guild].append(music)

    if not voice.is_playing():
        while ctx.guild in playlist:
            try:
                if len(playlist[ctx.guild]) > 0 and not voice.is_playing(): # If there's something is the playlist play it
                    player = playlist[ctx.guild].pop(0)
                    voice.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                    await ctx.channel.send("Tocando agora: {}".format(player.title))

                elif not voice.is_playing(): # No music is playing and there is nothing in the playlist
                    del playlist[ctx.guild]
                    await voice.disconnect()
                    await ctx.channel.send("Cabo a playlist **waaaaaaaaaaa**")
                    break

                else: # Waiting for the music to end
                    await asyncio.sleep(1)
            
            except Exception as e:
                print(e)
                break


async def cStop(ctx, client):
    try:
        voice = get(client.voice_clients, guild=ctx.guild)
        del playlist[ctx.guild]
        await voice.disconnect()
        await ctx.channel.send("Bye bye")
    except:
        await ctx.channel.send("Parar de tocar o que? A tua mãe? *CANALHA*")

async def cSkip(ctx, client):
    try:
        voice = get(client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            await ctx.channel.send("Skippando a música atual. Quem foi que colocou essa bomba?")
            voice.stop()
    except:
        await ctx.channel.send("Não tem nada pra skippar seu *burro*")

