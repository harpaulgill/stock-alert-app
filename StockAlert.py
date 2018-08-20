from apiclient import discovery
from datetime import date
import httplib2
import requests
import schedule
import time
import Auth
import SendEmail

email = "Your email goes here"
apikey = 'Your API Key from Alpha Vantage goes here'
SCOPES = 'https://mail.google.com/'
# get a credentials.json file after making a new project on the google developer console
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'StockAlert'
authInst = Auth.Auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
credentials = authInst.get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http)


def get_labels():
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


def send_email(symbol, price, sma):
    send_inst = SendEmail.SendEmail(service)
    text = 'The price of {0} is {1} and has fallen below its 200 day simple moving average of {2}'.format(symbol, price, sma)
    message = send_inst.create_message(email, email, 'Stock Alert', text)
    send_inst.send_message('me', message)
    return


def get_daily_price(func, symbol, outputsize, today):
    payload = {'function': func, 'symbol': symbol, 'ouputsize': outputsize, 'apikey': apikey}
    r = requests.get('https://www.alphavantage.co/query', params=payload)
    parsed_json = r.json()
    parsed_json = parsed_json['Time Series (Daily)'][today]['4. close']
    return float(parsed_json)


def get_sma(func, symbol, interval, time_period, series_type,  today):
    payload = {'function': func, 'symbol': symbol, 'interval': interval, 'time_period': time_period,
               'series_type': series_type, 'apikey': apikey}
    r = requests.get('https://www.alphavantage.co/query', params=payload)
    parsed_json = r.json()
    parsed_json = parsed_json['Technical Analysis: SMA'][today]['SMA']
    return float(parsed_json)


def check_price(symbol):
    today = str(date.today())
    sma = get_sma('SMA', symbol, 'daily', '200', 'close', today)
    price = get_daily_price('TIME_SERIES_DAILY', symbol, 'compact', today)

    if price < sma:
        send_email(symbol, price, sma)
    return


def stock_alert():
    # use this function to run checkPrice with multiple different stocks
    # also ensure this program will not run on the weekends when the markets are closed
    if date.today().weekday() != 6 and date.today().weekday() != 7:
        check_price('SPY')
        check_price('DIA')
    return


schedule.every().day.at("17:30").do(stock_alert)
while True:
    schedule.run_pending()
    time.sleep(10)
    print('loop')
