from zipfile import ZipFile
import requests
from os import remove, system

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

import solve_captcha

def download_file_from_server_endpoint(server_endpoint, local_file_path, cookies_dict, data_dict):
 
    # Send HTTP GET request to server and attempt to receive a response
    response = requests.post(url=server_endpoint, data=data_dict, cookies=cookies_dict)
    
    # If the HTTP GET request can be served
    if response.status_code == 200:
 
        # Write the file contents in the response to a file specified by local_file_path
        with open(local_file_path, 'wb') as local_file:
            for chunk in response.iter_content(chunk_size=128):
                local_file.write(chunk)

def get_config(driver, platform, region, port, use_ip_addresses):
    captcha_solved = False
    while not captcha_solved:
        driver.get("https://mullvad.net/en/account/create/")
        captcha_element = driver.find_element_by_class_name("captcha")
        captcha_answer = solve_captcha.solve_image(captcha_element.get_attribute("src"))
        if captcha_answer == False: # We couldn't solve the captcha, we need to get a new one and try again
            continue
        captcha_answer_input = driver.find_element_by_id("id_captcha_1")
        captcha_answer_input.send_keys(str(captcha_answer))
        current_url = driver.current_url
        captcha_answer_input.send_keys(webdriver.common.keys.Keys.RETURN)
        webdriver.support.ui.WebDriverWait(driver, 15).until(EC.url_changes(current_url))
        if driver.current_url == "https://mullvad.net/en/account/welcome/":
            captcha_solved = True
        else:
            continue # Try again

    # If we get here, we've bypassed the captcha! Yay!

    webdriver.support.ui.WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.NAME, "account-number")))

    account_number = driver.find_element_by_name("account-number").get_attribute("value")
    
    print(f"Got account number! - {account_number}")

    driver.get("https://mullvad.net/en/download/config/")
    csrf_middleware_token = driver.find_element_by_name("csrfmiddlewaretoken").get_attribute("value")

    print("Grabbing Cookies & CSRFs...")

    
    cookies_list = driver.get_cookies()
    cookies_dict = {}
    for cookie in cookies_list:
        cookies_dict[cookie['name']] = cookie['value']

    csrf_token = cookies_dict.get("csrftoken")
    session_id = cookies_dict.get("sessionid")

    print(f"Got CSRFs and Cookies: CSRF is {csrf_token}, Session ID is {session_id}, CSRF-Middleware is {csrf_middleware_token}")

    print("Downloading file...")
    download_file_from_server_endpoint("https://mullvad.net/en/download/config/", "downloaded_configs/out.zip", {
        'csrftoken': csrf_token,
        'sessionid': session_id}, {
        'csrfmiddlewaretoken': csrf_middleware_token,
        'account_token': account_number,
        'platform': platform,
        'region': region,
        'port': port,
        'use_ip': use_ip_addresses})

    driver.quit()
    return True

def manage_zip_file():
    print("Unzipping file")
    with ZipFile('downloaded_configs/out.zip', 'r') as zip_obj:
    # Extract all the contents of zip file in different directory
        zip_obj.extractall('downloaded_configs')
    print("Cleaning up...")

def connect_to_vpn(platform, region):
    print("Connecting to VPN via openvpn commandline...")
    system(f'start /wait cmd /c "cd downloaded_configs/mullvad_config_{platform}_{region}/ && openvpn mullvad_{region}.ovpn && pause"')
    print("Thanks for using FreeMulvad(tm)")


def main(platform="windows", port=0, region="gb", use_ip_addresses="no"):
    options = webdriver.firefox.options.Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    get_config(driver, platform, region, port, use_ip_addresses)
    manage_zip_file()
    connect_to_vpn(platform, region)
    
