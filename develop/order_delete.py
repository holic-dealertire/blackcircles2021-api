import datetime
import json
import pymysql
import urllib3


def lambda_handler(event, context):
    mb_id = 'cardoc'
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d %H:%M:%S')

    if 'od_id' not in event or 'refund_request' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error"
        }

    od_id = event['od_id']
    seq = 0

    if type(od_id) is int:
        od_id = str(od_id)

    if od_id:
        connection = db_connect()
        cursor = connection.cursor()
        # 주문정보
        cursor.execute("select od_id, od_cart_count, od_mod_history, od_zip1, od_zip2, od_addr1, od_addr2, od_addr3, od_name from g5_shop_order where od_id=%s and mb_id=%s", (od_id, mb_id))
        connection.commit()
        order_info = cursor.fetchone()

        if order_info is None:
            return {
                'statusCode': 400,
                'message': "order not found"
            }

        row_count = cursor.rowcount
        length = len(event['refund_request'])
        od_cart_count = order_info[1]
        od_mod_history = order_info[2]
        od_zip1 = order_info[3]
        od_zip2 = order_info[4]
        od_addr1 = order_info[5]
        od_addr2 = order_info[6]
        od_addr3 = order_info[7]
        od_name = order_info[8]

        if row_count == 0 or length == 0:
            return {
                'statusCode': 400,
                'message': "order not found"
            }

        for i in range(length):
            io_part_no = event['refund_request'][i]['io_part_no']
            refund_reason = event['refund_request'][i]['refund_reason']
            ct_cancel_req_time = event['refund_request'][i]['ct_cancel_req_time']

            if io_part_no:
                cursor.execute("select io_no from g5_shop_item_option where io_part_no=%s", io_part_no)
                connection.commit()
                option_info = cursor.fetchone()
                if option_info is None:
                    return {
                        'statusCode': 202,
                        'message': "io_part_no is not exist"
                    }

                io_no = option_info[0]

                cursor.execute("select ct_id, ct_status, io_price, ct_qty, stock_idx, seller_mb_no from g5_shop_cart where od_id=%s and io_no=%s and mb_id=%s", (od_id, io_no, mb_id))
                connection.commit()
                cart_info = cursor.fetchone()
                cart_count = cursor.rowcount
                ct_id = cart_info[0]
                ct_status = cart_info[1]
                io_price = cart_info[2]
                ct_qty = cart_info[3]
                stock_idx = int(cart_info[4])
                seller_mb_no = cart_info[5]
                refund_price = int(io_price) * int(ct_qty)
                od_mod_history = od_mod_history + "\n" + ct_cancel_req_time + " " + str(ct_id) + " 구매자 주문취소"
                ct_qty = str(ct_qty)

                if cart_count == 0:
                    continue

                if ct_status == '확정':
                    return {
                        'statusCode': 403,
                        'message': "취소할 수 없는 주문입니다."
                    }

                if ct_status == '취소' or ct_status == '취소요청':
                    return {
                        'statusCode': 404,
                        'message': "이미 " + ct_status + " 된 주문입니다"
                    }

                if ct_status == '입금':  # 취소처리
                    # 재고조정
                    cursor.execute("update tbl_item_option_price_stock set stock = stock + %s where idx=%s", (ct_qty, stock_idx))
                    connection.commit()

                    # cart 수정
                    cursor.execute("update g5_shop_cart set refund_reason=%s, ct_status='취소' where ct_id=%s", (refund_reason, ct_id))
                    connection.commit()

                    # 주문서 수정
                    if od_cart_count > 1:
                        cursor.execute("update g5_shop_order set od_cancel_price=od_cancel_price + %s, od_mod_history=%s where od_id=%s", (refund_price, od_mod_history, od_id))
                        connection.commit()

                    # 주문서 취소 가능 여부 확인
                    cursor.execute("select count(*) as cnt from g5_shop_cart where od_id=%s and ct_status != '취소'", od_id)
                    connection.commit()
                    cart = cursor.fetchone()
                    if cart[0] == 0:
                        cursor.execute("update g5_shop_order set od_status='취소' where od_id=%s", od_id)
                        connection.commit()

                    # 알림톡
                    url = "https://alimtalk-api.bizmsg.kr/v2/sender/send"
                    headers = {
                        "content-type": "application/json",
                        "userId": "dealertire2018"
                    }
                    http = urllib3.PoolManager()

                    cursor.execute("select it_name, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type from (select io_no as cart_io_no, it_id as cart_it_id, ct_qty, it_name from g5_shop_cart where ct_id = %s) cart left join (select io_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type from g5_shop_item_option) opt on opt.io_no=cart.cart_io_no", ct_id)
                    connection.commit()
                    item_info = cursor.fetchone()
                    it_name = item_info[0]
                    io_size_origin = item_info[1]
                    io_pr = item_info[2]
                    io_max_weight = item_info[3]
                    io_speed = item_info[4]
                    io_car_type = item_info[5]
                    io_maker = item_info[6]
                    io_oe = item_info[7]
                    io_tire_type = item_info[8]
                    option = io_size_origin + " | " + io_pr + " | " + io_max_weight + " | " + io_speed + " | " + io_car_type + " | " + io_maker + " | " + io_oe + " | " + io_tire_type
                    addr = "[" + od_zip1 + od_zip2 + "] " + od_addr1 + " " + od_addr2 + " " + od_addr3
                    del_type = "택배"
                    od_tel = "카닥 주문건입니다. 블랙서클 담당자가 연락드리겠습니다."

                    cursor.execute("select mb_hp, clerk_tel1, clerk_tel2, clerk_tel3 from (select mb_no, mb_hp from g5_member where mb_no = %s) mb left join (select mb_no as seller_mb_no, clerk_tel1, clerk_tel2, clerk_tel3 from tbl_member_seller) seller on seller.seller_mb_no=mb.mb_no", seller_mb_no)
                    connection.commit()
                    seller = cursor.fetchone()
                    if seller[0]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[0],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[1]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[1],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[2]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[2],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[3]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[3],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    data = [{
                        "message_type": "at",
                        "phn": "01032845508",
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_cancel_02",
                        "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    data = [{
                        "message_type": "at",
                        "phn": "01056275408",
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_cancel_02",
                        "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)
                    seq = 1

                else:  # 취소요청처리, 이찬호+총판 알림톡
                    # cart 수정
                    cursor.execute("update g5_shop_cart set refund_reason=%s, ct_status='취소요청' where ct_id=%s", (refund_reason, ct_id))
                    connection.commit()

                    # 주문서 수정
                    if od_cart_count > 1:
                        cursor.execute("update g5_shop_order set od_mod_history=%s where od_id=%s", (od_mod_history, od_id))
                        connection.commit()

                    url = "https://alimtalk-api.bizmsg.kr/v2/sender/send"
                    headers = {
                        "content-type": "application/json",
                        "userId": "dealertire2018"
                    }
                    http = urllib3.PoolManager()

                    cursor.execute("select it_name, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type from (select io_no as cart_io_no, it_id as cart_it_id, ct_qty, it_name from g5_shop_cart where ct_id = %s) cart left join (select io_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type from g5_shop_item_option) opt on opt.io_no=cart.cart_io_no", ct_id)
                    connection.commit()
                    item_info = cursor.fetchone()
                    it_name = item_info[0]
                    io_size_origin = item_info[1]
                    io_pr = item_info[2]
                    io_max_weight = item_info[3]
                    io_speed = item_info[4]
                    io_car_type = item_info[5]
                    io_maker = item_info[6]
                    io_oe = item_info[7]
                    io_tire_type = item_info[8]
                    option = io_size_origin + " | " + io_pr + " | " + io_max_weight + " | " + io_speed + " | " + io_car_type + " | " + io_maker + " | " + io_oe + " | " + io_tire_type
                    addr = "[" + od_zip1 + od_zip2 + "] " + od_addr1 + " " + od_addr2 + " " + od_addr3
                    del_type = "택배"
                    od_tel = "카닥 주문건입니다. 블랙서클 담당자가 연락드리겠습니다."

                    cursor.execute("select mb_hp, clerk_tel1, clerk_tel2, clerk_tel3 from (select mb_no, mb_hp from g5_member where mb_no = %s) mb left join (select mb_no as seller_mb_no, clerk_tel1, clerk_tel2, clerk_tel3 from tbl_member_seller) seller on seller.seller_mb_no=mb.mb_no", seller_mb_no)
                    connection.commit()
                    seller = cursor.fetchone()
                    if seller[0]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[0],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[1]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[1],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[2]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[2],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[3]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[3],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_cancel_02",
                            "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    data = [{
                        "message_type": "at",
                        "phn": "01032845508",
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_cancel_02",
                        "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    data = [{
                        "message_type": "at",
                        "phn": "01056275408",
                        "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                        "tmplId": "renew_order_cancel_02",
                        "msg": "[블랙서클] 구매자가 주문을 취소하였습니다.\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + ct_qty + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 취소사유 : " + refund_reason + ""
                    }]
                    http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)
                    seq = 2

        cursor.close()
        connection.close()

    if seq == 1:
        return {
            'statusCode': 200,
            'message': "주문이 정상 취소되었습니다."
        }
    elif seq == 2:
        return {
            'statusCode': 210,
            'message': "주문이 정상 취소요청 되었습니다."
        }

    return {
        'statusCode': 400,
        'message': "Invalid ID supplied"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles")

    return connection
