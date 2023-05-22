import datetime
import json
import pymysql
import urllib3
from decimal import Decimal
import math
import random


def lambda_handler(event, context):
    if 'member_id' not in event['queryParams']:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    mb_id = event['queryParams']['member_id']
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

    if 'od_id' not in event['body'] or 'od_name' not in event['body'] or 'od_tel' not in event['body'] or 'od_zip' not in event['body'] or 'od_addr1' not in event['body'] or 'od_addr2' not in event['body'] or 'od_addr3' not in event['body'] or 'cart_item' not in event['body']:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    od_id = event['body']['od_id']
    od_name = event['body']['od_name']
    od_tel = event['body']['od_tel']
    od_addr1 = event['body']['od_addr1']
    od_addr2 = event['body']['od_addr2']
    od_addr3 = event['body']['od_addr3']
    od_reserv_date = event['body']['od_reserv_date']
    od_memo = ''
    if 'od_memo' in event['body']:
        od_memo = event['body']['od_memo']

    od_zip = event['body']['od_zip']
    od_zip1 = ''
    od_zip2 = ''
    if od_zip:
        od_zip1 = od_zip[:3]
        od_zip2 = od_zip[-2:]

    # 타입검사 & 변환
    if type(od_id) is int:
        od_id = str(od_id)

    if type(od_name) is int or type(od_addr1) is int or type(od_addr2) is int:
        return {
            'statusCode': 402,
            'message': "parameter error"
        }

    if od_id:
        connection = db_connect()
        cursor = connection.cursor()
        # 주문번호 중복 확인
        cursor.execute("select od_id from g5_shop_order where od_id=%s", od_id)
        connection.commit()
        order_info = cursor.fetchone()
        row_count = cursor.rowcount
        if row_count != 0:
            return {
                'statusCode': 201,
                'message': "od_id is already exist"
            }
        else:
            cursor.execute("select retail_type from (SELECT mb_no FROM g5_member WHERE mb_id ='" + mb_id + "' and mb_level = 5 and mb_14 = 1) member left join (select mb_no as retail_mb_no, retail_type from tbl_member_retail) retail on retail.retail_mb_no=member.mb_no")
            connection.commit()
            retail_type = cursor.fetchone()
            if retail_type is None:
                return {
                    'statusCode': 202,
                    'message': "member_id is not exist"
                }

            length = len(event['body']['cart_item'])
            od_receipt_price = 0
            tot_price = 0
            for i in range(length):
                input_io_part_no = event['body']['cart_item'][i]['io_part_no']
                input_ct_qty = event['body']['cart_item'][i]['ct_qty']
                input_ct_sale = event['body']['cart_item'][i]['ct_sale']
                input_seller_no = event['body']['cart_item'][i]['seller_no']
                input_it_sc_price = event['body']['cart_item'][i]['it_sc_price']

                if type(input_io_part_no) is int:
                    input_io_part_no = str(input_io_part_no)
                if type(input_seller_no) is int:
                    input_seller_no = str(input_seller_no)
                if type(input_ct_qty) is str:
                    input_ct_qty = int(input_ct_qty)
                if type(input_ct_sale) is str:
                    input_ct_sale = int(input_ct_sale)
                if type(input_it_sc_price) is str:
                    input_it_sc_price = int(input_it_sc_price)

                cursor.execute("""
                select io_no, io_delivery_price, io_sell_price_premium, range_1, range_2, range_3 FROM (
                                       SELECT io_no, it_id AS io_it_id, io_delivery_price, io_sell_price_premium
                                   FROM   g5_shop_item_option
                                   WHERE  io_part_no = %s) opt
                            LEFT JOIN
                            (
                                   SELECT it_id, ca_id AS it_ca_id
                                   FROM   g5_shop_item) item ON item.it_id=opt.io_it_id
                            LEFT JOIN
                            (
                                   SELECT ca_id, range_1, range_2, range_3
                                   FROM   g5_shop_category) cate ON cate.ca_id=item.it_ca_id
                            WHERE cate.ca_id IS NOT NULL
                """, input_io_part_no)
                connection.commit()
                io_info = cursor.fetchone()
                if io_info is None:
                    return {
                        'statusCode': 202,
                        'message': "io_part_no is not exist"
                    }
                io_no = io_info[0]
                io_delivery_price = io_info[1]
                io_sell_price_premium = io_info[2]
                range_1 = io_info[3]
                range_2 = io_info[4]
                range_3 = io_info[5]
                if io_no is None or range_1 is None or io_sell_price_premium is None:
                    return {
                        'statusCode': 402,
                        'message': "parameter error"
                    }
                if input_ct_qty < 1:
                    return {
                        'statusCode': 420,
                        'message': "ct_qty must be at least 1"
                    }
                input_tot_delivery_price = input_it_sc_price
                tot_delivery_price = io_delivery_price * input_ct_qty
                if input_tot_delivery_price != tot_delivery_price:
                    return {
                        'statusCode': 421,
                        'message': "delivery_price does not match"
                    }

                cursor.execute("""select sale_delivery, stock, idx from tbl_item_option_price_stock where mb_no = %s and io_no = %s""", (input_seller_no, io_no))
                connection.commit()
                sale_info = cursor.fetchone()
                if sale_info is None:
                    return {
                        'statusCode': 422,
                        'message': "seller's sale is not exist"
                    }
                seller_sale_delivery = sale_info[0]
                seller_stock = sale_info[1]
                seller_stock_idx = sale_info[2]

                if input_ct_sale < seller_sale_delivery and (input_ct_sale == io_sell_price_premium or input_ct_sale == io_sell_price_premium - range_1 or input_ct_sale == io_sell_price_premium - range_1 - range_2 or input_ct_sale == io_sell_price_premium - range_1 - range_2 - range_3 or input_ct_sale == seller_sale_delivery - 2):
                    ordered_sale = seller_sale_delivery
                else:
                    return {
                        'statusCode': 423,
                        'message': "seller's sale does not match"
                    }

                if input_ct_qty > seller_stock:
                    return {
                        'statusCode': 424,
                        'message': "seller's stock not enough"
                    }

                cursor.execute("""select io_no, it_id, it_name, io_size, io_id, io_factory_price, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type 
                                from (select io_no, it_id as io_it_id, io_size, io_id, io_factory_price, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type from g5_shop_item_option where io_no=%s) opt left join (select it_id, ca_id as it_ca_id, it_name from g5_shop_item) item on opt.io_it_id=item.it_id
                               """, io_no)
                connection.commit()
                option_info = cursor.fetchone()

                if option_info is None:
                    return {
                        'statusCode': 202,
                        'message': "io_part_no is not exist"
                    }

                io_no = option_info[0]
                it_id = option_info[1]
                delivery_idx = seller_stock_idx
                seller_mb_no = input_seller_no
                sale = input_ct_sale
                it_name = option_info[2]
                delivery_collect = '0'
                io_size = option_info[3]
                io_id = option_info[4]
                delivery_price = io_delivery_price
                io_factory_price = int(option_info[5])
                io_size_origin = option_info[6]
                io_pr = option_info[7]
                io_max_weight = option_info[8]
                io_speed = option_info[9]
                io_car_type = option_info[10]
                io_maker = option_info[11]
                io_oe = option_info[12]
                io_tire_type = option_info[13]
                idx = seller_stock_idx
                option = io_size_origin + " | " + io_pr + " | " + io_max_weight + " | " + io_speed + " | " + io_car_type + " | " + io_maker + " | " + io_oe + " | " + io_tire_type
                del_type = "택배"
                addr = "[" + od_zip1 + od_zip2 + "] " + od_addr1 + " " + od_addr2 + " " + od_addr3

                price = io_factory_price
                if sale > 0:
                    price = round(io_factory_price - (io_factory_price / 100 * sale), -3)

                tot_price += price
                it_sc_price = delivery_price
                it_sc_price = it_sc_price * input_ct_qty
                od_receipt_price += (price * input_ct_qty) + it_sc_price
                it_sc_type = '1'
                if it_sc_price > 0 and delivery_collect == '0':
                    it_sc_type = '3'

                cursor.execute(
                    """insert into g5_shop_cart set 
                                                od_id=%s, 
                                                mb_id=%s, 
                                                it_id=%s, 
                                                it_name=%s, 
                                                it_sc_type=%s, 
                                                it_sc_method='0', 
                                                it_delv_type='2', 
                                                it_sc_price=%s, 
                                                it_sc_minimum='0', 
                                                it_sc_qty='0', 
                                                ct_status='입금', 
                                                ct_price='0', 
                                                ct_sale=%s, 
                                                ct_point='0', 
                                                ct_point_use='0', 
                                                ct_stock_use='1', 
                                                ct_option=%s, 
                                                ct_qty=%s, 
                                                ct_notax='0', 
                                                io_no=%s, 
                                                io_id=%s, 
                                                io_type='1', 
                                                io_price=%s, 
                                                ct_time=%s, 
                                                ct_send_cost='0', 
                                                ct_direct='0', 
                                                ct_select='1', 
                                                ct_select_time=%s, 
                                                stock_idx=%s, 
                                                seller_mb_no=%s, 
                                                ct_orderable='1', 
                                                ordered_sale=%s,
                                                ct_factory_price=%s
                                                """,
                    (od_id, mb_id, it_id, it_name, it_sc_type, it_sc_price, sale, io_size, input_ct_qty, io_no, io_id, price, nowDatetime, nowDatetime, delivery_idx, seller_mb_no, ordered_sale, io_factory_price))
                connection.commit()

                cursor.execute("update tbl_item_option_price_stock set stock = stock - %s where idx = %s", (str(input_ct_qty), idx))
                connection.commit()

                # 알림톡
                url = "https://alimtalk-api.bizmsg.kr/v2/sender/send"
                headers = {
                    "content-type": "application/json",
                    "userId": "dealertire2018"
                }
                http = urllib3.PoolManager()

                cursor.execute("select mb_hp, clerk_tel1, clerk_tel2, clerk_tel3, mb_name from (select mb_no, mb_hp, mb_name from g5_member where mb_no = %s) mb left join (select mb_no as seller_mb_no, clerk_tel1, clerk_tel2, clerk_tel3 from tbl_member_seller) seller on seller.seller_mb_no=mb.mb_no", seller_mb_no)
                connection.commit()
                seller = cursor.fetchone()
                seller_mb_name = seller[4]
                msg = "<상품준비중>"

                if seller[0]:
                    data = [{
                        "message_type": "at",
                        "phn": seller[0],
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_04_01",
                        "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(input_ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                if seller[1]:
                    data = [{
                        "message_type": "at",
                        "phn": seller[1],
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_04_01",
                        "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(input_ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                if seller[2]:
                    data = [{
                        "message_type": "at",
                        "phn": seller[2],
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_04_01",
                        "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(input_ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                if seller[3]:
                    data = [{
                        "message_type": "at",
                        "phn": seller[3],
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_04_01",
                        "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(input_ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

            cursor.execute(
                "insert into g5_shop_order set od_id=%s, mb_id=%s, od_pwd='', od_name=%s, od_email='', od_tel=%s, od_hp=%s, od_zip1=%s, od_zip2=%s, od_addr1=%s, od_addr2=%s, od_addr3=%s, od_addr_jibeon='', od_b_name=%s, od_b_tel=%s, od_b_hp=%s, od_b_zip1=%s, od_b_zip2=%s, od_b_addr1=%s, od_b_addr2=%s, od_b_addr3=%s, od_b_addr_jibeon='', od_deposit_name=%s, od_cart_count=%s, od_cart_price=%s, od_cart_coupon=0, od_send_cost=0, od_send_cost2=0, od_coupon=0, "
                "od_cal_coupon_point=0, od_receipt_price=%s, od_receipt_point=0, od_bank_account='', od_receipt_time=%s, od_misu=0, od_pg='api', od_tno='', od_app_no='api', od_escrow='', od_tax_flag='', od_tax_mny='', od_vat_mny='', od_free_mny='', od_status='입금', od_shop_memo='', od_hope_date='', od_time=%s, od_settle_case='api', od_test='', od_vbank_expire='', od_reserv_date=%s",
                (od_id, mb_id, od_name, od_tel, od_tel, od_zip1, od_zip2, od_addr1, od_addr2, od_addr3, od_name, od_tel, od_tel, od_zip1, od_zip2, od_addr1, od_addr2, od_addr3, od_name, length, tot_price, od_receipt_price, nowDatetime, nowDatetime, od_reserv_date))
            connection.commit()
            connection.close()

            return {
                'statusCode': 200,
                'message': "주문 생성이 완료되었습니다."
            }

    return {
        'statusCode': 400,
        'message': "od_id is null"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles")

    return connection