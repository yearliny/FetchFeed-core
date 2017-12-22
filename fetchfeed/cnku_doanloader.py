import requests
import time

auth = {
    'password': 'yyl1248663054',
    'appkey': '2isdlw',
    'encryptKey': 'jds)(#&dsa7SDNJ32hwbds%u32j33edjdu2@**@3w',
    'url': 'http://api.cnki.net/OAuth/OAuth/Token'
}
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Apache-HttpClient/UNAVAILABLE (java 1.4)'
}
encPassData = []
for i in range(len(auth['password'])):
    encPassData.append()

data = {
    'grant_type': 'password',
    'username': 'yearliny',
    'password': 'Ex0fGBoXHlJFUgdmcA== ',
    'client_id': 'cnkimdl_clcn',
    'client_secret': '6c9d6b3a5bbc6a2b50c795e9d2ab311b22bbbd89',
    'sign': str(int(time.time()*1000))
}


s = requests.Session()
r = s.post(auth['url'], headers=headers, data=data)
r.encoding = 'utf-8'
print(r.text)
