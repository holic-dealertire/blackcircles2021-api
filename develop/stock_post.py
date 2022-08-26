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
    if row_count == 0:
        connection.close()
        return {
            'statusCode': 201,
            'message': "mb_id is not exist"
        }
    else:
        length = len(event['datas'])
        mb_no = mb_info[0]
        for i in range(length):
            io_part_no = event['datas'][i]['io_part_no']
            stock = int(event['datas'][i]['stock'])
            cursor.execute("select io_no from g5_shop_item_option where io_part_no=%s", io_part_no)
            connection.commit()
            opt_info = cursor.fetchone()
            opt_inset = cursor.rowcount
            if opt_inset != 0:
                io_no = opt_info[0]
                if io_part_no and stock and io_no:
                    cursor.execute("select idx from tbl_item_option_price_stock where mb_no=%s and io_no=%s", (mb_no, io_no))
                    connection.commit()
                    stock_info = cursor.fetchone()
                    idx = stock_info[0]
                    if idx:
                        cursor.execute("update tbl_item_option_price_stock set stock=%s where idx=%s", (stock, idx))
                        # else:
                        #     cursor.execute(
                        #         "insert into tbl_item_option_price_stock set stock=%s")
                        connection.commit()
        connection.close()

    return {
        'statusCode': 200,
        'message': "updated"
    }


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_develop")

    return connection