import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class TimeCommand:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.browser = None

    def execute(self, command, username):
        parts = command.split(" ")
        if len(parts) < 2:
            return "Укажите город для получения времени."
        
        city = parts[1]
        time_data = self.get_time_from_browser(city)
        
        if time_data:
            return f"{username}, текущее время в {city}: {time_data}"
        else:
            return f"Не удалось найти время для города: {city}"

    def get_time_from_browser(self, city):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")  # Отключение расширений
            chrome_options.add_argument("--disable-infobars")  # Отключение инфопанели
            chrome_options.add_argument("--start-maximized")  # Максимизация окна (ускорение загрузки)
            chrome_options.add_argument("--disable-notifications")  # Отключение уведомлений
            chrome_options.add_argument("--disable-popup-blocking")  # Отключение блокировки всплывающих окон
            self.browser = webdriver.Chrome(self.driver_path)
            search_query = f"https://www.google.com/search?q=время+{city}"
            self.browser.get(search_query)
        
            time.sleep(3)
            page_source = self.browser.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            time_element = soup.find('div', class_='gsrt vk_bk FzvWSb YwPhnf')
            if time_element:
                current_time = time_element.text
                return current_time
            else:
                return None

        except Exception as e:
            print(f"Ошибка при получении времени: {str(e)}")
            return None

        finally:
            if self.browser:
                self.browser.quit()
