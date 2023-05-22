import datetime
import json
import pymysql
import urllib3


def lambda_handler(event, context):
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

    if 'datas' not in event or 'mb_id' not in event:
        return {
            'statusCode': 402,
            'message': "parameter error"
        }

    mb_id = event['mb_id']
    connection = db_connect()
    cursor = connection.cursor()

    # 회원체크
    cursor.execute("select mb_no from g5_member where mb_id=%s", mb_id)
    connection.commit()
    mb_info = cursor.fetchone()
    row_count = cursor.rowcount
    tot_price = 0
    if row_count == 0:
        connection.close()
        return {
            'statusCode': 201,
            'message': "mb_id is not exist"
        }
    else:
        length = len(event['datas'])
        mb_no = mb_info[0]
        io_no = ''
        sql = 'insert into tbl_member_seller_stock(mb_id, io_part_no, stock, last_modify, mb_no) values '
        print(sql)
        sql_field = ''
        for i in range(length):
            io_part_no = event['datas'][i]['io_part_no']
            stock = int(event['datas'][i]['stock'])
            sql_field += ",('{0}','{1}','{2}',now(), '{3}')".format(mb_id, io_part_no, stock, mb_no)

        sql = sql + sql_field[1:]
        sql += " ON DUPLICATE KEY UPDATE tbl_member_seller_stock.io_part_no = VALUES(tbl_member_seller_stock.io_part_no)"
        sql += ",tbl_member_seller_stock.stock = VALUES(tbl_member_seller_stock.stock)"
        sql += ",tbl_member_seller_stock.last_modify = VALUES(tbl_member_seller_stock.last_modify)"

        cursor.execute(sql)
        connection.commit()

        cursor.execute("CALL updateSellerStock('{0}')".format(mb_no))
        connection.commit()

    cursor.close()
    connection.close()

    return {
        'statusCode': 200,
        'message': "updated"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection
