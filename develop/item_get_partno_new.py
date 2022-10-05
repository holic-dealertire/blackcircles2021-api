import datetime
import json
import pymysql
from decimal import Decimal
import math
import random


def lambda_handler(event, context):
    if 'member_id' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    if 'qty' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    mb_id = event['member_id']
    qty = event['qty']
    if qty is None:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }
    if type(qty) is str:
        qty = int(qty)
    if qty < 1:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

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
    io_part_no = event['io_part_no']

    if type(io_part_no) is int:
        io_part_no = str(io_part_no)

    cursor.execute("SELECT io_no  FROM  g5_shop_item_option WHERE io_part_no = '" + io_part_no + "'")
    connection.commit()
    io_no = cursor.fetchone()
    if io_no is None:
        return {
            'statusCode': 202,
            'message': "io_part_no is not exist"
        }

    cursor.execute("select algorithm_range from g5_shop_default")
    connection.commit()
    algorithm_range = cursor.fetchone()
    algorithm_range = algorithm_range[0]

    cursor.execute("""
    SELECT io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, delivery_stock, price, io_discontinued, io_delivery_price, ca_name, io_sell_price_premium, range_1, range_2, range_3, io_no
    FROM (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_btob_lowest, io_btob_price, io_discontinued, io_delivery_price FROM g5_shop_item_option where io_no = %s and origin_io_no is null) opt
             LEFT JOIN (SELECT it_id, ca_id AS item_ca_id, it_name, it_pattern, it_season, it_performance_type FROM g5_shop_item) item ON item.it_id = opt.io_it_id
             LEFT JOIN (select ca_id, ca_name from g5_shop_category) cate on cate.ca_id=item.item_ca_id
             LEFT JOIN
    (select *
     from (select *, CAST(SUM(sum_stock) AS SIGNED) as delivery_stock
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
                                   WHERE stock > 0) stock
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
    """, (io_no, nowDate, nowDate))
    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount

    return_list = []
    io_info = {}
    for row in rows:
        if type(row[17]) is str:
            io_sale = int(row[17])
        else:
            io_sale = row[17]
        io_no = row[25]
        io_sell_price_premium = row[21]
        range_1 = row[22]
        range_2 = row[23]
        range_3 = row[24]
        if type(io_sell_price_premium) is str:
            io_sell_price_premium = int(io_sell_price_premium)
        if type(range_1) is str:
            range_1 = int(range_1)
        if type(range_2) is str:
            range_2 = int(range_2)
        if type(range_3) is str:
            range_3 = int(range_3)
        range_min = 0
        range_max = 100

        # 최소 최대 할인율
        if io_sale >= io_sell_price_premium:
            range_min = io_sell_price_premium + 2
        elif (io_sell_price_premium - range_1) <= io_sale < (io_sell_price_premium + 2):
            range_min = io_sell_price_premium - range_1 + 2
            range_max = io_sell_price_premium + 2
        elif (io_sell_price_premium - range_1 - range_2) <= io_sale < (io_sell_price_premium - range_1 + 2):
            range_min = io_sell_price_premium - range_1 - range_2 + 2
            range_max = io_sell_price_premium - range_1 + 2
        elif (io_sell_price_premium - range_1 - range_2 - range_3) <= io_sale < (io_sell_price_premium - range_1 - range_2 + 2):
            range_min = io_sell_price_premium - range_1 - range_2 - range_3 + 2
            range_max = io_sell_price_premium - range_1 - range_2 + 2
        elif io_sale > 0:
            range_min = io_sale
        else:
            range_max = 0

        cursor.execute("""
            select stock_mb_no, sale_delivery
            from 
                 (
                        select io_no as stock_io_no, mb_no as stock_mb_no, sale_delivery
                        from tbl_item_option_price_stock
                        where stock >= %s and io_no = %s and sale_delivery < %s AND sale_delivery >= %s
                 ) stock
                LEFT JOIN (SELECT io_no AS check_io_no, it_id AS check_io_it_id FROM   g5_shop_item_option
                                                          WHERE  origin_io_no IS NULL) opt
                                                      ON stock.stock_io_no = opt.check_io_no
                                        LEFT JOIN (SELECT it_id AS check_it_id, ca_id AS check_it_ca_id
                                                          FROM   g5_shop_item) check_item
                                                      ON check_item.check_it_id = opt.check_io_it_id
                                        LEFT JOIN (SELECT ca_id, range_1, range_2, range_3
                                                          FROM   g5_shop_category) cate
                                                      ON cate.ca_id = check_item.check_it_ca_id
                                        LEFT JOIN (SELECT ca_id AS contract_ca_id, mb_no AS contract_mb_no, idx
                                                          FROM   tbl_member_seller_item_contract
                                                          WHERE  contract_status = '1' AND contract_start <= %s AND contract_end >= %s) contract
                                                      ON contract.contract_ca_id = check_item.check_it_ca_id AND contract.contract_mb_no = stock.stock_mb_no
                                        WHERE  contract.idx IS NOT NULL
        """, (qty, io_no, range_max, range_min, nowDate, nowDate))
        connection.commit()
        seller_list = cursor.fetchall()
        seller_cnt = cursor.rowcount
        seller_array = []
        sale_array = []
        weighted_array = []
        seller_no = ''
        if seller_cnt > 1:
            for i in range(seller_cnt):
                seller_array.append(seller_list[i][0])
                sale_array.append(seller_list[i][1])
        elif seller_cnt == 1:
            seller_no = seller_list[0][0]

        idx = ''
        if seller_cnt > 1:
            for j in range(seller_cnt):
                weighted_array.append(round(get_weighted_value_based_standard_deviation(sale_array[j], sale_array, seller_cnt, algorithm_range) * 10000))
            for k in range(0, 10):
                idx = f_weighed_random(weighted_array)
                if idx is not None:
                    break
        if idx != '':
            seller_no = seller_array[idx]

        stock = 0
        delv_date = ''
        if seller_no == '' or seller_no is None:
            seller_no = "NULL"
        else:
            cursor.execute("""select delv_date from tbl_member_seller where mb_no = %s""", str(seller_no))
            connection.commit()
            delv_date = cursor.fetchone()
            delv_date = delv_date[0]
            cursor.execute("""select stock from tbl_item_option_price_stock where mb_no = %s and io_no = %s""", (str(seller_no), str(io_no)))
            connection.commit()
            stock = cursor.fetchone()
            stock = stock[0]

        io_price = round(int(row[10]) - (int(row[10]) / 100 * io_sale), -3)
        io_info['io_size'] = str(row[0])
        io_info['io_size_origin'] = str(row[1])
        io_info['io_part_no'] = str(row[2])
        io_info['io_pr'] = str(row[3])
        io_info['io_max_weight'] = str(row[4])
        io_info['io_speed'] = str(row[5])
        io_info['io_car'] = str(row[6])
        io_info['io_oe'] = str(row[7])
        io_info['io_car_type'] = str(row[8])
        io_info['io_tire_type'] = str(row[9])
        io_info['io_factory_price'] = row[10]
        io_info['io_maker'] = str(row[11])
        io_info['it_name'] = str(row[12])
        io_info['it_pattern'] = str(row[13])
        io_info['it_season'] = str(row[14])
        io_info['it_performance_type'] = str(row[15])
        io_info['stock'] = stock
        io_info['io_price'] = int(io_price)
        io_info['io_sale'] = row[17]
        io_info['io_delivery_price'] = row[19]
        io_info['io_discontinued'] = str(row[18])
        io_info['ca_name'] = str(row[20])
        io_info['seller_no'] = seller_no
        io_info['delv_date'] = delv_date
        return_list = io_info

    cursor.close()
    connection.close()

    if row_count == 0:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(rows, ensure_ascii=False, cls=JSONEncoder, default=str)
        }

    elif return_list['stock'] is None:
        return {
            'statusCode': 201,
            'message': "no stock",
            'data': json.dumps(return_list, ensure_ascii=False, cls=JSONEncoder, default=str)
        }

    else:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(return_list, ensure_ascii=False, cls=JSONEncoder, default=str)
        }


