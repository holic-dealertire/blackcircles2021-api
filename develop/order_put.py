import datetime
import json
import pymysql


def lambda_handler(event, context):
    if 'member_id' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    mb_id = event['member_id']
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d %H:%M:%S')

    if 'od_id' not in event or 'od_name' not in event or 'od_tel' not in event or 'od_zip' not in event or 'od_addr1' not in event or 'od_addr2' not in event or 'od_addr3' not in event or 'cart_status' not in event:
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

        cursor.execute("select retail_type from (SELECT mb_no FROM g5_member WHERE mb_id ='" + mb_id + "' and mb_level = 5 and mb_14 = 1) member left join (select mb_no as retail_mb_no, retail_type from tbl_member_retail) retail on retail.retail_mb_no=member.mb_no")
        connection.commit()
        retail_type = cursor.fetchone()
        if retail_type is None:
            return {
                'statusCode': 202,
                'message': "member_id is not exist"
            }

        # 주문정보
        cursor.execute("select od_name, od_tel, concat(od_zip1, od_zip2) as od_zip, od_addr1, od_addr2, od_addr3, od_memo, od_receipt_price, od_time from g5_shop_order where od_id=%s and mb_id=%s", (od_id, mb_id))
        connection.commit()
        order_info = cursor.fetchone()

        if order_info is None:
            return {
                'statusCode': 400,
                'message': "order not found"
            }

        row_count = cursor.rowcount
        length = 0
        cart_status = event.get('cart_status')
        if cart_status:
            length = len(cart_status)

        if row_count == 0:
            return {
                'statusCode': 404,
                'message': "order not found"
            }

        if od_name and od_name != order_info[0]:
            cursor.execute("update g5_shop_order set od_name=%s where od_id=%s", (od_name, od_id))
            connection.commit()

        if od_tel and od_tel != order_info[1]:
            cursor.execute("update g5_shop_order set od_tel=%s where od_id=%s", (od_tel, od_id))
            connection.commit()

        if od_zip and od_zip != order_info[2]:
            od_zip1 = od_zip[:3]
            od_zip2 = od_zip[-2:]
            cursor.execute("update g5_shop_order set od_zip1=%s, od_zip2=%s where od_id=%s", (od_zip1, od_zip2, od_id))
            connection.commit()

        if od_addr1 and od_addr1 != order_info[3]:
            cursor.execute("update g5_shop_order set od_addr1=%s where od_id=%s", (od_addr1, od_id))
            connection.commit()

        if od_addr2 and od_addr2 != order_info[4]:
            cursor.execute("update g5_shop_order set od_addr2=%s where od_id=%s", (od_addr2, od_id))
            connection.commit()

        if od_addr3 and od_addr3 != order_info[5]:
            cursor.execute("update g5_shop_order set od_addr3=%s where od_id=%s", (od_addr3, od_id))
            connection.commit()

        for i in range(length):
            io_part_no = event['cart_status'][i]['io_part_no']
            ct_status = event['cart_status'][i]['ct_status']
            if io_part_no is not None:
                cursor.execute("select io_no from g5_shop_item_option where io_part_no=%s", io_part_no)
                connection.commit()
                option_info = cursor.fetchone()
                io_no = option_info[0]

                cursor.execute("select ct_id, ct_status, ct_history from g5_shop_cart where od_id=%s and io_no=%s and mb_id=%s", (od_id, io_no, mb_id))
                connection.commit()
                cart_info = cursor.fetchone()
                cart_count = cursor.rowcount

                if cart_count == 0:
                    continue

                if ct_status == '완료' or ct_status == '확정':
                    if cart_info[1] == '입금' or cart_info[1] == '준비' or cart_info[1] == '배송' or cart_info[1] == '완료':
                        ct_history = cart_info[2] + "\n" + nowDate + " 구매자 " + cart_info[1]
                        cursor.execute("update g5_shop_cart set ct_status=%s, ct_history=%s where ct_id=%s", (ct_status, ct_history, cart_info[0]))
                        connection.commit()

        cursor.close()
        connection.close()

        return {
            'statusCode': 200,
            'message': "success"
        }

    return {
        'statusCode': 400,
        'message': "Invalid ID supplied"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection
