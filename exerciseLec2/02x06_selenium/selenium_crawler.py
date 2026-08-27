import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

CHROMEDRIVER_PATH = "Path to the chromedriver executable"
WINDOW_SIZE = "1000,1024"

chrome_options = Options()
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)

# Creating a chromedriver instance
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)
# if the code above doesn't work, try:
# driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH)

# get page
driver.get("https://secure.last.fm/login")

driver.implicitly_wait(
    2
)  # It instructs the webdriver to wait for a certain amount of time before elements load on the webpage.

# you can write results here on file
time.sleep(2)
driver.find_element(By.CSS_SELECTOR, "#onetrust-accept-btn-handler").click()
time.sleep(2)
driver.get_screenshot_as_file("before.png")

user_name = "YOUR_USERNAME_HERE"
password = "YOUR_PASSWORD_HERE"

# Identifying email and password textboxes
email = driver.find_element(By.ID, "id_username_or_email")
passwd = driver.find_element(By.ID, "id_password")
button = driver.find_element(By.NAME, "submit")
# Sending user_name and password to corresponding textboxes
email.send_keys(user_name)
passwd.send_keys(password)
# button.click()
# Sending a signal that RETURN key has been pressed
passwd.send_keys(Keys.RETURN)

time.sleep(3)
driver.execute_script("window.scrollTo(0, 600)")
time.sleep(2)
driver.execute_script("window.scrollTo(0, 0)")


music_link = driver.find_element(
    By.XPATH, '//div[contains(@class, "navlist--more")]//a[@href="/music"]'
)
music_link.click()

time.sleep(3)
print("Now on:", driver.current_url)
driver.get_screenshot_as_file("screenshot.png")
driver.close()
driver.quit()  # important to free up RAM