def db_connect():
    connection = pymysql.connect(host="read.c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def get_weighted_value_based_standard_deviation(sale, sale_array, cnt, coefficient):
    sale_tot = 0
    coefficient_tot = 0
    s = 0
    for i in range(len(sale_array)):
        sale_tot += sale_array[i]

    for i in range(cnt):
        s += (sale_array[i] - (sale_tot / cnt)) * (sale_array[i] - (sale_tot / cnt))
    std = math.sqrt(s / cnt)
    for i in range(len(sale_array)):
        coefficient_tot += math.pow((sale_array[i] * std), (sale_tot / cnt) * float(coefficient))

    coefficient = pow((sale * std), (sale_tot / cnt) * float(coefficient))
    if coefficient_tot > 0 and coefficient > 0:
        return round(coefficient / coefficient_tot, 4)
    return 1


def f_weighed_random(weighted_array):
    total = 0
    sale_value_cnt = 0
    for i in range(len(weighted_array)):
        weighted_array[i] = weighted_array[i] * 10000
        total += weighted_array[i]
        if weighted_array[i] == 1:
            sale_value_cnt += 1
    if sale_value_cnt == len(weighted_array):
        return rand(0, sale_value_cnt - 1)
    else:
        r = random.randrange(0, total)
        for i in range(len(weighted_array)):
            r -= weighted_array[i]
            if r < 1:
                return i
    return false
