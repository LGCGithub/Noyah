import discord
import numpy as np
from PIL import Image, ImageOps, ImageFilter
import requests
import io

import cv2
from scipy.interpolate import UnivariateSpline

# Functions created by me (with a little help from stackoverflow):

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


# Functions i stole from stackoverflow and other websites:

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


token = open("token.txt", "r").read()
client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {user}'.format(user=client.user))

@client.event
async def on_message(message):
    user_id = message.author.id
    channel = message.channel

    if message.content.startswith('$help'):
        await message.channel.send("""
            Commands:
            **$help** -- Shows all commands
            **$gray** -- Applies grayscale to the last image sent to the channel 
            **$warm** -- Applies a "warm filter" to the last image sent to the channel
            **$cold** -- Applies a "cold filter" to the last image sent to the channel
            **$blur {radius:int}** -- Applies Gaussian Blur to the last image sent to the channel
        """)


    # grayscale command
    if message.content.startswith("$gray"):
        # get the last url in the messages, hopefully a image
        messages_in_channel = await message.channel.history(limit=10).flatten() 
        url = getImgUrl(messages_in_channel)

        if url == None:
            return
        
        #get img from url, resize if too big, grayscale, upload
        img = await downloadImg(url)
        img = check_image_size(img)
        img = ImageOps.grayscale(img)
        await uploadImg(img, channel)
        
    
    # blur command
    if message.content.startswith("$blur"):
        args = message.content.split()
        r = int(args[1])

        # get the last url in the messages, hopefully a image
        messages_in_channel = await message.channel.history(limit=10).flatten() 
        url = getImgUrl(messages_in_channel)

        if url == None:
            return

        #get img from url, resize if too big, blur, upload
        img = await downloadImg(url)
        img = check_image_size(img)
        img = img.filter(ImageFilter.GaussianBlur(radius=r))
        await uploadImg(img, channel)


    if message.content.startswith("$warm"):
        
        # get the last url in the messages, hopefully a image
        messages_in_channel = await message.channel.history(limit=10).flatten() 
        url = getImgUrl(messages_in_channel)

        if url == None:
            return

        #get img from url, resize if too big, warm filter, upload
        img = await downloadImg(url)
        img = check_image_size(img)
        img = cv_to_pil(warmImage(pil_to_cv(img)))
        await uploadImg(img, channel)

    
    if message.content.startswith("$cold"):
        
        # get the last url in the messages, hopefully a image
        messages_in_channel = await message.channel.history(limit=10).flatten() 
        url = getImgUrl(messages_in_channel)

        if url == None:
            return

        #get img from url, resize if too big, cold filter, upload
        img = await downloadImg(url)
        img = check_image_size(img)
        img = cv_to_pil(coldImage(pil_to_cv(img)))
        await uploadImg(img, channel)
        
    
client.run(token)
