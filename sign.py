# Tieba_Sign-Py

print('Tieba_Sign Python version')
print('Code by Konge(@zkonge)')
print('Protocol from Kookxiang(@kookxiang)\n')

print('Loading modules', end='')
import hashlib, os, sys, time
from bs4 import BeautifulSoup
import requests as req

print('...Finish')


class baiduUser:
    r = req.Session()
    r.headers = {}

    def __init__(self, BDUSS):
        self.BDUSS = BDUSS
        self.r.cookies.set('BDUSS', BDUSS)

    def getTbsPage(self):
        rawPage = self.r.get("http://tieba.baidu.com/dc/common/tbs")
        return rawPage.json()

    @property
    def isLogin(self):
        return bool(self.getTbsPage()['is_login'])

    def getTbs(self):
        return self.getTbsPage()['tbs']

    # ->[(tiebaName,tiebaId,tiebaExp),...]
    def getLikedTiebaList(self):
        likedTiebaList = []
        pn = 1

        while True:
            rawPage = self.r.get('http://tieba.baidu.com/f/like/mylike?pn=%d' % pn)
            parsedPage = BeautifulSoup(rawPage.text, 'html.parser')

            if not parsedPage.td:
                return likedTiebaList

            rawLikedTiebaList = parsedPage.find_all('tr')

            for likedTieba in rawLikedTiebaList:
                if likedTieba.th:
                    continue
                likedTieba = likedTieba.find_all('td')
                tbName, tbExp, tbId = likedTieba[0].a['title'], likedTieba[1].a.getText(), likedTieba[-1].span['balvid']
                likedTiebaList.append((tbName, tbId, tbExp))
            pn += 1


def tiebaSign(tiebaUser, tiebaName, tiebaId):
    data = {
        'BDUSS': tiebaUser.BDUSS,
        '_client_id': '03-00-DA-59-05-00-72-96-06-00-01-00-04-00-4C-43-01-00-34-F4-02-00-BC-25-09-00-4E-36',
        '_client_type': '4',
        '_client_version': '1.2.1.17',
        '_phone_imei': '540b43b59d21b7a4824e1fd31b08e9a6',
        'fid': str(tiebaId),
        'kw': tiebaName,
        'net_type': '3',
        'tbs': tiebaUser.getTbs()
    }

    signData = ''.join([k + '=' + data[k] for k in sorted(data.keys())])
    signData += 'tiebaclient!!!'
    signData = hashlib.md5(signData.encode()).hexdigest().upper()

    data['sign'] = signData

    returnData = tiebaUser.r.post('http://c.tieba.baidu.com/c/c/forum/sign', data=data).json()
    code = returnData['error_code']
    if code == '0':
        return 1, returnData['user_info']['sign_bonus_point']
    elif code in ('3', '160002'):
        return 0, 1  # haveSigned
    else:
        return 0, 0, returnData['error_code'], returnData['error_msg']


def work(likedTieba):
    global user  # FuckingCode..
    ret = tiebaSign(user, likedTieba[0], likedTieba[1])
    if ret[0]:
        print('Signing', likedTieba[0], '...Exp', likedTieba[2], '+%s' % ret[1])
    elif ret[1]:
        print('Signing', likedTieba[0], '...', 'HasSigned')
    else:
        print('ERR~ ', ret[2], ret[3])


try:
    if not os.path.exists('cookie.txt'):
        print('cookie.txt not found,create it and put your BDUSS value in it.')
        exit()
    with open('cookie.txt') as f:
        BDUSS = f.read().strip()

    user = baiduUser(BDUSS)

    if not user.isLogin:
        print('\nis it a invaild cookie?')
        exit()

    print('\ngetTiebaList', end='')
    likedTiebaList = user.getLikedTiebaList()
    print('...OK\n')

    if len(sys.argv) > 1 and sys.argv[1] == '-m':
        print('NOTICE:Multi thread mode ON')
        from multiprocessing.dummy import Pool

        if len(sys.argv) > 2:
            pool = Pool(int(sys.argv[2]))
        else:
            pool = Pool(3)
        pool.map(work, likedTiebaList)

    else:  # SingleThread
        for likedTieba in likedTiebaList:
            ret = tiebaSign(user, likedTieba[0], likedTieba[1])
            if ret[0]:
                print('Signing', likedTieba[0], '...Exp', likedTieba[2], '+%s' % ret[1])
            elif ret[1]:
                print('Signing', likedTieba[0], '...', 'HasSigned')
            else:
                print('ERR~ ', ret[2], ret[3])
except KeyboardInterrupt:
    pass
except Exception as e:
    print('Program ERROR!! ', e)
