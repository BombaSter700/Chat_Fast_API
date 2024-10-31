import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class WeatherCommand:
    def __init__(self, driver_path):
        self.driver_path = "C:\\Users\\Sanek\\Desktop\\Chat_Fast_API"
        self.browser = None

    def execute_weather(self, command, username):
        parts = command.split(" ")
        if len(parts) < 2:
            return "Укажите город для получения прогноза погоды."
        
        city = ' '.join(parts[1:])
        weather_data = self.get_weather_from_browser(city)
        
        if weather_data:
            return f"{username}, погода в {city}: {weather_data}"
        else:
            return f"Не удалось найти погоду для города: {city}"

    def get_weather_from_browser(self, city):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            
            self.browser = webdriver.Chrome(options=chrome_options)
            search_query = f"https://www.google.com/search?q=погода+{city}"
            self.browser.get(search_query)
        
            time.sleep(3)  # Ждем загрузку страницы
            page_source = self.browser.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Парсим данные о погоде
            temp_element = soup.find('span', id='wob_tm')
            condition_element = soup.find('span', id='wob_dc')
            humidity_element = soup.find('span', id='wob_hm')
            wind_element = soup.find('span', id='wob_ws')

            if temp_element and condition_element:
                temp = temp_element.text
                condition = condition_element.text
                humidity = humidity_element.text if humidity_element else "N/A"
                wind = wind_element.text if wind_element else "N/A"

                weather_info = (
                    f"Температура: {temp}°C, {condition}. "
                    f"Влажность: {humidity}. Ветер: {wind}."
                )
                return weather_info
            else:
                return None

        except Exception as e:
            print(f"Ошибка при получении погоды: {str(e)}")
            return None

        finally:
            if self.browser:
                self.browser.quit()
