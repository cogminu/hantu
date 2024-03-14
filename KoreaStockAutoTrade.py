import requests
import json
import datetime
import time
from config import APP_KEY, APP_SECRET, CANO, ACNT_PRDT_CD, URL_BASE_REAL, URL_BASE_FAKE, DISCORD_WEBHOOK_URL

"""===VARIABLES==="""
momentum_weight = 0.1 # default = 0.5
URL_BASE = URL_BASE_REAL


"""===CONSTANTS===DO=NOT=CHANGE=THESE==="""
mon, tue, wed, thr, fri, sat, sun = [0, 1, 2, 3, 4, 5, 6]


def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)


def get_access_token():
    """토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN


def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        'content-Type': 'application/json',
        'appKey': APP_KEY,
        'appSecret': APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey


def get_current_price(code="005930"):
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey":APP_KEY,
               "appSecret":APP_SECRET,
               "tr_id":"FHKST01010100"}
    params = {
        "fid_cond_mrkt_div_code":"J",
        "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])


def get_target_price(code="005930", weight=0.5):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey":APP_KEY,
               "appSecret":APP_SECRET,
               "tr_id":"FHKST01010400"}
    params = {
        "fid_cond_mrkt_div_code":"J",
        "fid_input_iscd":code,
        "fid_org_adj_prc":"1",
        "fid_period_div_code":"D"
    }
    res = requests.get(URL, headers=headers, params=params)
    stck_oprc = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    stck_hgpr = int(res.json()['output'][1]['stck_hgpr']) #전일 고가
    stck_lwpr = int(res.json()['output'][1]['stck_lwpr']) #전일 저가
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * weight
    return target_price

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
               "authorization":f"Bearer {ACCESS_TOKEN}",
               "appKey":APP_KEY,
               "appSecret":APP_SECRET,
               "tr_id":"TTTC8434R",
               "custtype":"P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    send_message(f"평가액 : {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"손익합 : {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    send_message(f"총평가액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json",
               "authorization":f"Bearer {ACCESS_TOKEN}",
               "appKey":APP_KEY,
               "appSecret":APP_SECRET,
               "tr_id":"TTTC8908R",
               "custtype":"P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    send_message(f"예수금: {cash}원")
    return int(cash)

def buy(code="005930", qty="1"):
    """주식 시장가 매수"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0802U",
               "custtype": "P",
               "hashkey": hashkey(data)
               }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        #send_message(f"[매수성공]{str(res.json())}")
        send_message(f"[매수성공]")
        return True
    else:
        #send_message(f"[매수실패]{str(res.json())}")
        send_message(f"[매수실패]")
        return False

def sell(code="005930", qty="1"):
    """주식 시장가 매도"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0801U",
               "custtype": "P",
               "hashkey": hashkey(data)
               }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        #send_message(f"[매도성공]{str(res.json())}")
        send_message(f"[매도성공]")
        return True
    else:
        #send_message(f"[매도실패]{str(res.json())}")
        send_message(f"[매도실패]")
        return False

# 자동매매 시작
# try:
ACCESS_TOKEN = get_access_token() # API사용을 위해 발행받는 토큰. 자동매매를 돌릴때마다 새로 갱신.

symbol_list = ["003490", "035720", "000660", "069500"]  # 매수 희망 종목 리스트
bought_list = []  # 매수 완료된 종목 리스트
total_cash = get_balance()  # 보유 현금 조회
stock_dict = get_stock_balance()  # 보유 주식 조회
for sym in stock_dict.keys():
    bought_list.append(sym)
target_buy_count = 3  # 매수할 종목 수
buy_percent = 0.33  # 종목당 매수 금액 비율
buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산
soldout = False


send_message("국내 주식 자동매매 프로그램 시작")

while True:
    t_now = datetime.datetime.now()
    t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
    t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
    t_sell = t_now.replace(hour=10, minute=15, second=0, microsecond=0)
    t_exit = t_now.replace(hour=10, minute=20, second=0, microsecond=0)
    today = datetime.datetime.today().weekday()

    # 토요일이나 일요일이면 자동 종료
    if today == sat or today == sun:  # 토요일이나 일요일이면 자동 종료
        send_message("주말입니다. 프로그램 종료")
        break

    # 평일~
    # ~ AM 09:00 프로그램 종료
    if t_now < t_9:
        send_message("폐장 시간. 프로그램을 종료")
        break

    # AM 09:00 ~ 09:05 : 잔여 수량 매도
    if t_9 < t_now < t_start and soldout == False:
        for sym, qty in stock_dict.items():
            sell(sym, qty)
        soldout == True
        bought_list = []
        stock_dict = get_stock_balance()

    # AM 09:05 ~ PM 03:15 : 매수
    if t_start < t_now < t_sell:
        for sym in symbol_list:
            if len(bought_list) < target_buy_count:
                if sym in bought_list:
                    continue
                target_price = get_target_price(sym, momentum_weight)
                current_price = get_current_price(sym)
                if target_price < current_price:
                    buy_qty = 0  # 매수할 수량 초기화
                    buy_qty = int(buy_amount // current_price)
                    if buy_qty > 0:
                        send_message(f"{sym} 목표가 달성({target_price} < {current_price}) 매수를 시도.")
                        result = buy(sym, buy_qty)
                        if result:
                            soldout = False
                            bought_list.append(sym)
                            get_stock_balance()
                time.sleep(1)
        time.sleep(1)
        if t_now.minute == 30 and t_now.second <= 5:
            get_stock_balance()
            time.sleep(5)

    # PM 03:15 ~ PM 03:20 : 일괄 매도
    if t_sell < t_now < t_exit:
        if soldout == False:
            stock_dict = get_stock_balance()
            for sym, qty in stock_dict.items():
                sell(sym, qty)
            soldout = True
            bought_list = []
            time.sleep(1)

    # PM 03:20 ~ : 프로그램 종료
    if t_exit < t_now:
        send_message("폐장시간. 프로그램 종료")
        break

# except Exception as e:
#     send_message(f"[오류 발생]{e}")
#     time.sleep(1)