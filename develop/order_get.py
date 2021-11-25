import datetime
import json
import pymysql


def lambda_handler(event, context):
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')

    if 'od_id' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error"
        }

    od_id = event['od_id']

    if type(od_id) is int:
        od_id = str(od_id)

    if od_id:
        connection = db_connect()
        cursor = connection.cursor()
        # 주문정보
        cursor.execute("select od_name, od_tel, concat(od_zip1, od_zip2) as od_zip, od_addr1, od_addr2, od_addr3, od_memo, od_receipt_price, od_time, od_reserv_date from g5_shop_order where od_id=%s", od_id)
        connection.commit()
        order_info = cursor.fetchone()

        if order_info is None:
            return {
                'statusCode': 400,
                'message': "order not found"
            }

        # 장바구니
        cursor.execute("SELECT io_part_no, ct_qty, ct_status, ct_delivery_company, ct_invoice, ct_invoice_time, ct_complete_time, ct_confirm_time FROM "
                       "    ( SELECT *, it_id AS ca_it_id, io_no AS cart_io_no FROM g5_shop_cart WHERE od_id = '" + od_id + "' AND ct_select = '1' AND ct_orderable = '1' AND mb_id = 'cardoc' ) cart "
                       "    LEFT JOIN ( SELECT it_id, ca_id AS it_ca_id FROM g5_shop_item) item ON item.it_id = cart.ca_it_id "
                       "    LEFT JOIN ( SELECT io_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, origin_io_no, io_part_no FROM g5_shop_item_option) opt ON opt.io_no = cart.cart_io_no "
                       "    LEFT JOIN ( SELECT ca_id, ca_name FROM g5_shop_category WHERE  length(ca_id) = 4) category ON category.ca_id = item.it_ca_id "
                       "    LEFT JOIN ( SELECT mb_name as seller_name, mb_hp as seller_tel, mb_no as seller_no FROM g5_member WHERE mb_level = 8) mb_seller ON mb_seller.seller_no = cart.seller_mb_no "
                       "    LEFT JOIN ( SELECT *, mb_no as seller_mb_no from tbl_member_seller ) seller on seller.seller_mb_no=mb_seller.seller_no "
                       "ORDER BY ct_id ASC ")
        connection.commit()
        rows = cursor.fetchall()
        row_count = cursor.rowcount
        cursor.close()
        connection.close()
        cart_list = [{"io_part_no": x[0], "ct_qty": x[1], "ct_status": x[2], "delivery_company": x[3], "ct_invoice": x[4], "ct_invoice_time": x[5], "ct_complete_time": x[6], "ct_confirm_time": x[7]} for x in rows]
        return_list = [{"od_name": order_info[0], "od_tel": order_info[1], "od_zip": order_info[2], "od_addr1": order_info[3], "od_addr2": order_info[4], "od_addr3": order_info[5], "od_memo": order_info[6], "od_receipt_price": order_info[7], "od_time": order_info[8], "od_reserv_date": order_info[9], "cart_item": cart_list}]

        if row_count == 0:
            return {
                'statusCode': 400,
                'message': "order not found",
                'data': json.dumps(rows)
            }

        else:
            return {
                'statusCode': 200,
                'message': "success",
                'data': json.dumps(return_list, indent=4, sort_keys=False, default=str)
            }

    return {
        'statusCode': 400,
        'message': "od_id is null"
    }

def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_dev")

    return connection
