import json
import pymysql


def lambda_handler(event, context):
    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute("select mb_no, mb_id, mb_name from g5_member where 1 order by mb_no asc")
    connection.commit()
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        'statusCode': 200,
        'body': json.dumps(rows)
    }

# body에 name : value로 넣으면
# 받을때는 event['name'] 으로


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_dev")

    return connection
a