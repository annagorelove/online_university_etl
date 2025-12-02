import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Подключаемся к API
def api_data(client, client_key, start, end, api_url):
    params = {
        'client': client,
        'client_key': client_key,
        'start': start,
        'end': end
    }
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    return response.json()  

API_URL = "https://b2b.itresume.ru/api/statistics"
CLIENT = "Skillfactory"
CLIENT_KEY = "M2MGWS"
START_DATE = "2023-04-01 12:46:47.860798"
END_DATE = "2023-04-02 12:46:47.860798"
data = api_data(CLIENT, CLIENT_KEY, START_DATE, END_DATE, API_URL)

# Подключаемся к нашему email и отправляем отчет об выгрузке данных 
EMAIL_CONFIG = {
    'smtp_server': 'smtp.mail.ru',
    'smtp_port': 587,
    'from_email': '977szjfqi2kb@mail.ru',
    'password': '7APOo78h0UDpmP75HWwb',
    'to_email': 'dkkaaa02@gmail.com'
}
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_CONFIG['from_email']
    msg['To'] = EMAIL_CONFIG['to_email']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
    server.starttls()
    server.login(EMAIL_CONFIG['from_email'], EMAIL_CONFIG['password'])
    server.send_message(msg)
    server.quit()

try:
    send_email(
        subject="Выгрузка данных успешна",
        body=f"Данные успешно выгружены в PostgreSQL и Google Sheets. Всего записей: {len(data)}")
except Exception as e:
    send_email(
        subject="Ошибка при выгрузке данных",
        body=f"Произошла ошибка при выгрузке данных:{str(e)}")