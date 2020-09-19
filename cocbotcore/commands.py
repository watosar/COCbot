# -*- coding: utf-8 -*-
import re
import asyncio
from discord import Embed, Forbidden, Status
from collections import namedtuple
from .utils import calc
from textwrap import dedent


class Response(namedtuple('Response', ('status_code','reason', 'content'))):
    def __new__(cls, status_code, reason='', content=None):
        return super().__new__(cls, status_code, reason, content)
    

class Context:
    __slots__ = ('author', 'channel', 'top', 'targets', 'contents_list')
    def __init__(self, msg):
        self.author = msg.author
        self.channel = msg.channel
        self.top, *elements = (
            i for i in msg.content.translate(
                str.maketrans({'？': '?', '＄': '$', '（': '(', '）': ')', '＋': '+', '＝': '='})
                ).upper().split()
            )
        user_mentions = dict(re.findall('(<@!?([0-9]+)>)', msg.content))
        role_mentions = dict(re.findall('(<@&([0-9]+)>)', msg.content))
        self.targets = []
        print(elements)
        for i in reversed(elements):
            if i in user_mentions:
                elements.pop()
                self.targets.append(int(user_mentions[i]))
                continue
            elif i in role_mentions:
                elements.pop()
                self.targets.extend(m.id if m else '...' for m in msg.guild.get_role(int(role_mentions[i])).members or [None])
            elif i == '@EVERYONE':
                elements.pop()
                self.targets.extend(m.id for m in msg.guild.members if not m.bot)
            elif i == '@HERE':
                elements.pop()
                self.targets.extend(m.id for m in msg.guild.members if not m.bot and m.status is Status.online)
            break
        if not self.targets:
            self.targets.append(msg.author.id)
            
        self.contents_list = elements
        
        
