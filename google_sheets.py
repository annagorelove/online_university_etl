import requests
import pandas as pd
import gspread 

# Подключаемся к API
API_URL = "https://b2b.itresume.ru/api/statistics" 
CLIENT = "Skillfactory"
CLIENT_KEY = "M2MGWS" 
START_DATE = "2023-04-01 12:46:47.860798"
END_DATE = "2023-05-01 12:46:47.860798"


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

data = api_data(CLIENT, CLIENT_KEY, START_DATE, END_DATE, API_URL)

# Создаем датафрейм и агрегируем данные
df = pd.DataFrame(data)
df['created_at'] = pd.to_datetime(df['created_at'])
df['date'] = df['created_at'].dt.date
agg_df = df.groupby('date').agg(
    total_attempts=pd.NamedAgg(column='attempt_type', aggfunc='count'),
    successful_attempts=pd.NamedAgg(column='is_correct', aggfunc='sum'),
    unique_users=pd.NamedAgg(column='lti_user_id', aggfunc=pd.Series.nunique)
).reset_index()

# Загружаем данные в созданную таблицу Google Sheets
gc = gspread.service_account(filename='creds.json')
wks = gc.open('MonthlyAPiStat').sheet1
wks.clear()
wks.append_row(["Date", "Total Attempts", "Successful Attempts", "Unique Users"])
for _, row in agg_df.iterrows():
    wks.append_row([str(row['date']), row['total_attempts'], row['successful_attempts'], row['unique_users']])
print("Данные успешно загружены в Google Sheets!")