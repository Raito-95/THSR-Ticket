import ssl
from typing import Any, Optional
from urllib.parse import urljoin

import requests
import truststore
from requests.adapters import HTTPAdapter
from requests.models import Response
from urllib3.util.retry import Retry

from configs.web.http_config import HTTPConfig
from configs.web.parse_html_element import BOOKING_PAGE
from configs.web.param_schema import (
    BookingRequestParams,
    ConfirmTicketRequestParams,
    ConfirmTrainRequestParams,
)
from html_parser import parse_html


class SystemTrustStoreHTTPAdapter(HTTPAdapter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        super().__init__(*args, **kwargs)

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,
        **pool_kwargs: Any,
    ) -> None:
        pool_kwargs["ssl_context"] = self.ssl_context
        super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: Any) -> Any:
        proxy_kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


class HTTPRequest:
    def __init__(self, max_retries: int = 3, timeout: int = 15) -> None:
        self.sess = requests.Session()
        retry_cfg = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            backoff_factor=0.3,
            allowed_methods=frozenset(["GET"]),
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        )
        self.sess.mount("https://", SystemTrustStoreHTTPAdapter(max_retries=retry_cfg))
        self.timeout = timeout

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
                timeout=self.timeout,
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
            response = self.sess.get(
                img_url, headers=self.common_head_html, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Security code image took too long to respond")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def submit_booking_form(
        self, params: BookingRequestParams, action_url: Optional[str] = None
    ) -> Response:
        jsessionid = self.sess.cookies.get("JSESSIONID", None)
        if not jsessionid:
            raise ValueError("No JSESSIONID found. Cannot submit booking form")

        url = (
            self._resolve_url(action_url)
            if action_url
            else HTTPConfig.SUBMIT_FORM_URL.format(jsessionid)
        )

        try:
            response = self.sess.post(
                url,
                headers=self.common_head_html,
                data=params,
                allow_redirects=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Booking form submission took too long")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def submit_train(
        self, params: ConfirmTrainRequestParams, action_url: Optional[str] = None
    ) -> Response:
        url = (
            self._resolve_url(action_url)
            if action_url
            else HTTPConfig.CONFIRM_TRAIN_URL
        )
        try:
            response = self.sess.post(
                url,
                headers=self.common_head_html,
                data=params,
                allow_redirects=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Train selection took too long")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def submit_ticket(
        self, params: ConfirmTicketRequestParams, action_url: Optional[str] = None
    ) -> Response:
        url = (
            self._resolve_url(action_url)
            if action_url
            else HTTPConfig.CONFIRM_TICKET_URL
        )
        try:
            response = self.sess.post(
                url,
                headers=self.common_head_html,
                data=params,
                allow_redirects=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Timeout: Ticket confirmation took too long")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request Error: {e}")

        return response

    def _resolve_url(self, action_url: Optional[str]) -> str:
        if not action_url:
            raise ValueError("Form action URL is empty")
        return urljoin(HTTPConfig.BASE_URL, action_url)


def parse_security_img_url(html: bytes) -> str:
    page = parse_html(html)
    element = page.find(**BOOKING_PAGE["security_code_img"])
    if element and "src" in element.attrs:
        return urljoin(HTTPConfig.BASE_URL, str(element["src"]))
    raise ValueError("Captcha image not found")
