from typing import Mapping, Any
import requests
from requests.adapters import HTTPAdapter
from requests.models import Response
from bs4 import BeautifulSoup

from configs.web.http_config import HTTPConfig
from configs.web.parse_html_element import BOOKING_PAGE


class HTTPRequest:
    def __init__(self, max_retries: int = 3) -> None:
        self.sess = requests.Session()
        self.sess.mount("https://", HTTPAdapter(max_retries=max_retries))

        self.common_head_html: dict = {
            "Host": HTTPConfig.HTTPHeader.BOOKING_PAGE_HOST,
            "User-Agent": HTTPConfig.HTTPHeader.USER_AGENT,
            "Accept": HTTPConfig.HTTPHeader.ACCEPT_HTML,
            "Accept-Language": HTTPConfig.HTTPHeader.ACCEPT_LANGUAGE,
            "Accept-Encoding": HTTPConfig.HTTPHeader.ACCEPT_ENCODING,
        }

    def request_booking_page(self) -> Response:
        try:
            response = self.sess.get(
                HTTPConfig.BOOKING_PAGE_URL,
                headers=self.common_head_html,
                allow_redirects=True,
                timeout=15,
            )
            response.raise_for_status()

            jsessionid = self.sess.cookies.get("JSESSIONID")

            if not jsessionid:
                raise ValueError("JSESSIONID not found")

        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Booking page took too long to respond")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def request_security_code_img(self, book_page: bytes) -> Response:
        img_url = parse_security_img_url(book_page)

        try:
            response = self.sess.get(img_url, headers=self.common_head_html, timeout=15)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Security code image took too long to respond")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def submit_booking_form(self, params: Mapping[str, Any]) -> Response:
        jsessionid = self.sess.cookies.get("JSESSIONID", None)
        if not jsessionid:
            raise ValueError("No JSESSIONID found. Cannot submit booking form")

        url = HTTPConfig.SUBMIT_FORM_URL.format(jsessionid)

        try:
            response = self.sess.post(
                url,
                headers=self.common_head_html,
                params=params,
                allow_redirects=True,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Booking form submission took too long")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def submit_train(self, params: Mapping[str, Any]) -> Response:
        try:
            response = self.sess.post(
                HTTPConfig.CONFIRM_TRAIN_URL,
                headers=self.common_head_html,
                params=params,
                allow_redirects=True,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Train selection took too long")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def submit_ticket(self, params: Mapping[str, Any]) -> Response:
        try:
            response = self.sess.post(
                HTTPConfig.CONFIRM_TICKET_URL,
                headers=self.common_head_html,
                params=params,
                allow_redirects=True,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Ticket confirmation took too long")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response


def parse_security_img_url(html: bytes) -> str:
    page = BeautifulSoup(html, features="html.parser")
    element = page.find(**BOOKING_PAGE["security_code_img"])
    if element and "src" in element.attrs:
        return str(HTTPConfig.BASE_URL) + element["src"]
    raise ValueError("Captcha image not found")
