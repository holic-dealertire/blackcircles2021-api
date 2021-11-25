import requests
import urllib3
import json

address = "서울 종로구 종로 6"
data = {"query": "{}".format(address)}
# url = "https://dapi.kakao.com/v2/local/search/address.json"
rest_api_key = "faef15a7d23be7322e31dc76b5cc1b86"
headers = {"Authorization": "KakaoAK {}".format(rest_api_key)}

http = urllib3.PoolManager()

url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
# headers = {"Authorization": rest_api_key}

try:
    response = http.request('GET', url, body=json.dumps(data), headers=headers, retries=False)
    print(response)
    print(response.json())
except:
    response = ''

