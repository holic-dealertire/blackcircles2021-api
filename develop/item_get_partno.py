import datetime
import json
import pymysql

def lambda_handler(event, context):
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    io_part_no = event['io_part_no']
    connection = db_connect()
    cursor = connection.cursor()

    if type(io_part_no) is int:
        io_part_no = str(io_part_no)

    cursor.execute("SELECT io_no  FROM  g5_shop_item_option WHERE io_part_no='" + io_part_no + "'")
    connection.commit()
    io_check = cursor.fetchone()
    if io_check is None:
        return {
            'statusCode': 202,
            'message': "io_part_no is not exist"
        }

    cursor.execute("SELECT io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, tot_stock, io_btob_price as io_price, io_discontinued, delivery_seller_no, io_no, delv_date FROM   "
                   "    (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_btob_lowest, io_btob_price, io_discontinued FROM  g5_shop_item_option WHERE io_part_no='" + io_part_no + "' AND origin_io_no IS NULL AND io_btob_price is not null and io_btob_price > 0) opt"
                   "    LEFT JOIN (SELECT it_id, ca_id AS it_ca_id, it_name, it_name_en, it_brand, it_pattern, it_season FROM   g5_shop_item WHERE  origin_it_id IS NULL) item ON opt.io_it_id = item.it_id "
                   "    LEFT JOIN (SELECT ca_id, ca_name, image FROM   g5_shop_category WHERE  Length(ca_id) = 4 AND Substring(ca_id, 1, 2) = '10') category ON category.ca_id = item.it_ca_id /* 택배가격 */ "
                   "    LEFT JOIN (SELECT * FROM   "
                   "                (SELECT * FROM   "
                   "                    (SELECT io_no AS stock_io_no, mb_no AS delivery_seller_no, sale_delivery, stock AS tot_stock, delivery_collect, delivery_price AS delivery_price1 FROM tbl_item_option_price_stock WHERE  stock != '' AND stock > 7) stock"
                   "                     LEFT JOIN (select mb_no as seller_mb_no, delv_date from tbl_member_seller) seller on seller.seller_mb_no=stock.delivery_seller_no"                                                                                                                                                                                                                                                                                                                           
                   "                     LEFT JOIN (SELECT io_no AS check_io_no, it_id AS check_io_it_id, io_btob_lowest as check_btob_lowest FROM g5_shop_item_option WHERE  origin_io_no IS NULL and io_part_no='" + io_part_no + "' ) check_option ON check_option.check_io_no = stock.stock_io_no "
                   "                     LEFT JOIN (SELECT it_id AS check_it_id, ca_id AS check_ca_id, it_performance_type FROM g5_shop_item WHERE  origin_it_id IS NULL) check_item ON check_item.check_it_id = check_option.check_io_it_id "
                   "                     LEFT JOIN (SELECT ca_id AS contract_ca_id, mb_no AS contract_mb_no, idx AS contract_idx FROM tbl_member_seller_item_contract WHERE  contract_status = '1' AND contract_start <= '" + nowDate + "' AND contract_end >= '" + nowDate + "') contract ON contract.contract_mb_no = stock.delivery_seller_no AND contract.contract_ca_id = check_item.check_ca_id "
                   "                 WHERE  contract_idx IS NOT NULL and check_btob_lowest <= sale_delivery ORDER  BY sale_delivery DESC, delivery_price1 ASC, tot_stock DESC) stock GROUP BY stock.stock_io_no) AS delivery_price ON delivery_price.stock_io_no = opt.io_no /* 택배가격 */ "
                   "WHERE  category.ca_id IS NOT NULL AND item.it_id IS NOT NULL")

    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    connection.close()

    # return_list = [{"io_size": x[0], "io_size_origin": x[1], "io_part_no": x[2], "io_pr": x[3], "io_max_weight": x[4], "io_speed": x[5], "io_car": x[6], "io_oe": x[7], "io_car_type": x[8], "io_tire_type": x[9], "io_factory_price": x[10], "io_maker": x[11], "it_name": x[12], "it_pattern": x[13], "it_season": x[14], "it_performance_type": x[15], "tot_stock": x[16], "io_price": x[17], "io_discontinued": x[18]} for x in rows]
    return_list = []
    io_info = {}
    for row in rows:
        io_info['io_size'] = row[0]
        io_info['io_size_origin'] = row[1]
        io_info['io_part_no'] = row[2]
        io_info['io_pr'] = row[3]
        io_info['io_max_weight'] = row[4]
        io_info['io_speed'] = row[5]
        io_info['io_car'] = row[6]
        io_info['io_oe'] = row[7]
        io_info['io_car_type'] = row[8]
        io_info['io_tire_type'] = row[9]
        io_info['io_factory_price'] = row[10]
        io_info['io_maker'] = row[11]
        io_info['it_name'] = row[12]
        io_info['it_pattern'] = row[13]
        io_info['it_season'] = row[14]
        io_info['it_performance_type'] = row[15]
        io_info['tot_stock'] = row[16]
        if io_info['tot_stock'] is None:
            io_info['tot_stock'] = 0

        io_info['io_price'] = row[17]
        io_info['io_discontinued'] = row[18]
        io_info['delv_date'] = ''
        if row[21]:
            io_info['delv_date'] = str(row[21])
        return_list = io_info

    if row_count == 0:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(rows)
        }

    elif return_list['tot_stock'] is None:
        return {
            'statusCode': 201,
            'message': "no stock",
            'data': json.dumps(return_list)
        }

    else:
        return {
            'statusCode': 200,
            'message': "success",
            'data': json.dumps(return_list)
        }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles")

    return connection


