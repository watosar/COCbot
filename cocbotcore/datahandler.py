# -*- coding: utf-8 -*-
from .scrape import scrape
from math import ceil

abi_initial_val_dict = {
    '回避': '$DEX×2', 'キック': 25, '組みつき': 25, 'こぶし': 50, 'パンチ': 50, '頭突き': 10, '投擲': 25, 'マーシャルアーツ': 1, '拳銃': 20, 'サブマシンガン': 15, 'ショットガン': 30, 'マシンガン': 15, 'ライフル': 25, '応急手当': 30, '鍵開け': 1, '隠す': 15, '隠れる': 10, '聞き耳': 25, '忍び歩き': 10, '写真術': 10, '精神分析': 1, '追跡': 10, '登攀': 40, '図書館': 25, '目星': 25, '運転': 20, '機械修理': 20, '重機械操作': 1, '乗馬': 5, '水泳': 25, '制作': 5, '操縦': 1, '跳躍': 25, '電気修理': 10, 'ナビゲート': 10, '変装': 1, '言いくるめ': 5, '信用': 15, '説得': 15, '母国語': 10, '医学': 5, 'オカルト': 5, '化学': 1, 'クトゥルフ神話': 0, '芸術': 5, '経理': 10, '考古学': 1, 'コンピューター': 1, '心理学': 5, '生物学': 1, '地質学': 1, '電子工学': 1, '天文学': 1, '博物学': 10, '物理学': 1, '法律': 5, '薬学': 1, '歴史': 20, 'フェンシング': 20, 'サーベル': 15, 'ナイフ': 25, '日本刀': 15, '青龍刀': 10, '薙刀': 10, '杖': 25, '鎖鎌': 5, '節棍': 5, 'ムチ': 5, '居合': 1}
    
    
get_damage_bonus = lambda i:i<13 and '-1D6' or i<17 and '-1D4' or i<25 and '0' or i<33 and '1D4' or i<41 and '1D6' or i<57 and '2D6' or '3D6'


class GuildCharaDataCollection:
    __slots__ = ('chara_data_dict', 'url_dict', 'additional_abi_name_set')
    def __init__(self, data):
        self.chara_data_dict = data
        self.url_dict = {}
        self.additional_abi_name_set = set(('SAN', 'MP', 'HP', 'アイデア', 'アイディア', 'IDEA', '幸運', 'LUC', 'DB', '知識', 'コンピュータ'))
    
    async def set(self, target_user, url):
        url = url.lower()
        result = await scrape(url)
        conv_keys = {'幸運': 'LUC', 'コンピュータ': 'コンピューター'}
        for i in set(result):
            if i not in abi_initial_val_dict:
                self.additional_abi_name_set.add(i)
            conv_key = conv_keys.get(i)
            if conv_key:
                result[conv_key] = result.pop(i)
        self.chara_data_dict[target_user] = result
        self.url_dict[target_user] = url

    def patch(self, target_user, target_abi, change_amount):
        target_abi_dict = self.get_abi_of_chara(target_abi, target_user)
        target_abi_dict['addition'] += int(change_amount)
        addition = target_abi_dict['addition']
        initial = target_abi_dict['initial']
        target_user_dict = self.chara_data_dict[target_user]
        if target_abi == 'CON':
            target_user_dict['HP']['initial'] = ceil((addition+initial+sum(target_user_dict['SIZ'].values()))/2)
        elif target_abi == 'SIZ':
            target_user_dict['HP']['initial'] = ceil((addition+initial+sum(target_user_dict['CON'].values()))/2)
        elif target_abi == 'POW':
            value = addition+initial
            target_user_dict['MP']['initial'] = value
            target_user_dict['SAN']['initial'] = value*5
            self.get_abi_of_chara('幸運', target_user)['initial'] = value*5
        elif target_abi == 'INT':
            target_user_dict['アイデア']['initial'] = (addition+initial)*5
        elif target_abi == 'EDU':
            target_user_dict['知識']['initial'] = (addition+initial)*5
        
        return initial+addition, initial
        
    def get_url(self, user):
        return self.url_dict.get(user)
        
    def get_abi_of_chara(self, ability, user):
        if ability not in abi_initial_val_dict.keys() and ability not in self.additional_abi_name_set:
            raise KeyError((400, f'{ability} is not ability'))
        user_abi_dict = self.chara_data_dict.get(user)
        if user_abi_dict is None:
            raise KeyError((404, ('no data', user)))
        value = user_abi_dict.get(ability)
        if not value:
            if ability == '幸運':
                value = user_abi_dict.get('LUC')
            if ability == 'コンピュータ':
                value = user_abi_dict.get('コンピューター')
            elif ability in ('アイディア', 'IDEA'):
                value = user_abi_dict.get('アイデア')
            elif ability in abi_initial_val_dict:
                value = user_abi_dict.setdefault(ability, {'initial':abi_initial_val_dict[ability],'addition':0})
            elif ability == 'DB':
                value = {'initial':get_damage_bonus(sum((*user_abi_dict.get('SIZ').values(),*user_abi_dict.get('STR').values()))), 'addition':0}
                
        if not value:
            raise KeyError((404, ('no {ability}', user)))
        return value
        
    def get_abi_of_multiple_charas(self, ability, users):
        resp = {}
        value = None
        _error = None
        for user in users:
            try:
                value = self.get_abi_of_chara(ability, user)
            except KeyError as e:
                if e.args[0][0] != 404:
                    _error = e
                    break
                value = {'initial':None, 'addition':None}
            finally:
                resp[user] = value
        else:
            return resp
        raise _error
        
    def get_abi_of_every_charas(self, ability):
        return self.get_abi_of_multiple_charas(ability, self.chara_data_dict.keys())

    def get_nick_of_chara(self, user):
      nick = ''
      for abi in ('HP','SAN'):
        data = self.get_abi_of_chara(abi, user)
        initial = data['initial']
        addition = data['addition']
        nick += f'|{abi}:{initial+addition}/{initial}'
      return nick
      

class MultiGuildHandler:
    __slots__=('characollections_dict', )
    def __init__(self):
        self.characollections_dict = {}
        
    def get_characollection(self, guild_id):
        return self.characollections_dict.get(guild_id)
        
    def add_characollection(self, guild_id, data):
        self.characollections_dict[guild_id] = GuildCharaDataCollection(data)
        return self.characollections_dict[guild_id] 
        
