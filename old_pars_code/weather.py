import requests
from bs4 import BeautifulSoup

class WeatherCommand:
    def __init__(self):
        self.base_url = "https://yandex.ru/pogoda/"

    def get_weather(self, city):
        city_url = city.lower().replace(" ", "-")
        url = f"{self.base_url}{city_url}"

        response = requests.get(url)
        if response.status_code != 200:
            return f"Не удалось получить данные о погоде для {city}"

        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            temp = soup.find('span', class_='temp__value').text
            weather_condition = soup.find('div', class_='link__condition').text
            feels_like = soup.find('div', class_='term__value').find('span', class_='temp__value').text
            wind_speed = soup.find('span', class_='wind-speed').text
            humidity = soup.find('div', class_='term term_orient_v fact__humidity').find('div', class_='term__value').text

            weather_info = (
                f"Погода в {city.capitalize()}: Температура {temp}°C, "
                f"{weather_condition}. Ощущается как {feels_like}°C. "
                f"Скорость ветра {wind_speed} м/с. Влажность: {humidity}."
            )

            return weather_info

        except AttributeError:
            return "Не удалось найти данные о погоде для указанного города."

    def execute(self, command, username):
        parts = command.split()
        if len(parts) < 2:
            return "Укажите город для получения прогноза погоды."

        city = parts[1]
        return self.get_weather(city)