def get_delivery(seller_no):
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')
    day = int(now.strftime('%w'))
    hours = now.strftime('%H:%M')

    connection = db_connect()
    cursor = connection.cursor()

    # 한국 공휴일
    cursor.execute("select idx from tbl_holiday_kor where holiday=%s limit 1", today)
    connection.commit()
    holiday = cursor.fetchone()

    # 휴무 체크
    cursor.execute("select holiday_saturday from tbl_member_retail where mb_no=%s", seller_no)
    connection.commit()
    retail_info = cursor.fetchone()

    cursor.execute("select delivery_deadline_weekday, delivery_deadline_weekend from tbl_member_seller where mb_no=%s", seller_no)
    connection.commit()
    seller_info = cursor.fetchone()

    cursor.execute("select count(*) as cnt from tbl_member_seller_holiday where mb_no=%s and holiday=%s", (seller_no, today))
    connection.commit()
    seller_holiday = cursor.fetchone()

    if holiday is not None and holiday[0] is not None:  # 공휴일이고 영업시간 지남
        next_delivery_date = get_next_delivery(2, seller_no)
    elif 1 <= day <= 5 and seller_info is not None and seller_info[0] and hours < seller_info[0] and seller_holiday is not None and seller_holiday[0] == 0:  # 평일이고 영업중
        next_delivery_date = get_next_delivery(1, seller_no)
    elif day == 5 and seller_info is not None and seller_info[0] and hours > seller_info[0]:  # 금요일이고 영업시간 지남
        if retail_info is not None and retail_info[0]:  # 토요일 휴무라면
            next_delivery_date = get_next_delivery(3, seller_no)
        else:
            next_delivery_date = get_next_delivery(2, seller_no)
    elif day == 6 and seller_info is not None and seller_info[1] and hours < seller_info[0] and retail_info is not None and retail_info[0] == 0:  # 토요일이고 영업중, 토요일 휴무가 아님
        next_delivery_date = get_next_delivery(1, seller_no)
    elif day == 6 and ((seller_info is not None and seller_info[1] and hours > seller_info[1]) or (retail_info is not None and retail_info[0] == 1)):  # 토요일이고 영업시간 지났거나 토요일휴무
        next_delivery_date = get_next_delivery(2, seller_no)
    else:
        next_delivery_date = get_next_delivery(2, seller_no)

    return next_delivery_date


def get_next_delivery(next_working_day, seller_no):
    numberOfDays = next_working_day
    weekends = ['sunday']
    now = datetime.datetime.now()
    currentDate = now.strftime('%Y-%m-%d')
    timeStamp = now
    i = 0

    connection = db_connect()
    cursor = connection.cursor()

    off_day = []

    # 공휴일 휴무 체크
    cursor.execute("select holiday_public from tbl_member_retail where mb_no=%s", seller_no)
    connection.commit()
    retail_info = cursor.fetchone()

    if retail_info is not None and retail_info[0] is not None:
        cursor.execute("select holiday from tbl_holiday_kor where holiday >= %s", currentDate)
        connection.commit()
        for row in cursor:
            if len(off_day) == 0 or row[0] not in off_day:
                off_day.append(str(row[0]))

    cursor.execute("select holiday from tbl_member_seller_holiday where mb_no = %s and holiday >= %s", (seller_no, currentDate))
    connection.commit()
    for row in cursor:
        if len(off_day) == 0 or row[0] not in off_day:
            off_day.append(str(row[0]))

    while i > -10:
        timeStamp = timeStamp + datetime.timedelta(days=1)
        next_day = timeStamp.strftime('%A').lower()
        check_day = timeStamp.strftime('%Y-%m-%d')

        cursor.execute("select idx from tbl_holiday_kor where holiday >= %s limit 1", check_day)
        connection.commit()
        holiday_check = cursor.fetchone()

        if holiday_check is not None and holiday_check[0] is not None:  # 공휴일
            i -= 1
        elif len(off_day) > 0 and check_day in off_day:  # 총판 쉬는날
            i -= 1
        elif next_day in weekends:  # 일요일
            i -= 1

        i += 1
        if i == numberOfDays:
            break

    return timeStamp.strftime('%Y-%m-%d')