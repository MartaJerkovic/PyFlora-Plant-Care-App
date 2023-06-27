import requests
import datetime

def current_temperature_ow():

    api_key = 'YOUR_API_KEY'
    city = 'YOUR_CITY'

    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}'

    response = requests.get(url)

    if response.status_code == 200:
        
        data = response.json()
        temperature_celsius = data['main']['temp']
        current_time = datetime.datetime.now().time().strftime("%H:%M:%S")
        #print(f"Time: {current_time}. Current Temperature in {city}: {temperature_celsius}°C")
        return round(temperature_celsius, 2)

    else:
        print("Failed to retrieve weather data. Status Code:", response.status_code)
        return None
    
#current_temperature_ow()
