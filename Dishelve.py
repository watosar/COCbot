class DiShelve:
    def __init__(self, client, shelve_guild_id : int):
        self.client = client
        self._shelve_guild_id: int = shelve_guild_id
    
    @property
    def _shelve_guild(self):
        return self.client.get_guild(self._shelve_guild_id)

    async def ready(self):
        prepared_guild_id_set = set(i.name for i in self._shelve_guild.channels) 
        for g in self.client.guilds:
            if g.id == self._shelve_guild: continue
            elif str(g.id) not in prepared_guild_id_set:
                ch = await self._shelve_guild.create_text_channel(name=g.id)
                await ch.send("0{}1")
    
    def _get_channel_of_guild(self, guild_id: int):
        key = str(guild_id)
        return next(
            ch for ch in self._shelve_guild.channels
                if ch.name == key
        )
    
    async def add_shelf(self, guild_id):
        ch = await  self._shelve_guild.create_text_channel(guild_id)
        await ch.send("0{}1")

    async def write(self, guild_id: int, json_data: str):
        ch = self._get_channel_of_guild(guild_id)
        text = f"0{json_data}1"
        for _ in range(len(text)//2000):
            text_, text = text[:2000], text[2000:] 
            await ch.send(text_)
        if text:
            await ch.send(text)

    async def read(self, guild_id: int) -> str:
        ch = self._get_channel_of_guild(guild_id)
        if not ch:
            raise ValueError(f"no available channel for the guild: {guild_id}")
        content = ""
        found_last_symbol = False
        async for msg in ch.history(limit=None):
            if not found_last_symbol:
                if not msg.content.endswith("}1"): 
                    raise ValueError(f"invalid style message in channle: {guild_id}")
                    
                found_last_symbol = True
                content = msg.content[:-1]
                if content.startswith('0{'):
                    content = content[1:]
                    break
            elif msg.content.startswith('0{'):
                content = msg.content[1:]+content
                break
            else:
                content = msg.content+content
        return content
    