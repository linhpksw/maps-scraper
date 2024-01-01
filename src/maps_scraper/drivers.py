from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def create_driver():
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.implicitly_wait(2)
    
    return driver
