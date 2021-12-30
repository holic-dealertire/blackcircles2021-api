import datetime
import json
import pymysql


def lambda_handler(event, context):
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')

    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute("SELECT io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, io_btob_price as io_price, io_discontinued FROM   "
                   "    (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_btob_lowest, io_btob_price, io_discontinued FROM  g5_shop_item_option WHERE origin_io_no IS NULL AND io_btob_price is not null and io_btob_price > 0) opt"
                   "    LEFT JOIN (SELECT it_id, ca_id AS it_ca_id, it_name, it_name_en, it_brand, it_pattern, it_season, it_performance_type FROM   g5_shop_item WHERE  origin_it_id IS NULL) item ON opt.io_it_id = item.it_id "
                   "    LEFT JOIN (SELECT ca_id, ca_name, image FROM   g5_shop_category WHERE  Length(ca_id) = 4 AND Substring(ca_id, 1, 2) = '10') category ON category.ca_id = item.it_ca_id /* 택배가격 */ "
                   "WHERE  category.ca_id IS NOT NULL AND item.it_id IS NOT NULL")
    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    connection.close()

    # return_list = [{"io_size": x[0], "io_size_origin": x[1], "io_part_no": x[2], "io_pr": x[3], "io_max_weight": x[4], "io_speed": x[5], "io_car": x[6], "io_oe": x[7], "io_car_type": x[8], "io_tire_type": x[9], "io_factory_price": x[10], "io_maker": x[11], "it_name": x[12], "it_pattern": x[13], "it_season": x[14], "it_performance_type": x[15], "tot_stock": x[16], "io_price": x[17], "io_discontinued": x[18]} for x in rows]
    return_list = []
    tot_stock = 0
    delv_date = ''
    for row in rows:
        io_info = {'io_size': row[0], 'io_size_origin': row[1], 'io_part_no': row[2], 'io_pr': row[3], 'io_max_weight': row[4], 'io_speed': row[5], 'io_car': row[6], 'io_oe': row[7], 'io_car_type': row[8], 'io_tire_type': row[9], 'io_factory_price': row[10], 'io_maker': row[11], 'it_name': row[12], 'it_pattern': row[13], 'it_season': row[14], 'it_performance_type': row[15], 'tot_stock': tot_stock, 'io_price': row[16], 'io_discontinued': row[17], 'delv_date': delv_date}

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
