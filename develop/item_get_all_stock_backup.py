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

    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')

    cursor.execute(" SELECT io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, delivery_stock, io_btob_price as io_price, io_discontinued, delivery_seller_no, delv_date FROM "
                   "                (SELECT * FROM   "
                   "                                (SELECT * FROM   "
                   "                                                (SELECT io_no AS stock_io_no, mb_no AS delivery_seller_no, sale_delivery, stock AS delivery_stock, delivery_collect, delivery_price AS delivery_price1 FROM  tbl_item_option_price_stock WHERE  stock != '' AND stock > 1) stock "
                   "                                                        LEFT JOIN (SELECT io_no AS check_io_no, it_id AS check_io_it_id, io_btob_price FROM   g5_shop_item_option WHERE  origin_io_no IS NULL AND io_btob_price IS NOT NULL AND io_btob_price > 0) check_option ON check_option.check_io_no = stock.stock_io_no "
                   "                                                        LEFT JOIN (SELECT it_id AS check_it_id, ca_id AS check_ca_id FROM   g5_shop_item WHERE  origin_it_id IS NULL) check_item ON check_item.check_it_id = check_option.check_io_it_id"
                   "                                                        LEFT JOIN (SELECT ca_id AS contract_ca_id, mb_no AS contract_mb_no, idx   AS contract_idx FROM   tbl_member_seller_item_contract WHERE  contract_status = '1' AND contract_start <= '" + nowDate + "' AND contract_end >= '" + nowDate + "') contract ON contract.contract_mb_no = stock.delivery_seller_no AND contract.contract_ca_id = check_item.check_ca_id"
                   "                                  WHERE  contract_idx IS NOT NULL ORDER  BY sale_delivery DESC, delivery_price1 ASC, delivery_stock DESC) stock GROUP  BY stock.stock_io_no"
                   "                  ) AS delivery_price "
                   "                 LEFT JOIN (select mb_no as seller_mb_no, delv_date from tbl_member_seller) seller on seller.seller_mb_no=delivery_price.delivery_seller_no"
                   "                 LEFT JOIN (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_rating, io_discontinued FROM   g5_shop_item_option WHERE  origin_io_no IS NULL AND io_discontinued != '2' AND io_btob_price IS NOT NULL AND io_btob_price > 0) opt ON opt.io_no = delivery_price.stock_io_no "
                   "                 LEFT JOIN (SELECT it_id, ca_id AS it_ca_id, it_name, it_name_en, it_brand, it_pattern, it_season, it_performance_type FROM   g5_shop_item WHERE  origin_it_id IS NULL) item "
                   "ON opt.io_it_id = item.it_id LEFT JOIN (SELECT ca_id, ca_name, image FROM   g5_shop_category WHERE  Length(ca_id) = 4) category ON category.ca_id = item.it_ca_id /* 택배가격 */ WHERE  category.ca_id IS NOT NULL AND item.it_id IS NOT NULL ")
    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    connection.close()

    return_list = []
    for row in rows:
        delv_date = ''
        if row[20]:
            delv_date = str(row[20])
        io_info = {'io_size': row[0], 'io_size_origin': row[1], 'io_part_no': row[2], 'io_pr': row[3], 'io_max_weight': row[4], 'io_speed': row[5], 'io_car': row[6], 'io_oe': row[7], 'io_car_type': row[8], 'io_tire_type': row[9], 'io_factory_price': row[10], 'io_maker': row[11], 'it_name': row[12], 'it_pattern': row[13], 'it_season': row[14], 'it_performance_type': row[15], 'tot_stock': row[16], 'io_price': row[17], 'io_discontinued': row[18], 'delv_date': delv_date}

        return_list.append(io_info)

    if row_count == 0:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(rows)
        }

    else:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(return_list)
        }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection
