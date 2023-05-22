import datetime
import json
import pymysql
import urllib3
from decimal import Decimal
import math
import random


def lambda_handler(event, context):
    if 'driver_info' not in event['body'] or 'order_id' not in event['body']:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    driver_info = event['body']['driver_info']
    order_id = event['body']['order_id']

    # 타입검사 & 변환
    if type(order_id) is int:
        order_id = str(order_id)

    if order_id:
        name = driver_info['name']  # 차주명
        phone_number = driver_info['phone_number']  # 연락처
        if type(phone_number) is int:
            phone_number = str(phone_number)

        connection = db_connect()
        cursor = connection.cursor()

        # 장바구니
        cursor.execute("SELECT cart_od_id, ct_qty, cart_io_no, ca_it_id, it_name, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type, od_name, od_tel, od_addr1, od_addr2, od_addr3, od_memo, seller_tel, clerk_tel1, clerk_tel2, clerk_tel3, seller_name, ct_id FROM "
                     "    ( SELECT *, it_id AS ca_it_id, io_no AS cart_io_no, od_id as cart_od_id FROM g5_shop_cart WHERE ct_logispot_id = '" + order_id + "') cart "
                     "    LEFT JOIN ( SELECT it_id, ca_id AS it_ca_id FROM g5_shop_item) item ON item.it_id = cart.ca_it_id "
                     "    LEFT JOIN ( SELECT io_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, origin_io_no, io_part_no FROM g5_shop_item_option) opt ON opt.io_no = cart.cart_io_no "
                     "    LEFT JOIN ( SELECT ca_id, ca_name FROM g5_shop_category WHERE  length(ca_id) = 4) category ON category.ca_id = item.it_ca_id "
                     "    LEFT JOIN ( SELECT mb_name as seller_name, mb_hp as seller_tel, mb_no as seller_no FROM g5_member WHERE mb_level = 8) mb_seller ON mb_seller.seller_no = cart.seller_mb_no "
                     "    LEFT JOIN ( SELECT *, mb_no as seller_mb_no from tbl_member_seller ) seller on seller.seller_mb_no=mb_seller.seller_no "
                     "    LEFT JOIN ( select od_name, od_tel, od_addr1, od_addr2, od_addr3, od_memo, od_id from g5_shop_order) od on od.od_id=cart.cart_od_id "
                     "ORDER BY ct_id ASC ")
        connection.commit()
        cart = cursor.fetchone()

        if cart is None:
            return {
                'statusCode': 202,
                'message': "order is not exist"
            }

        ct_id = cart[24]
        if type(ct_id) is int:
            ct_id = str(ct_id)

        # 번호저장
        cursor.execute("update g5_shop_cart set ct_invoice=%s where ct_id=%s", (phone_number, ct_id))
        connection.commit()

        od_id = cart[0]
        if type(od_id) is int:
            od_id = str(od_id)
        ct_qty = cart[1]
        if type(ct_qty) is int:
            ct_qty = str(ct_qty)
        it_name = cart[4]
        io_size_origin = cart[5]
        io_pr = cart[6]
        io_max_weight = cart[7]
        io_speed = cart[8]
        io_car_type = cart[9]
        io_maker = cart[10]
        io_oe = cart[11]
        io_tire_type = cart[12]
        od_name = cart[13]
        od_tel = cart[14]
        if type(od_tel) is int:
            od_tel = str(od_tel)
        od_addr1 = cart[15]
        od_addr2 = cart[16]
        od_addr3 = cart[17]
        od_memo = cart[18]
        seller_tel = cart[19]
        clerk_tel1 = cart[20]
        clerk_tel2 = cart[21]
        clerk_tel3 = cart[22]
        seller_name = cart[23]
        del_type = '퀵배송'
        option = io_size_origin + " | " + io_pr + " | " + io_max_weight + " | " + io_speed + " | " + io_car_type + " | " + io_maker + " | " + io_oe + " | " + io_tire_type
        addr = od_addr1 + " " + od_addr2 + " " + od_addr3

        cursor.close()
        connection.close()

        # 알림톡
        url = "https://alimtalk-api.bizmsg.kr/v2/sender/send"
        headers = {
            "content-type": "application/json",
            "userId": "dealertire2018"
        }
        http = urllib3.PoolManager()

        if (seller_tel):
            data = [{
                "message_type": "at",
                "phn": seller_tel,
                "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                "tmplId": "quick_completed",
                "msg": "[블랙서클] " + seller_name + "님, 📢" + del_type + "📢 퀵배송 배차가 완료되었어요!\n\n<주문정보>\n▶ 주문번호: " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n<퀵배송 정보>\n▶ 배송번호 : " + order_id + "\n▶ 운송기사 : " + name + "\n▶ 연락처 : " + phone_number + "\n\n알림톡 확인 후, 상품 출고 준비해주세요!"
            }]
            http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

        if (clerk_tel1):
            data = [{
                "message_type": "at",
                "phn": clerk_tel1,
                "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                "tmplId": "quick_completed",
                "msg": "[블랙서클] " + seller_name + "님, 📢" + del_type + "📢 퀵배송 배차가 완료되었어요!\n\n<주문정보>\n▶ 주문번호: " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n<퀵배송 정보>\n▶ 배송번호 : " + order_id + "\n▶ 운송기사 : " + name + "\n▶ 연락처 : " + phone_number + "\n\n알림톡 확인 후, 상품 출고 준비해주세요!"
            }]
            http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

        if (clerk_tel2):
            data = [{
                "message_type": "at",
                "phn": clerk_tel2,
                "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                "tmplId": "quick_completed",
                "msg": "[블랙서클] " + seller_name + "님, 📢" + del_type + "📢 퀵배송 배차가 완료되었어요!\n\n<주문정보>\n▶ 주문번호: " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n<퀵배송 정보>\n▶ 배송번호 : " + order_id + "\n▶ 운송기사 : " + name + "\n▶ 연락처 : " + phone_number + "\n\n알림톡 확인 후, 상품 출고 준비해주세요!"
            }]
            http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

        if (clerk_tel3):
            data = [{
                "message_type": "at",
                "phn": clerk_tel3,
                "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                "tmplId": "quick_completed",
                "msg": "[블랙서클] " + seller_name + "님, 📢" + del_type + "📢 퀵배송 배차가 완료되었어요!\n\n<주문정보>\n▶ 주문번호: " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n<퀵배송 정보>\n▶ 배송번호 : " + order_id + "\n▶ 운송기사 : " + name + "\n▶ 연락처 : " + phone_number + "\n\n알림톡 확인 후, 상품 출고 준비해주세요!"
            }]
            http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

        return {
            'statusCode': 200,
            'message': "완료"
        }

    return {
        'statusCode': 400,
        'message': "order_id is null"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles")

    return connection
