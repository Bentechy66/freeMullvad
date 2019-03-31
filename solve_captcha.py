import numpy as np
import cv2
from matplotlib import pyplot as plt
import pytesseract
from skimage import io
from requests import get
import bs4

pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def solve_image(captcha_url, show_image=False):
    string = ""
    print(f"Trying to break captcha")

    print(f"Grabbing {captcha_url}")

    img = io.imread(captcha_url)

    dst = img # In case we wish to view the matplot visualisation later

    denoise_passes = 5

    print("Beginning denoising")
    for i in range(1, denoise_passes + 1):
        print(f"Denoising: Pass {i} of {denoise_passes}")
        dst = cv2.fastNlMeansDenoisingColored(dst,None,10,10,7,21) # pylint: disable=no-member

    dst = cv2.resize(dst, (80, 40)) # pylint: disable=no-member

    print("Denoising Complete")
    print("Starting OCR")

    string = pytesseract.image_to_string(dst).replace("=", "")

    common_mistakes = {'S': 5, 's': 5, 't': '*', 'i': 1, 'I': 1, 'g': 8}

    print(f"OCR Got {string}, replacing common variants.")

    for key in common_mistakes:
        string = string.replace(key, str(common_mistakes[key]))

    if "+" in string or "-" in string or "*" in string or "/" in string:
        print(f"Got Captcha Text! - {string}\nSolving captcha now...")
        try:
            answer = eval(string)
        except:
            print("Captcha wasn't an evalable string, must not have been formatted correctly. Try again.")
            return False
        print(f"Got Captcha Answer! - {str(answer)}")
        return answer
    else:
        print("String did not match specified parameters.")
        return False
    if show_image:
        plt.subplot(121),plt.imshow(img)
        plt.subplot(122),plt.imshow(dst)
        plt.show()

if __name__ == "__main__":
        print("Grabbing captcha URL")
        r = get("https://mullvad.net/en/account/create/")
        soup = bs4.BeautifulSoup(r.content, "lxml")
        captcha_url = "https://mullvad.net" + soup.findAll("img", {"class": "captcha"})[0]["src"]
        solve_image(captcha_url)