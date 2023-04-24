import json
import pymysql


def lambda_handler(event, context):
    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute("select mb_no, mb_id, mb_name from g5_member where 1 order by mb_no asc")
    connection.commit()
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d %H:%M:%S')
    print(today)

    url = "https://alimtalk-api.bizmsg.kr/v2/sender/send"
    headers = {
        "content-type": "application/json",
        "userId": "dealertire2018"
    }
    http = urllib3.PoolManager()

    data = [{
        "message_type": "at",
        "phn": seller[0],
        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
        "tmplId": "renew_order_04_01",
        "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(input_ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
    }]
    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

    return {
        'statusCode': 200,
        'body': json.dumps(rows)
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection
