import datetime
import json
import pymysql
import urllib3
from decimal import Decimal
import math
import random


def lambda_handler(event, context):
    if 'event_type' not in event['body'] or 'event_at' not in event['body'] or 'order_id' not in event['body']:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    event_type = event['body']['event_type']
    event_at = event['body']['event_at']
    order_id = event['body']['order_id']

    # 타입검사 & 변환
    if type(event_type) is str:
        event_type = int(event_type)

    if type(order_id) is str:
        order_id = int(order_id)

    if order_id:
        connection = db_connect()
        cursor = connection.cursor()

        if event_type == 1000:
            cursor.execute("update g5_shop_cart set ct_status='배송', ct_invoice_time = now() where ct_logispot_id=%s and ct_status='입금'", order_id)
        if event_type == 2000:
            cursor.execute("update g5_shop_cart set ct_status='완료', ct_complete_time = now() where ct_logispot_id=%s and ct_status='배송'", order_id)

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
