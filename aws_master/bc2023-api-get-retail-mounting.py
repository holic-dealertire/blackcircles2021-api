# get 장착점 리스트
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

    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    cursor.execute("""
        select mb_no, mb_name, mb_zip1, mb_zip2, mb_addr1, mb_addr2, mb_addr3, company_photo1, company_photo2, company_photo3, company_photo4, company_photo5, business_weekday_start, business_weekday_end, business_weekend_start, business_weekend_end, IF(holiday_saturday = 1, '휴무','') as holiday_saturday, IF(holiday_sunday = 1, '휴무', '') as holiday_sunday, mb_hp from 
        (
            select mb_no, mb_name, mb_hp, mb_zip1, mb_zip2, mb_addr1, mb_addr2, mb_addr3 from g5_member where mb_level = 5 or mb_level = 8
        ) mb
        left join (
            select mb_no as retail_mb_no, company_photo1, company_photo2, company_photo3, company_photo4, company_photo5, business_weekday_start, business_weekday_end, business_weekend_start, business_weekend_end, holiday_saturday, holiday_sunday from tbl_member_retail where mounting_target = 1
        ) retail on retail.retail_mb_no=mb.mb_no
        where retail_mb_no is not null
        """)

    connection.commit()
    rows = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    connection.close()

    return_list = []
    for row in rows:
        if type(row[0]) is str:
            mb_no = int(row[0])
        else:
            mb_no = row[0]
        mb_name = row[1]
        mb_hp = row[18]
        mb_zip = [row[2], row[3]]
        mb_zip = ''.join(mb_zip)
        md_addr = [row[4], row[5], row[6]]
        md_addr = ''.join(md_addr)
        company_photo1 = row[7]
        company_photo2 = row[8]
        company_photo3 = row[9]
        company_photo4 = row[10]
        company_photo5 = row[11]
        business_weekday_start = row[12]
        business_weekday_end = row[13]
        business_weekend_start = row[14]
        business_weekend_end = row[15]
        holiday_saturday = row[16]
        holiday_sunday = row[17]
        retail_image = []

        if company_photo1:
            retail_image.append(company_photo1)

        if company_photo2:
            retail_image.append(company_photo2)

        if company_photo3:
            retail_image.append(company_photo3)

        if company_photo4:
            retail_image.append(company_photo4)

        if company_photo5:
            retail_image.append(company_photo5)

        retail_info = {'mb_no': mb_no, 'mb_name': mb_name, 'mb_hp': mb_hp, 'mb_zip': mb_zip, 'md_addr': md_addr, 'retail_image': retail_image, 'business_weekday_start': business_weekday_start, 'business_weekday_end': business_weekday_end, 'business_weekend_start': business_weekend_start, 'business_weekend_end': business_weekend_end, 'holiday_saturday': holiday_saturday,
                       'holiday_sunday': holiday_sunday}
        return_list.append(retail_info)

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
