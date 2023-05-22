# get 차종 정보
import datetime
import json
import pymysql
from decimal import Decimal


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

    if 'size' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error",
            "data": json.dumps(event)
        }

    size = event['size']

    if type(size) is int:
        size = str(size)

    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    cursor.execute("""
        select IF(brand_make = '0', '국산', '수입') as brand_make, brand_name, brand_name_en, car_name, model_name, IF(position = '0', '전륜', '후륜') as position, inch, size, size_origin
        from (select model_idx as size_model_size, position, inch, size, size_origin
              from tbl_car_match_size where size = %s) match_size
                 left join (select idx as model_idx, car_idx as model_car_idx, model_name
                            from tbl_car_match_model) model on match_size.size_model_size = model.model_idx
                 left join (select idx as car_idx, brand_idx as car_brand_idx, car_name
                            from tbl_car_match_car) car on car.car_idx = model.model_car_idx
                 left join (select idx, brand_make, brand_name, brand_name_en
                            from tbl_car_match_brand) brand on brand.idx = car.car_brand_idx
        """, size)

    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    connection.close()

    return_list = []
    for row in rows:
        brand_make = row[0]
        brand_name = row[1]
        brand_name_en = row[2]
        car_name = row[3]
        model_name = row[4]
        position = row[5]
        size_origin = row[8]

        if type(row[6]) is str:
            inch = int(row[6])
        else:
            inch = row[6]

        if type(row[7]) is str:
            size = int(row[7])
        else:
            size = row[7]

        model_info = {'brand_make': brand_make, 'brand_name': brand_name, 'brand_name_en': brand_name_en, 'car_name': car_name, 'model_name': model_name, 'position': position, 'inch': inch, 'size': size, 'size_origin': size_origin}
        return_list.append(model_info)

    if row_count == 0:
        return {
            "statusCode": 200,
            "message": "success",
            "data": json.dumps(rows, ensure_ascii=False, cls=JSONEncoder)
        }

    else:
        return {
            "statusCode": 200,
            "message": "success",
            "data": json.dumps(return_list, ensure_ascii=False, cls=JSONEncoder)
        }


def db_connect():
    connection = pymysql.connect(host="read.c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles")
    return connection


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
