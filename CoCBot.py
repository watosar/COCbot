# -*- coding: utf-8 -*-
 
from discord import Client
import asyncio
import os
import json
from cocbotcore import Commands, MultiGuildHandler, GuildCharaDataCollection

 
class CocBotClient(Client):
    """
    nekojyarasi#9236 のCoC支援Bot
    プレフィックスは有りません
    * 機能一覧
        + キャラクターシートのデータのキャッシュ
            set URL
                対応済みURL
                - [TRPGキャラシート アーカイブス](chara.revinx.net)
                - [キャラクター保管所](charasheet.vampire-blood.net)
        + キャッシュされた値への補正の一時保存
            ステータス/技能名 [-+]= 数式
        + ニックネームでのHP/SAN/MP表示
            (ex. nekojyarasi HP:00/00|SAN:00/00|MP:00/00)
        + ダイスロール
            chara   
                キャラクターのステータス設定用のダイス
            数式 
                (xdyを含む場合)
            $技能名 
                技能値表示
            $技能名[-+]?=[0-9]+ 
                技能値編集
            数式？ 
                1d100成否ダイス
            数式？？ 
                シークレット1d100成否ダイス
    """
 
    def __init__(self):
        super().__init__()
        self.owner = None
        self._data_guild_id = None
        self.guild_handler = MultiGuildHandler()
        self.commands = Commands(client=self)
        
    @property
    def data_guild(self):
        return self.get_guild(self._data_guild_id)
    
    @data_guild.setter
    def data_guild(self, guild):
        self._data_guild_id = guild.id
        
    def get_data_guild_channel_from_guild_id(self, guild_id):
        return next(ch for ch in self.data_guild.channels if ch.name==str(guild_id))
 
    async def on_ready(self):
        self.owner = (await self.application_info()).owner
        print(f'Logged on as {client.user.name}!')
        print(f'owner is {self.owner}')
        print('start setup data guild')
        await self.setup_data_guild()
        print('done')
        
    async def setup_data_guild(self):
        for g in self.guilds:
            if g.owner == self.user:
                break
        else:
            g = await self.create_guild(name='data')
        
        self.data_guild = g
        print('data guild is :', g)
        channel_names = tuple(i.name for i in self.data_guild.channels)
        for g in self.guilds:
            if g == self.data_guild:
                continue
            if str(g.id) not in channel_names:
                ch = await self.data_guild.create_text_channel(name=g.id)
                await ch.send('0{}1')
    
    async def init_guild_charas_data(self, guild_id):
        ch = self.get_data_guild_channel_from_guild_id(guild_id)
        content = ''
        find_end = False
        async for msg in ch.history(limit=None):
            if find_end:
                if msg.content.startswith('0{'):
                    content = msg.content[2:]+content
                    break
                content = msg.content+content
            elif msg.content.endswith('}1'):
                find_end = True
                content = msg.content[:-1]
                if content.startswith('0{'):
                    content = content[1:]
                    break
        data = json.loads(content)
        characollection = self.guild_handler.add_characollection(guild_id, {})
        if data:
            await asyncio.wait([self.loop.create_task(characollection.set(int(user), url)) for user, url in data.items()])
            
        return characollection
        
    async def save(self, guild_id):
        print('save start')
        ch = self.get_data_guild_channel_from_guild_id(guild_id)
        data = self.guild_handler.get_characollection(guild_id).url_dict
        text = f'0{json.dumps(data)}1'
        while len(text)>2000:
            _text = text[:2000]
            await ch.send(_text)
            text = text[:2000]
        if text:
            await ch.send(text)
        
    async def on_message(self, msg):
        if msg.author == self.user:
          return 
        if debug:
            if msg.author != self.owner:
              return 
        print('msg is :', msg.content)
        if msg.guild and ('$' in msg.content or msg.content.startswith('set ')):
            guild_id = msg.guild.id
            
            collection = self.guild_handler.get_characollection(guild_id) or await self.init_guild_charas_data(guild_id)
            
        else:
            collection = GuildCharaDataCollection({})
            
        command_is_set = msg.content.startswith('set ')
        res = await self.commands.run(msg, collection)
        if command_is_set and res.status_code in (200, 403):
            await self.save(guild_id)
            if res.status_code == 200:
                await msg.channel.send('success')
 
    async def on_guild_join(self, guild):
        ch = await self.data_guild.create_text_channel(guild.id)
        await ch.send('0{}1')


debug = os.environ.get('debug',False)
token = os.environ['token']
client = CocBotClient()


if __name__ == '__main__':
    client.run(token)
