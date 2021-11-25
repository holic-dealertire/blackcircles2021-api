import datetime
import json
import pymysql


def lambda_handler(event, context):
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute("SELECT io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, tot_stock, io_btob_price as io_price FROM   "
                   "    (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_btob_lowest, io_btob_price FROM  g5_shop_item_option WHERE  origin_io_no IS NULL AND io_btob_price is not null) opt"
                   "    LEFT JOIN (SELECT it_id, ca_id AS it_ca_id, it_name, it_name_en, it_brand, it_pattern, it_season FROM   g5_shop_item WHERE  origin_it_id IS NULL) item ON opt.io_it_id = item.it_id "
                   "    LEFT JOIN (SELECT ca_id, ca_name, image FROM   g5_shop_category WHERE  Length(ca_id) = 4 AND Substring(ca_id, 1, 2) = '10') category ON category.ca_id = item.it_ca_id /* 택배가격 */ "
                   "    LEFT JOIN (SELECT * FROM   "
                   "                (SELECT * FROM   "
                   "                    (SELECT io_no AS stock_io_no, mb_no AS delivery_seller_no, sale_delivery, stock AS tot_stock, delivery_collect, delivery_price AS delivery_price1 FROM tbl_item_option_price_stock WHERE  stock != '' AND stock > 7) stock"
                   "                     LEFT JOIN (SELECT io_no AS check_io_no, it_id AS check_io_it_id FROM g5_shop_item_option WHERE  origin_io_no IS NULL) check_option ON check_option.check_io_no = stock.stock_io_no "
                   "                     LEFT JOIN (SELECT it_id AS check_it_id, ca_id AS check_ca_id, it_performance_type FROM g5_shop_item WHERE  origin_it_id IS NULL) check_item ON check_item.check_it_id = check_option.check_io_it_id "
                   "                     LEFT JOIN (SELECT ca_id AS contract_ca_id, mb_no AS contract_mb_no, idx AS contract_idx FROM tbl_member_seller_item_contract WHERE  contract_status = '1' AND contract_start <= '" + nowDate + "' AND contract_end >= '" + nowDate + "') contract ON contract.contract_mb_no = stock.delivery_seller_no AND contract.contract_ca_id = check_item.check_ca_id "
                   "                 WHERE  contract_idx IS NOT NULL ORDER  BY sale_delivery DESC, delivery_price1 ASC, tot_stock DESC) stock GROUP BY stock.stock_io_no) AS delivery_price ON delivery_price.stock_io_no = opt.io_no /* 택배가격 */ "
                   "WHERE  category.ca_id IS NOT NULL AND item.it_id IS NOT NULL and sale_delivery >= opt.io_btob_lowest ORDER BY sell_cnt DESC ")
    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount

    cursor.close()
    connection.close()

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
            'data': json.dumps(rows)
        }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_dev")

    return connection
