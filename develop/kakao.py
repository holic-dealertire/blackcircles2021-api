import json
import requests

url = "https://alimtalk-api.bizmsg.kr/v2/sender/send"
data = [{
    "message_type": "at",
    "phn": "010-6308-8902",
    "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
    "tmplId": "new_purchase_01",
    "msg": "[블랙서클]\n안녕하세요. 블랙서클 회원님!\n구매 목표 구간을 달성하여 할인쿠폰이 발행되었어요.\n오른쪽 하단 내 메뉴 > 쿠폰에서 발급된 쿠폰을 확인하실 수 있습니다.\n\n※ 쿠폰 유효기간은 발급일로부터 일주일이며, 기간이 만료되면 쿠폰 사용 여부와 관계없이 자동 소멸되어 사용이 불가능합니다.\n\n항상 저희 블랙서클을 이용해 주셔서 감사드립니다."
}]

headers = {
    "content-type": "application/json",
    "userId": "dealertire2018"
}

response = requests.post(url, json=data, headers=headers)
print(response)
tokens = response.json()

print(tokens)
