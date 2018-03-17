import hashlib
import os
import sys
import requests
from bs4 import BeautifulSoup

print('Tieba sign python edition')
print('Code by Konge(@zkonge)')


class BaiduUser:
    r = requests.Session()
    r.headers = {}

    def __init__(self, cookies):
        for item in cookies.split('; '):
            item = item.split('=', 1)
            self.r.cookies.set(item[0], item[1])

    def get_tbs_page(self):
        return self.r.get("http://tieba.baidu.com/dc/common/tbs").json()

    @property
    def is_login(self):
        return bool(self.get_tbs_page()['is_login'])

    def get_tbs(self):
        return self.get_tbs_page()['tbs']

    # ->[(tieba_name,tieba_id,tiebaExp),...]
    def get_liked_tieba_list(self):
        liked_tieba_list = []
        pn = 1

        while True:
            raw_page = self.r.get('http://tieba.baidu.com/f/like/mylike?pn=%d' % pn)
            parsed_page = BeautifulSoup(raw_page.text, 'html.parser')

            if not parsed_page.td:
                return liked_tieba_list

            raw_liked_tieba_list = parsed_page.find_all('tr')

            for liked_tieba in raw_liked_tieba_list:
                if liked_tieba.th:
                    continue
                liked_tieba = liked_tieba.find_all('td')
                tb_name, tb_exp, tb_id = liked_tieba[0].a['title'], liked_tieba[1].a.getText(), liked_tieba[-1].span[
                    'balvid']
                liked_tieba_list.append((tb_name, tb_id, tb_exp))
            pn += 1


def tieba_sign(tieba_user, tieba_name, tieba_id):
    data = {
        '_client_id': '03-00-DA-59-05-00-72-96-06-00-01-00-04-00-4C-43-01-00-34-F4-02-00-BC-25-09-00-4E-36',
        '_client_type': '4',
        '_client_version': '1.2.1.17',
        '_phone_imei': '540b43b59d21b7a4824e1fd31b08e9a6',
        'fid': str(tieba_id),
        'kw': tieba_name,
        'net_type': '3',
        'tbs': tieba_user.get_tbs()
    }

    sign_data = ''.join([k + '=' + data[k] for k in sorted(data.keys())])
    sign_data += 'tiebaclient!!!'
    sign_data = hashlib.md5(sign_data.encode()).hexdigest().upper()

    data['sign'] = sign_data

    return_data = tieba_user.r.post('http://c.tieba.baidu.com/c/c/forum/sign', data=data).json()
    code = return_data['error_code']
    if code == '0':
        return 1, return_data['user_info']['sign_bonus_point']
    elif code in ('3', '160002'):
        return 0, 1  # have signed
    else:
        return 0, 0, return_data['error_code'], return_data['error_msg']


def work(liked_tieba):
    global user  # FuckingCode..
    ret = tieba_sign(user, liked_tieba[0], liked_tieba[1])
    if ret[0]:
        print('Signing', liked_tieba[0], '...Exp', liked_tieba[2], '+%s' % ret[1])
    elif ret[1]:
        print('Signing', liked_tieba[0], '...', 'HasSigned')
    else:
        print('ERR~ ', ret[2], ret[3])


try:
    cookie_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cookie.txt')
    if not os.path.exists(cookie_path):
        print('cookie.txt not found,create it and put your cookies in it.')
        exit(1)
    with open(cookie_path) as f:
        user = BaiduUser(f.read().strip())

    if not user.is_login:
        print('\nis it a invalid cookie?')
        exit(1)

    print('\nget tieba list', end='')
    liked_tieba_list = user.get_liked_tieba_list()
    print('...OK\n')

    if len(sys.argv) > 1 and sys.argv[1] == '-m':
        print('NOTICE:fast mode ON')
        from multiprocessing.dummy import Pool

        if len(sys.argv) > 2:
            pool = Pool(int(sys.argv[2]))
        else:
            pool = Pool(3)
        pool.map(work, liked_tieba_list)

    else:
        for liked_tieba in liked_tieba_list:
            ret = tieba_sign(user, liked_tieba[0], liked_tieba[1])
            if ret[0]:
                print('Signing', liked_tieba[0], '...Exp', liked_tieba[2], '+%s' % ret[1])
            elif ret[1]:
                print('Signing', liked_tieba[0], '...', 'HasSigned')
            else:
                print('ERR~ ', ret[2], ret[3])
except KeyboardInterrupt:
    pass
except Exception as e:
    print('\nProgram ERROR!! ', e)
