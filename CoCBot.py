from discord import Client
import asyncio
import os
import json
from cocbotcore import Commands, MultiGuildHandler, GuildCharaDataCollection
from Dishelve import DiShelve
 
class CocBotClient(Client):
    def __init__(self):
        super().__init__()
        self.owner = None
        self._data_guild_id = None
        self.guild_handler = MultiGuildHandler()
        self.commands = Commands(client=self)
        self.dishelve = None
    
    async def on_ready(self):
        self.owner = (await self.application_info()).owner
        print(f'Logged on as {client.user.name}!')
        print(f'owner is {self.owner}')
        print('init shelve guild')
        await self.init_dishelve()
        print('done')
        
    async def init_dishelve(self):
        for g in self.guilds:
            if g.owner == self.user:
                break
        else:
            g = await self.create_guild(name='data')
        
        self.dishelve = DiShelve(self, g.id)
        await self.dishelve.ready()
    
    async def init_guild_charas_data(self, guild_id):
        content = await self.dishelve.read(guild_id)
        data = json.loads(content)
        characollection = self.guild_handler.add_characollection(guild_id, {})
        if data:
            await asyncio.wait([self.loop.create_task(characollection.set(int(user), url)) for user, url in data.items()])
            
        return characollection
        
    async def save(self, guild_id):
        print('save start')
        data = self.guild_handler.get_characollection(guild_id).url_dict
        self.dishelve.write(guild_id, json.dumps(data))
        
    async def on_message(self, msg):
        if msg.author == self.user:
          return 
        if debug:
            if msg.author != self.owner:
              return 
        #print('msg is :', msg.content)
        if msg.guild and ('$' in msg.content or msg.content.startswith('set ')):
            guild_id = msg.guild.id
            
            collection = self.guild_handler.get_characollection(guild_id) \
                            or await self.init_guild_charas_data(guild_id)
            
        else:
            collection = GuildCharaDataCollection({})
            
        command_is_set = msg.content.startswith('set ')
        res = await self.commands.run(msg, collection)
        if command_is_set and res.status_code in (200, 403):
            await self.save(guild_id)
            if res.status_code == 200:
                await msg.channel.send('success')
 
    async def on_guild_join(self, guild):
        await self.dishelve.add_shelf(guild.id)


debug = os.environ.get('debug',False)
token = os.environ['token']
client = CocBotClient()


if __name__ == '__main__':
    client.run(token)
