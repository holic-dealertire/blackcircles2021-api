import datetime
import json
import pymysql
import urllib3

def lambda_handler(event, context):
    mb_id = 'cardoc'
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

    if 'od_id' not in event or 'od_name' not in event or 'od_tel' not in event or 'od_zip' not in event or 'od_addr1' not in event or 'od_addr2' not in event or 'od_addr3' not in event or 'cart_item' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error"
        }

    od_id = event['od_id']
    od_name = event['od_name']
    od_tel = event['od_tel']
    od_addr1 = event['od_addr1']
    od_addr2 = event['od_addr2']
    od_addr3 = event['od_addr3']
    od_reserv_date = event['od_reserv_date']
    od_memo = ''
    od_zip = event['od_zip']
    od_zip1 = ''
    od_zip2 = ''
    if od_zip:
        od_zip1 = od_zip[:3]
        od_zip2 = od_zip[-2:]

    # 타입검사 & 변환
    if type(od_id) is int:
        od_id = str(od_id)
    else:
        return {
            'statusCode': 402,
            'message': "parameter error"
        }

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
        tot_price = 0
        if row_count != 0:  # ㅇㅇ
            return {
                'statusCode': 201,
                'message': "od_id is already exist"
            }
        else:
            length = len(event['cart_item'])
            od_receipt_price = 0
            for i in range(length):
                io_part_no = event['cart_item'][i]['io_part_no']
                ct_qty = int(event['cart_item'][i]['ct_qty'])
                cursor.execute("select io_btob_price from g5_shop_item_option where io_part_no=%s", io_part_no)
                connection.commit()
                option_info = cursor.fetchone()

                if option_info is None:
                    return {
                        'statusCode': 202,
                        'message': "io_part_no is not exist"
                    }

                io_btob_price = option_info[0]
                if type(od_name) is str:
                    io_btob_price = int(io_btob_price)

                od_receipt_price += io_btob_price * ct_qty

            for i in range(length):
                io_part_no = event['cart_item'][i]['io_part_no']
                ct_qty = int(event['cart_item'][i]['ct_qty'])
                if io_part_no and ct_qty:
                    cursor.execute("select io_no, it_id, delivery_idx, delivery_seller_no, sale_delivery, it_name, delivery_collect, io_size, io_id, delivery_price1, io_factory_price, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type, idx "
                                   "    from (select io_no, it_id as io_it_id, io_btob_price, io_btob_lowest, io_size, io_id, io_factory_price, io_size_origin, io_pr, io_max_weight, io_speed, io_car_type, io_maker, io_oe, io_tire_type from g5_shop_item_option where io_part_no=%s and io_btob_price is not null and io_btob_lowest is not null) opt left join (select it_id, ca_id as it_ca_id, it_name from g5_shop_item) item on opt.io_it_id=item.it_id"
                                   "    left join ("
                                   "                select * from ("
                                   "                                    select * from ("
                                   "                                                        select idx, io_no as stock_io_no, mb_no as delivery_seller_no, sale_delivery, stock, idx as delivery_idx, delivery_price as delivery_price1, delivery_collect from tbl_item_option_price_stock where stock > %s"
                                   "                                                  ) stock"
                                   "                                    left join (select io_no as check_io_no, it_id as check_io_it_id, io_btob_lowest as check_btob_lowest from g5_shop_item_option where io_part_no=%s) check_option on check_option.check_io_no=stock.stock_io_no"
                                   "                                    left join (select it_id as check_it_id, ca_id as check_ca_id from g5_shop_item) check_item on check_item.check_it_id=check_option.check_io_it_id"
                                   "                                    left join (select ca_id as contract_ca_id, mb_no as contract_mb_no, idx as contract_idx from tbl_member_seller_item_contract where contract_status='1' and contract_start <= %s and contract_end >= %s) contract on contract.contract_mb_no=stock.delivery_seller_no and contract.contract_ca_id=check_item.check_ca_id"
                                   "                                    where contract_idx is not null and check_btob_lowest <= sale_delivery"
                                   "                                    order by sale_delivery desc, delivery_price1 asc, stock desc"
                                   "                              ) stock"
                                   "                 group by stock.stock_io_no"
                                   "           ) as delivery_price"
                                   " on delivery_price.stock_io_no=opt.io_no", (io_part_no, ct_qty, io_part_no, nowDate, nowDate))
                    connection.commit()
                    option_info = cursor.fetchone()

                    if option_info is None:
                        return {
                            'statusCode': 202,
                            'message': "io_part_no is not exist"
                        }

                    if option_info[4] is None:
                        return {
                            'statusCode': 405,
                            'message': "not enough stock io_part_no : " + io_part_no
                        }

                    io_no = option_info[0]
                    it_id = option_info[1]
                    delivery_idx = option_info[2]
                    seller_mb_no = option_info[3]
                    sale = int(option_info[4])
                    it_name = option_info[5]
                    delivery_collect = option_info[6]
                    io_size = option_info[7]
                    io_id = option_info[8]
                    delivery_price = option_info[9]
                    io_factory_price = int(option_info[10])
                    io_size_origin = option_info[11]
                    io_pr = option_info[12]
                    io_max_weight = option_info[13]
                    io_speed = option_info[14]
                    io_car_type = option_info[15]
                    io_maker = option_info[16]
                    io_oe = option_info[17]
                    io_tire_type = option_info[18]
                    idx = option_info[19]
                    option = io_size_origin + " | " + io_pr + " | " + io_max_weight + " | " + io_speed + " | " + io_car_type + " | " + io_maker + " | " + io_oe + " | " + io_tire_type
                    del_type = "택배"
                    addr = "[" + od_zip1 + od_zip2 + "] " + od_addr1 + " " + od_addr2 + " " + od_addr3

                    price = io_factory_price
                    if sale > 0:
                        price = round(io_factory_price - (io_factory_price / 100 * sale), -3)

                    tot_price += price
                    it_sc_price = delivery_price
                    it_sc_type = '1'
                    if it_sc_price > 0 and delivery_collect == '0':
                        it_sc_type = '3'

                    cursor.execute("insert into g5_shop_cart set od_id=%s, mb_id=%s, it_id=%s, it_name=%s, it_sc_type=%s, it_sc_method='0', it_delv_type='2', it_sc_price=%s, it_sc_minimum='0', it_sc_qty='0', ct_status='입금', ct_price='0', ct_sale=%s, ct_point='0', ct_point_use='0', ct_stock_use='1', ct_option=%s, ct_qty=%s, ct_notax='0', io_no=%s, io_id=%s, io_type='1', io_price=%s, ct_time=%s, ct_send_cost='0', ct_direct='0', ct_select='1', ct_select_time=%s, stock_idx=%s, "
                                   "seller_mb_no=%s, ct_orderable='1'", (od_id, mb_id, it_id, it_name, it_sc_type, it_sc_price, sale, io_size, ct_qty, io_no, io_id, price, nowDatetime, nowDatetime, delivery_idx, seller_mb_no))
                    connection.commit()

                    cursor.execute("update tbl_item_option_price_stock set stock = stock - %s where idx = %s", (str(ct_qty), idx))
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
                            "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[1]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[1],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_04_01",
                            "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[2]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[2],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_04_01",
                            "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

                    if seller[3]:
                        data = [{
                            "message_type": "at",
                            "phn": seller[3],
                            "profile": "dd12d9e5886c35b5d6918831e0257d8e93a72c61",
                            "tmplId": "renew_order_04_01",
                            "msg": "[블랙서클] " + seller_mb_name + "님, 주문이 정상 접수되었어요!\n▶ 주문번호 : " + od_id + "\n▶ 상품명 : " + it_name + "\n▶ 옵션 : " + option + "\n▶ 주문수량 : " + str(ct_qty) + "개\n▶ 배송방식 : " + del_type + "\n▶ 배송지 : " + od_name + "\n" + addr + "\n▶ 구매자연락처 : " + od_tel + "\n▶ 주문요청사항 : " + od_memo + "\n\n알림톡 확인 후, 판매자 페이지에서 주문상태를 " + msg + "으로 바꿔주세요!"
                        }]
                        http.request('POST', url, body=json.dumps(data), headers=headers, retries=False)

            cursor.execute("insert into g5_shop_order set od_id=%s, mb_id=%s, od_pwd='', od_name=%s, od_email='', od_tel=%s, od_hp=%s, od_zip1=%s, od_zip2=%s, od_addr1=%s, od_addr2=%s, od_addr3=%s, od_addr_jibeon='', od_b_name=%s, od_b_tel=%s, od_b_hp=%s, od_b_zip1=%s, od_b_zip2=%s, od_b_addr1=%s, od_b_addr2=%s, od_b_addr3=%s, od_b_addr_jibeon='', od_deposit_name=%s, od_cart_count=%s, od_cart_price=%s, od_cart_coupon=0, od_send_cost=0, od_send_cost2=0, od_coupon=0, "
                           "od_cal_coupon_point=0, od_receipt_price=%s, od_receipt_point=0, od_bank_account='', od_receipt_time=%s, od_misu=0, od_pg='cardoc', od_tno='', od_app_no='cardoc', od_escrow='', od_tax_flag='', od_tax_mny='', od_vat_mny='', od_free_mny='', od_status='입금', od_shop_memo='', od_hope_date='', od_time=%s, od_settle_case='cardoc', od_test='', od_vbank_expire='', od_reserv_date=%s",
                           (od_id, mb_id, od_name, od_tel, od_tel, od_zip1, od_zip2, od_addr1, od_addr2, od_addr3, od_name, od_tel, od_tel, od_zip1, od_zip2, od_addr1, od_addr2, od_addr3, od_name, length, tot_price, od_receipt_price, nowDatetime, nowDatetime, od_reserv_date))
            connection.commit()

            return {
                'statusCode': 200,
                'message': "주문 생성이 완료되었습니다."
            }

    return {
        'statusCode': 400,
        'message': "od_id is null"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_dev")

    return connection