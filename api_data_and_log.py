import requests
import ast
import psycopg2
import logging
import os
from datetime import datetime, timedelta

# Создаем папку для логирования данных 
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Удаление логов старше 3 дней
for filename in os.listdir(LOG_DIR):
    file_path = os.path.join(LOG_DIR, filename)
    if os.path.isfile(file_path):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if datetime.now() - file_mtime > timedelta(days=3):
            os.remove(file_path)

# Устанавливаем формат логов
log_filename = os.path.join(LOG_DIR, f"script_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ])

# Функция для получения данных из API в нужном формате
def get_api_data(client, client_key, start, end, api_url):
    logging.info("Начинаем скачивание и обработку данных API")
    headers = {'Content-Type': 'application/json'}   
    params = {
        'client': client,
        'client_key': client_key,
        'start': start,
        'end': end}
    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info('Скачивание завершено')
    except requests.exceptions.RequestException as err:
        logging.error('Ошибка при загрузке данных %s', err)
    except Exception as err:
        logging.error('Ошибка скачивания %s', err)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ошибка разбора JSON")
    
    normalized = []

    for item in data:
      if item.get('passback_params'):
        passback = dict(ast.literal_eval(str(item.get('passback_params'))))
      else:
        passback = dict({'oauth_consumer_key': None, 'lis_result_sourcedid': None, 'lis_outcome_service_url': None})
      user_id = item.get('lti_user_id')
      is_correct = item.get('is_correct')
      attempt_type = item.get('attempt_type')
      created_at = item.get('created_at')
      oauth_consumer_key = passback.get('oauth_consumer_key')
      lis_result_sourcedid = passback.get('lis_result_sourcedid')
      lis_outcome_service_url = passback.get('lis_outcome_service_url')

      normalized_item = {
            'user_id': user_id,
            'is_correct': is_correct,
            'attempt_type': attempt_type,
            'created_at': created_at,
            'oauth_consumer_key': oauth_consumer_key,
            'lis_result_sourcedid': lis_result_sourcedid,
            'lis_outcome_service_url': lis_outcome_service_url
        }

      normalized.append(normalized_item)
      logging.info(f"Подготовлено {len(normalized)} записей для вставки в PostgreSQL")

    return normalized

# Подключаемся к нашему API
API_URL = "https://b2b.itresume.ru/api/statistics"
CLIENT = "Skillfactory"
CLIENT_KEY = "M2MGWS"
START_DATE = "2023-04-01 12:46:47.860798"
END_DATE = "2023-04-02 12:46:47.860798"
raw_data = get_api_data(CLIENT, CLIENT_KEY, START_DATE, END_DATE, API_URL)

# Подключаемся к базе данных, удаляем прошлые записи и выгружаем данные
delete_query = "delete from api_results"
conn = psycopg2.connect(
    host = "localhost",
    port = "5433",
    database = "study",
    user = "postgres",
    password = "111222333000")
cursor = conn.cursor()
cursor.execute(delete_query)
try:
    logging.info("Начало вставки данных в PostgreSQL")
    for row in raw_data:
        cursor.execute("""
                    INSERT INTO api_results (
                    user_id, is_correct, attempt_type, created_at,
                    oauth_consumer_key, lis_result_sourcedid, lis_outcome_service_url) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """, (row["user_id"], row["is_correct"], row["attempt_type"], row["created_at"],
                          row["oauth_consumer_key"], row["lis_result_sourcedid"], row["lis_outcome_service_url"]
                          ))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Данные успешно загружены в PostgreSQL")
except Exception as err:
    logging.error(f"Ошибка при вставке данных в PostgreSQL: {str(err)}")
