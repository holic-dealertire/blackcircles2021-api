import json
import pymysql
import urllib.request
import math
from datetime import datetime, timedelta


def lambda_handler(event, context):
    if 'event_type' not in event['body'] or 'event_at' not in event['body'] or 'order_id' not in event['body']:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    event_type = event['body']['event_type']
    order_id = event['body']['order_id']

    # 타입검사 & 변환
    if type(event_type) is str:
        event_type = int(event_type)

    if type(order_id) is str:
        order_id = int(order_id)

    if order_id:
        connection = db_connect()
        cursor = connection.cursor()

        cursor.execute("select seller_lng, seller_lat, retail_lng, retail_lat from (select * from g5_shop_cart where ct_logispot_id = %s) cart left join (select mb_id as retail_mb_id, mb_lat as retail_lat, mb_lng as retail_lng from g5_member where mb_level >= 5) retail on retail.retail_mb_id=cart.mb_id left join (select mb_no, mb_lat as seller_lat, mb_lng as seller_lng from g5_member where mb_level >= 8) seller on seller.mb_no=cart.seller_mb_no", order_id)
        connection.commit()
        order_info = cursor.fetchone()
        seller_lng = order_info[0]
        seller_lat = order_info[1]
        retail_lng = order_info[2]
        retail_lat = order_info[3]

        if event_type == 1000:
            time = naver_direction_api(seller_lat, seller_lng, retail_lat, retail_lng)
            cursor.execute("update g5_shop_cart set ct_status='배송', ct_invoice_time = now(), ct_within_invoice_time = %s where ct_logispot_id=%s and ct_status='준비'", (time, order_id))
        if event_type == 2000:
            cursor.execute("update g5_shop_cart set ct_status='완료', ct_complete_time = now() where ct_logispot_id=%s and (ct_status='배송' or ct_status = '준비')", order_id)

        connection.commit()
        connection.close()

        return {
            'statusCode': 200,
            'message': "업데이트 완료"
        }

    return {
        'statusCode': 400,
        'message': "order_id is null"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection


def naver_direction_api(start_lat, start_lng, end_lat, end_lng):
    option = 'traavoidcaronly'
    client_id = 'a7mm5vkrds'
    client_secret = 'LWJIRrEtCwG9eVCZMGFAiEl6uAzMQc2mIDCKeICV'
    url = f"https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?start={end_lng},{end_lat}&goal={start_lng},{start_lat}&option={option}"
    url = url.replace(" ", "%20")
    request = urllib.request.Request(url)
    request.add_header('X-NCP-APIGW-API-KEY-ID', client_id)
    request.add_header('X-NCP-APIGW-API-KEY', client_secret)

    response = urllib.request.urlopen(request)
    response_body = response.read().decode('utf-8')
    results = json.loads(response_body)
    now = datetime.now()
    duration = results['route']['traavoidcaronly'][0]['summary']['duration']
    complete_time = now + timedelta(minutes=30) + timedelta(milliseconds=duration)
    minutes = complete_time.minute
    minutes = math.ceil(int(minutes) / 10) * 10
    hours = complete_time.hour
    if minutes >= 60:
        minutes = minutes - 60
        hours = hours + 1
    return str(hours) + ":" + str(minutes).zfill(2)
