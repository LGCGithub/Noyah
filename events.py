import utils

def defineEvents(client):
    @client.event
    async def on_ready():
        print('We have logged in as {user}'.format(user=client.user))

    switch = {
        '$help': utils.cHelp,
        '$gray': utils.cGray,
        '$blur': utils.cBlur,
        '$warm': utils.cWarm,
        '$cold': utils.cCold,
        '$gui': utils.cGui,
        '$p': utils.cPlay,
        '$play': utils.cPlay,
        '$stop': utils.cStop,
        '$skip': utils.cSkip
    }

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        
        if message.content.startswith("$") and message.content != "$":
            await switch.get(message.content.split()[0].lower(), lambda: "Invalid choice")(message, client)






