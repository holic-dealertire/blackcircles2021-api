from webdriver_manager.chrome import ChromeDriverManager
from seleniumwire import webdriver as wired_webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import schedule
import traceback
import datetime

# 과제 1.OOO 팝업제어
# 과제 2.OOO 사이트 로그인 전에 대기되도록 webdriver wait 기능 구현
# 과제 3.OOO 프로그램 돌아가던 중에 로그아웃 처리가 되면 텔레그램 메시지 전송되도록 구현
# 과제 4.OOO 00:00~06:00 사이에는 재고사항이 업데이트진행되지않도록 스케쥴 모듈 구현
# 과제 5. 사이트 AWS서버에 전송되도록 구현

# 리스트 나누는 함수
def list_chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


# 재고 조회버튼 반복문
def get_stock_info(n=0):
    try:
        # 오전 6시 이후 알림팝업 뜨면 제 거

        try:
            da = Alert(driver)
            da.text()
            if '0시' in da.text:
                da.accept()
                print('06시 알림 제거했습니다.')
            elif '세션이 만료 되었습니다.' in da.text:
                # 텔레그램 메시지
                da.accept()
                print('#세션완료입니다. 재 로그인 해주세요.')
                quit()
            else:
                da.accept()
                pass
        except Exception as e:
            if 'alert' in str(e):
                pass
            elif 'reachable' in str(e):
                log = traceback.format_exc()
                print(log)
                quit()
            else:
                print('창이 꺼진 오류입니다. 오류메시지', e)

        # 조회 버튼 누르기 + 0807 수정 send_keys error 수정 -> Keys.ENTER 로 바꾸기
        wait('mainframe.WorkFrame.form.divWork_131_IV1010.form.btnSearch:icontext')
        time.sleep(10)
        driver.find_element(By.ID, 'mainframe.WorkFrame.form.divWork_131_IV1010.form.btnSearch:icontext').click()
        # 0804 수정
        if n == 1:
            data = driver.wait_for_request('https://smart.hankooktech.com/SSYSTEM/IV1010/selectInvStock.do', timeout=20).body
        else:
            requested = []
            request_list = driver.requests
            for i in request_list:
                if i.url == 'https://smart.hankooktech.com/SSYSTEM/IV1010/selectInvStock.do':
                    requested.append(i)
            data = requested[-1].body
        # 원하는 정보 접근에 필요한 jsessionid 얻기
        jsessionid = driver.wait_for_request('https://smart.hankooktech.com/SSYSTEM/sys/insertLog.do').headers['cookie'].split(';')[0].split('=')[1]
        # wired_webdriver.requests[340].headers['cookie']

        cookies = {
            'JSESSIONID': f'{jsessionid}',
            # 'AWSELB': '03477D831CCA41EB98C2C9AF9E23CE77277F4B635F422E2FE809452D70536035F2F2EFE0238C423A2E3AF61848C3B9B76E5A3F4449EF5997B94ED8948F91298F4D30B8B361307C172E7D0B88B8DF78A54B97842216',
            # 'WMONID': 'RgpMo_O0Ia5',
            # 'AWSALB': 'NlF2IxQ3u+GF2to6/BIGzD92B8sxl9FRZjHSWSKNoUW2K1sAQpOjlCxLYkJS5k1QIbkCpnN8pVB0qaWKPaXLcgdVTwVrezTFBpL4ERk4EaE2FsBYSlcxrojUo4wx',
        }

        headers = {
            'authority': 'smart.hankooktech.com',
            'accept': 'application/xml, text/xml, */*',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache, no-store',
            'content-type': 'text/xml',
            'expires': '-1',
            'if-modified-since': 'Sat, 1 Jan 2000 00:00:00 GMT',
            'origin': 'https://smart.hankooktech.com',
            'pragma': 'no-cache',
            'referer': 'https://smart.hankooktech.com/',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        response = requests.post('https://smart.hankooktech.com/SSYSTEM/IV1010/selectInvStock.do', cookies=cookies, headers=headers, data=data, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 전처리 데이터
        f = soup.text.split('(255)')[-1]

        # 리스트 나눈 변수 값
        chunked_list = list_chunk(f.replace('\x1e', '\x1f').split('\x1f')[1:-2], 45)

        # 재고 고유값 리스트
        io_part_nos = []
        # 재고
        stocks = []
        data = []
        for row in chunked_list:
            io_part_nos.append(row[5])
            stocks.append(row[25])
        # bot.sendMessage(chat_id=publick_chat_name, text=str(len(io_part_no))).chat_id
        print(len(io_part_nos), io_part_nos)
        print(len(stocks), stocks)
        for io_part_no, stock in zip(io_part_nos, stocks):
            data.append({'io_part_no': io_part_no, 'stock': stock})

        header = {
            'method': 'post',
            'content-type': 'application/json',
            'x-api-key': '0BeUTq2fpUeTCEIl7O4f7gpHk92gfvd7SuvVrUsj'
        }
        datas = {
            "mb_id": "3428601436",
            "datas": data}
        # print(datas)
        print(datetime.datetime.now())
        r = requests.post('https://api.blackcircles.co.kr/stock', headers=header, json=datas)
        print(r.text)
        print(r.status_code)
    except Exception as e:
        print('추출함수 실행중 발생한 오류입니다. 오류메시지:', e)
        log = traceback.format_exc()
        print(log)
        # 텔레그램 메시지 보내기


# 웹드라이브 기다리는 함수
def wait(id_):
    wait_time.until(EC.presence_of_element_located((By.ID, id_)))


time.sleep(3)


# 스케줄 함수
def schedule_job():
    schedule.every(5).minutes.until('23:54').do(get_stock_info)


options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_experimental_option('detach', True)
driver = wired_webdriver.Chrome(ChromeDriverManager().install(), options=options)
driver.get('https://smart.hankooktech.com/')
driver.maximize_window()

# 로그인 되기전까지 대기. -> 한국타이어 웹상에 재고확인버튼 발견시 break

while True:
    time.sleep(5)
    try:
        driver.find_element(By.ID, 'mainframe.WorkFrame.form.divTop.form.btnG_IV:icontext')
        print('로그인이 완료되었습니다.')
        break
    except Exception as e:
        print('로그인을 해주세요.')

# +팝업 제거 추가. 0807
time.sleep(10)
try:
    # driver.find_element(By.ID,'mainframe.WorkFrame.detailBoardPopup10.form')
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup10.titlebar.closebutton:icontext').click()
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup11.titlebar.closebutton:icontext').click()
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup12.titlebar.closebutton:icontext').click()
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup13.titlebar.closebutton:icontext').click()
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup14.titlebar.closebutton:icontext').click()
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup15.titlebar.closebutton:icontext').click()
    driver.find_element(By.ID, 'mainframe.WorkFrame.detailBoardPopup16.titlebar.closebutton:icontext').click()
except:
    print('팝업없음')
    pass
# 웹드라이브 기본 대기시간 설정
wait_time = WebDriverWait(driver, 10)
# 웹드라이브 상황별 대기 함수

# 재고 버튼 누르기
wait('mainframe.WorkFrame.form.divTop.form.btnG_IV:icontext')
driver.find_element(By.ID, 'mainframe.WorkFrame.form.divTop.form.btnG_IV:icontext').click()
time.sleep(5)
# 재고현황 버튼 누르기
wait('mainframe.WorkFrame.form.divTop.form.pDivMenu.form.grdMenu.body.gridrow_0.cell_0_0:text')
driver.find_element(By.ID, 'mainframe.WorkFrame.form.divTop.form.pDivMenu.form.grdMenu.body.gridrow_0.cell_0_0:text').click()

get_stock_info(1)
schedule.every().day.at("06:00").do(schedule_job)
schedule.every(1).minutes.until('21:00').do(get_stock_info)
# print(schedule.get_jobs())
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except Exception as e:
    print('반복 추출함수 실행도중 발생한 오류입니다. 오류메시지:', e)
    log = traceback.format_exc()
    print(log)
