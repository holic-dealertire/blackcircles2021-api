import datetime
import json
import pymysql
from decimal import Decimal


# 알고리즘 적용 완료

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

    cursor.execute("""
    select io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, delivery_stock, price, io_discontinued, io_delivery_price, ca_name, max_stock
    from (select io_no as chk_io_no from tbl_item_option_price_stock where stock > 0 group by io_no) check_stock
             left join
    (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_btob_lowest, io_btob_price, io_discontinued, io_delivery_price
     FROM g5_shop_item_option
     where origin_io_no is null) opt
    on opt.io_no = check_stock.chk_io_no
             LEFT JOIN (SELECT it_id, ca_id AS item_ca_id, it_name, it_pattern, it_season, it_performance_type FROM g5_shop_item) item ON item.it_id = opt.io_it_id
             LEFT JOIN (select ca_id, ca_name from g5_shop_category) cate on cate.ca_id = item.item_ca_id
             LEFT JOIN
    (select *
     from (select *, CAST(SUM(sum_stock) AS SIGNED) as delivery_stock, MAX(stock) AS max_stock
           from (SELECT *
                 FROM (SELECT *,
                           CASE
                               WHEN sale_delivery >= io_sell_price_premium + 2
                                   THEN io_sell_price_premium
                               WHEN sale_delivery >= io_sell_price_premium - range_1 + 2 AND sale_delivery < io_sell_price_premium + 2
                                   THEN io_sell_price_premium - range_1
                               WHEN sale_delivery >= io_sell_price_premium - range_1 - range_2 + 2 AND sale_delivery < io_sell_price_premium - range_1 + 2
                                   THEN io_sell_price_premium - range_1 - range_2
                               WHEN sale_delivery >= io_sell_price_premium - range_1 - range_2 - range_3 + 2 AND sale_delivery < io_sell_price_premium - range_1 - range_2 + 2
                                   THEN io_sell_price_premium - range_1 - range_2 - range_3
                               else sale_delivery - 2
                               end AS price
                       FROM (SELECT *,
                                 Sum(stock) AS sum_stock
                             FROM (SELECT io_no AS stock_io_no, sale_delivery, stock, mb_no AS stock_mb_no, idx as delivery_idx
                                   FROM tbl_item_option_price_stock
                                   WHERE stock > 3) stock
                                      LEFT JOIN (SELECT io_no AS check_io_no, it_id AS check_io_it_id, io_sell_price_basic, io_sell_price_premium
                                                 FROM g5_shop_item_option
                                                 WHERE origin_io_no IS NULL) check_option
                             ON stock.stock_io_no = check_option.check_io_no
                                      LEFT JOIN (SELECT it_id AS check_it_id, ca_id AS check_it_ca_id
                                                 FROM g5_shop_item) check_item
                             ON check_item.check_it_id = check_option.check_io_it_id
                                      LEFT JOIN (SELECT ca_id as ca_id_1, range_1, range_2, range_3
                                                 FROM g5_shop_category) cate
                             ON cate.ca_id_1 = check_item.check_it_ca_id
                                      LEFT JOIN (SELECT ca_id AS contract_ca_id, mb_no AS contract_mb_no, idx
                                                 FROM tbl_member_seller_item_contract
                                                 WHERE contract_status = '1' AND contract_start <= %s AND contract_end >= %s) contract
                             ON contract.contract_ca_id = check_item.check_it_ca_id AND contract.contract_mb_no = stock.stock_mb_no
                             WHERE contract.idx IS NOT NULL
                             GROUP BY stock_io_no, sale_delivery) stock) AS price_table
                 WHERE price IS NOT NULL
                 ORDER BY stock_io_no ASC, price DESC) as stock
           group by stock_io_no, price
           order by price desc) price
     group by stock_io_no) AS delivery_price
    ON delivery_price.stock_io_no = opt.io_no
    where io_no is not null and stock_io_no is not null
    """, (nowDate, nowDate))
    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    connection.close()

    return_list = []
    for row in rows:
        if type(row[17]) is str:
            io_sale = int(row[17])
        else:
            io_sale = row[17]

        if io_sale is None or io_sale < 0:
            io_sale = 0

        if type(row[10]) is str:
            io_factory_price = int(row[10])
        else:
            io_factory_price = row[10]

        io_price = int(round(io_factory_price - (io_factory_price / 100 * io_sale), -3))
        if io_price < 0:
            io_price = 0

        if row[16] is None:
            tot_stock = 0
        else:
            tot_stock = row[16]

        if row[19] is None:
            io_delivery_price = 0
        else:
            io_delivery_price = row[19]

        if row[21] is None:
            max_stock = 0
        else:
            max_stock = row[21]

        io_info = {'io_size': row[0], 'io_size_origin': row[1], 'io_part_no': row[2], 'io_pr': row[3], 'io_max_weight': row[4], 'io_speed': row[5], 'io_car': row[6], 'io_oe': row[7],
                   'io_car_type': row[8], 'io_tire_type': row[9], 'io_factory_price': io_factory_price, 'io_maker': row[11], 'it_name': row[12], 'it_pattern': row[13], 'it_season': row[14],
                   'it_performance_type': row[15],
                   'tot_stock': tot_stock, 'io_price': io_price, 'io_sale': io_sale, 'io_delivery_price': io_delivery_price, 'io_discontinued': row[18], 'ca_name': row[20], 'max_stock': max_stock}

        return_list.append(io_info)

    if row_count == 0:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(rows, ensure_ascii=False, cls=JSONEncoder)
        }

    else:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(return_list, ensure_ascii=False, cls=JSONEncoder)
        }


def db_connect():
    connection = pymysql.connect(host="read.c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles")

    return connection


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
