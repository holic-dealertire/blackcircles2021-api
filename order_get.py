import datetime
import json
import pymysql


def lambda_handler(event, context):
    # 카닥 : 1448121245
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    od_id = event['od_id']
    connection = db_connect()
    cursor = connection.cursor()
    data = []

    # 주문정보
    cursor.execute("select od_name, od_tel, concat(od_zip1, od_zip2) as od_zip, od_addr1, od_addr2, od_addr3, od_memo, od_receipt_price, od_ip, od_time from g5_shop_order where od_id='" + od_id + "' and mb_id = '1448121245'")
    connection.commit()
    order_info = cursor.fetchall()

    # 장바구니
    cursor.execute("SELECT io_part_no, ct_qty, ct_status, delivery_company, ct_invoice, ct_invoice_time, ct_complete_time, ct_confirm_time FROM "
                   "    ( SELECT *, it_id AS ca_it_id, io_no AS cart_io_no FROM g5_shop_cart WHERE od_id = '" + od_id + "' AND ct_select = '1' AND ct_orderable = '1' AND mb_id = '1448121245' ) cart "
                   "    LEFT JOIN ( SELECT it_id, ca_id AS it_ca_id FROM g5_shop_item) item ON item.it_id = cart.ca_it_id "
                   "    LEFT JOIN ( SELECT io_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, origin_io_no, io_part_no FROM g5_shop_item_option) opt ON opt.io_no = cart.cart_io_no "
                   "    LEFT JOIN ( SELECT ca_id, ca_name FROM g5_shop_category WHERE  length(ca_id) = 4) category ON category.ca_id = item.it_ca_id "
                   "    LEFT JOIN ( SELECT mb_name as seller_name, mb_hp as seller_tel, mb_no as seller_no FROM g5_member WHERE mb_level = 8) mb_seller ON mb_seller.seller_no = cart.seller_mb_no "
                   "    LEFT JOIN ( SELECT *, mb_no as seller_mb_no from tbl_member_seller ) seller on seller.seller_mb_no=mb_seller.seller_no "
                   "ORDER BY ct_id ASC ")
    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount

    for row in rows:
        data.append(row)

    cursor.close()
    connection.close()

    if row_count == 0:
        return {
            'statusCode': 400,
            'message': "order not found",
            'data': json.dumps(dict(zip(order_info, data)))
        }

    else:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(rows)
        }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_dev")

    return connection
