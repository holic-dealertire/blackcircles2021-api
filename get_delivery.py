import datetime
import json
import pymysql
import time


def db_connect():
    connection = pymysql.connect(host="blackcircles2021.cluster-c2syf7kukikc.ap-northeast-2.rds.amazonaws.com", user="admin", password="Dealertire0419**", db="blackcircles_dev")
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


print(get_delivery('55'))
