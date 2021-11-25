import requests


def location_data(address):
    params = {"query": "{}".format(address)}
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()['documents'][0]['road_address']['zone_no']
    except:
        data = ''
    print(data)


url = "https://dapi.kakao.com/v2/local/search/address.json"

rest_api_key = "faef15a7d23be7322e31dc76b5cc1b86"
headers = {"Authorization": "KakaoAK {}".format(rest_api_key)}

address = "서울 종로구 종로 6"
location_data(address)