class CommandsBody:
    __slots__ = ('client', 'chara_data_collection', )
    def __init__(self, client, collection):
        self.client = client
        self.chara_data_collection = collection
        
    async def run(self, msg):
        if len(msg.content.splitlines()) > 1:
            return Response(204)
            
        ctx = Context(msg)
        print(ctx.top)
        try:
            if re.match(f'<@!?{self.client.user.id}>' , ctx.top):
                if ctx.contents_list == ['HELP']:
                    await msg.channel.send(self.client.__doc__)
                    response = Response(200, ctx)
                elif  len(ctx.contents_list)==2 and ctx.contents_list[0] == 'CALC':
                    response = await self.send_calc_results(
                        ctx.author, ctx.channel, ctx.contents_list[1], self.calc(ctx.contents_list[1], ctx.targets)
                    )
                else:
                    response = Response(204)
            elif ctx.top == 'CHARA':
                response = await self.chara_create_dice_roll(ctx.channel, ctx.targets)
            elif ctx.top == 'SET':
                response = await self.set(ctx.channel, *ctx.contents_list, ctx.targets)
            elif ctx.top.endswith('?'):
                response = await self.comp_with_1d100(ctx.author, ctx.channel, ctx.top, ctx.targets)
            elif ctx.top.startswith('$') and not any(i in ctx.top for i in '+-/*()'):
                response = await self.abi_controle(ctx.author, ctx.channel, ctx.top[1:], ctx.contents_list, ctx.targets)
            elif re.search('[0-9]D[0-9]', ctx.top):
                response = await self.roll_dice(ctx.author, ctx.channel,  ctx.top, ctx.targets)
            else:
                response = Response(204)
        except Exception as e:
            if len(e.args)>0 and isinstance(e.args[0], (tuple,)):
                status_code, reason = e.args[0]
                if isinstance(e, (KeyError,)) and isinstance(reason,(tuple,)) and isinstance(reason[1],(int,)):
                    reason = f'{reason[0]} : <@{reason[1]}>'
                response = Response(status_code, reason)
            else:
                response = Response(500, e)
        else:
            if not response:
                response = Response(200)
        
        return response
        
    async def chara_create_dice_roll(self, channel, targets):
        tasks = []
        for target in targets:
            chara_abis=f'>> <@{target}>\n'
            for key in ('STR', 'CON', 'POW', 'DEX', 'APP', 'SIZ', 'INT', 'EDU'):
                formula_0 = ('3d6' if key in ('STR', 'CON', 'POW', 'DEX', 'APP','EDU') else '2d6')+{'SIZ':'+6','INT':'+6','EDU':'+3'}.get(key,'')
                calc_result, formula_1 = calc(formula_0)
                chara_abis += f'{key}: {calc_result:>2} |\\| {formula_0:<5}={formula_1}\n'
            tasks.append(self.client.loop.create_task(channel.send(chara_abis)))
        await asyncio.wait(tasks)
        return Response(200)
        
    async def send_calc_results(self, author, channel, title, results, *, is_secret=False):
        #head = f'>> {author.mention}'
        embed = Embed(title=title)
        descriptions=(dedent('''\
        >> <@{target}>
        {result} |\\| {formula}
        '''.format(**i)) for i in results)
        if not is_secret:
            #await channel.send(head, embed=embed)
            await channel.send(embed=embed)
            await asyncio.wait([self.client.loop.create_task(channel.send(description)) for description in descriptions])
        else:
            #await author.send(head, embed=embed)
            await author.send(embed=embed)
            await asyncio.wait([self.client.loop.create_task(author.send(description)) for description in descriptions])
            embed.description = '**SECRET**'
            #await channel.send(head, embed=embed)
            await channel.send(embed=embed)
    
    def repl_abi(self, formula, target):
        print('before:', formula)
        formula = re.sub(
            '(?=^|(?<=[-+*/%<>=]))[$](.+?)(?=[-+*/%<>=)]|$)',
            lambda m: '('+'+'.join(str(
                i) for i in self.chara_data_collection.get_abi_of_chara(
                    m.groups()[0], target
                ).values() if i)+')',
            formula
        )
        print('after:', formula)
        return formula
    
    def calc(self, formula_0, targets):
        results = []
        for target in targets:
            formula = self.repl_abi(formula_0, target)
            calc_result, formula_1 = calc(formula)
            results.append({'target': target, 'result': calc_result, 'formula': formula_1})
        return results
            
    async def roll_dice(self, author, channel, formula_0, targets):
        print('roll_dice', channel, formula_0, targets)
        results = []
        for target in targets:
            formula = self.repl_abi(formula_0, target)
            print(formula)
            try:
                calc_result, formula_1 = calc(formula)
            except ValueError:
                return Response(204)
            results.append({'target': target, 'result': calc_result, 'formula': formula_1})
        await self.send_calc_results(author, channel, formula_0, results)

    async def comp_with_1d100(self, author, channel, command, targets):
        secret = False
        results = []
        if command.endswith('??'):
            command = command[:-1]
            secret = True
        formula_left = command[:-1]
        formula_0 = formula_left+'>=1D100'
        for target in targets:
            formula = self.repl_abi(formula_0, target)
            try:
                calc_result, formula_1 = calc(formula)
            except ValueError as e:
                if len(e.args)>0 and isinstance(e.args[0],(tuple,)) and e.args[0][0]==400:
                    return Response(204)
            results.append ({'target': target, 'result': calc_result, 'formula': formula_1})
        await self.send_calc_results(author, channel, formula_0, results, is_secret=secret) 
        
    async def abi_controle(self, author, channel, abi, contents_list, targets):
        if not abi:
            return Response(204)
        elif not len(contents_list):
            return await self.show(author, channel, abi, targets)
        elif len(contents_list) != 2:
            return Response(400, '引数が不正です')
        operator, formula = contents_list
        return await self.edit(author, channel, abi, operator, formula, targets)
    
    async def _edit_nick_for_chara(self, channel, target):
        abi_info = self.chara_data_collection.get_nick_of_chara(target)
        member = channel.guild.get_member(target)
        bef = ''
        for i in member.display_name.split():
            if ':'not in i and '/'not in i and '|'not in i:
                bef += i
                continue
            break
        nick=f'{bef} {abi_info}'[:32]
        print(member.guild.me.guild_permissions.manage_nicknames)
        try:
            await member.edit(nick=nick)
        except Forbidden as e:
            print(e)
            await channel.send(nick)
            return Response(403, e.text)
            
    async def set(self, channel, url, targets):
        if len(targets)>1:
            return Response(400, 'ターゲッティングが不正')
        elif not isinstance(url, (str,)):
            return Response(400, '引数が不正')
        target = targets[0]
        try:
            await self.chara_data_collection.set(target, url)
        except ValueError:
            return Response(400, 'urlが不正です')
        else:
            res = await self._edit_nick_for_chara(channel, target)
            return res or Response(200)

    async def edit(self, author, channel, abi, operator, formula_0, targets):
        results = []
        res = None
        for target in targets:
            formula = self.repl_abi(formula_0, target)
            calc_result, formula_1 = calc(formula)
                
            if isinstance(calc_result,(bool,)):
                return Response(400, '真偽値は使用できません')
            
            if operator == '=':
                plus = -sum(self.chara_data_collection.get_abi_of_chara(abi, target).values())+calc_result
            elif operator == '+=':
                plus = calc_result
            elif  operator == '-=':
                plus = -calc_result
                
            current, initial = self.chara_data_collection.patch(target, abi, plus)
            results.append({'target': target, 'result': plus, 'formula': operator+formula_1})
            res = await self._edit_nick_for_chara(channel, target)
        await self.send_calc_results(author, channel, abi+operator+formula_0, results)
        return res

    async def show(self, author, channel, abi, targets):
        description = '\n'.join(
            f'<@{target}>: {value}'
            for target,value in self.chara_data_collection.get_abi_of_multiple_charas(abi, targets).items()
        )
        embed = Embed(title=abi, description=description)
        await channel.send(f'>> {author.mention}',embed=embed)
        return Response(200)


class Commands:
    __slots__ = ('client')
    def __init__(self, client):
      self.client = client

    async def response(self, author, channel, response):
        status_code = response.status_code
        if status_code == 204:
            print('msg is not command')
            return
        if status_code == 200:
            #await channel.send(f'正常終了 >> {author.mention}\n{" : "+response.reason if response.reason else ""}')
            pass
        elif status_code == 500:
            await channel.send(f'内部エラー：{response.reason}')
            raise response.reason
        elif status_code == 501:
            await channel.send('未完成のコマンド')
        elif status_code == 400:
            await channel.send(f'コマンドが不正です。: {response.reason}')
        elif status_code == 403:
            await channel.send(f'FORBIDDEN: {response.reason}')
        elif status_code == 404:
            await channel.send(f'Not Found : {response.reason}')
        else:
            await channel.send('未定義エラーです')
        print(status_code)
        return response
        
    async def run(self, message, collection):
        response = await CommandsBody(self.client, collection).run(message)
        self.client.loop.create_task(self.response(message.author, message.channel, response))
        return response
 
