# -*- coding: utf-8 -*-
import aiohttp
from bs4 import BeautifulSoup
from math import ceil
import re

def _conv(initial, addition=0):
    return {'initial': initial, 'addition': addition}


def _chara_vevinx_net(html):
    soup = BeautifulSoup(html, 'html5lib')
    
    status_name = (''.join(i.strings) for i in soup.select_one('#status').thead.find_all('th') if [*i.strings])
    status_initial = (int(i.attrs.get('value',0)) for i in soup.select_one('#status_num').find_all('input'))
    status_addition = (int(i.attrs.get('value')) for i in soup.select_one('#status_plus').find_all('input'))
    
    status = {name: _conv(next(status_initial), next(status_addition)) for name in status_name}
    ext = {
        'HP': ceil((sum(status['CON'].values()) + sum(status['SIZ'].values())) / 2),
        'MP': sum(status['POW'].values()),
        'SAN': sum(status['POW'].values()) * 5,
        'アイデア': sum(status['INT'].values()) * 5,
        '幸運': sum(status['POW'].values()) * 5,
        '知識': sum(status['EDU'].values()) * 5
    }
    for key, value in ext.items():
        status[key]['initial'] = value
    
    status.update({
        i.string or i.input.get('value'):
            _conv(sum(int(j.get('value',0)) 
                for j in i.find_parent().find_all('input', class_='skill_input'))) 
            for i in soup.find_all('th',class_='th_skill_title')
    })
    
    return status


def _charasheet_vampire_blood_net(data):
    result = {}
    # HSM は {'HSM':{'additional':..., 'initial':...}}
    # その他は {'NAME':...}

    # 最後にPをつけたのが技能の最終値
    # 最後にNameで追加技能の名前
    
    abilities = {
      'TBA': ['回避', 'キック', '組み付き', 'こぶし', '頭突き', '投擲', 'マーシャルアーツ', '拳銃', 'サブマシンガン', 'ショットガン', 'マシンガン', 'ライフル'],
      'TFA': ['応急手当', '鍵開け', '隠す', '隠れる', '聞き耳', '忍び歩き', '写真術', '精神分析', '追跡', '登攀', '図書館', '目星'],
      'TAA': ['運転', '機械修理', '重機械操作', '乗馬', '水泳', '製作', '操縦', '跳躍', '電気修理', 'ナビゲート', '変装'],
      'TCA': ['言いくるめ', '信用', '説得', '値切り', '母国語'],
      'TKA': ['医学', 'オカルト', '化学', 'クトゥルフ神話', '芸術', '経理', '考古学', 'コンピューター', '心理学', '人類学', '生物学', '地質学', '電子工学', '天文学', '博物学', '物理学', '法律', '薬学', '歴史']
    }
    for cate_name, abi_name_list in abilities.items():
        abi_name_list += data.get(f'{cate_name}Name',[])
        result.update(
            {
                k: _conv(int(v))
                for k,v in zip(abi_name_list, data[f'{cate_name}P'])
            }
        )

    # 初期値 'NA1~14'
    # 最終値 'NP1~14'
    abi = ('STR', 'CON', 'POW', 'DEX', 'APP', 'SIZ', 'INT', 'EDU', 'HP', 'MP', 'SAN', 'アイデア', 'LUC', '知識') # TODO : 直した
    result.update(
      {
        abi[index]: _conv(
            int(data[f'NA{index+1}']),
            int(data[f'NP{index+1}'])-int(data[f'NA{index+1}'])
        )
        for index in range(14)
      }
    )
    return result
    
_chara_vevinx_net_pat = re.compile('https?://chara\.revinx\.net/(coc_view|coc_make)/[0-9]+')
_charasheet_vampire_blood_net_pat = re.compile('https://charasheet\.vampire-blood\.net/[0-9]+')
  

async def scrape(url):
    print(url)
    if _chara_vevinx_net_pat.match(url):
        urlbase = 'http://chara.revinx.net/coc_make/'
        id = url.split('/')[-1]
        async with aiohttp.request('GET', urlbase+id) as resp:
            return _chara_vevinx_net(await resp.text())
    elif _charasheet_vampire_blood_net_pat.match(url):
        async with aiohttp.request('GET', url.split('#')[0]+'.js') as resp:
            return _charasheet_vampire_blood_net(await resp.json())   
    else:
        raise ValueError('incorrect url')

