"""
@describe:
@fileName: cookies_downloader.py
@time    : 2025/12/23 下午2:49
@author  : duke
"""
import time
import json
from selenium import webdriver
from selenium.common import InvalidSessionIdException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import os

chrome_options = Options()
chrome_service = Service(executable_path='resource/chromedriver.exe')
wd = webdriver.Chrome(service=chrome_service, options=chrome_options)


if not os.path.exists('cookies'):
    os.mkdir('cookies')

try:
    while wd.current_window_handle:
        wd.get('https://h.liepin.com/')

        dom = WebDriverWait(wd, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main-container"]/div/div[3]/div/div/ul/span')
            )
        )

        dom.click()

        while wd.current_url != 'https://h.liepin.com/':
            time.sleep(1)

        dom = WebDriverWait(wd, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main-container"]/header/div[1]/div/div[2]/div[2]/div[1]/a/span')
            )
        )

        name = dom.text

        with open(f'cookies/{name}_cookies_lp.json', 'w') as f:
            json.dump(wd.get_cookies(), f)

        wd.delete_all_cookies()

except InvalidSessionIdException:
    pass
finally:
    wd.quit()


