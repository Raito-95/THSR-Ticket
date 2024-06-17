class HTTPConfig:
    BASE_URL = "https://irs.thsrc.com.tw"
    BOOKING_PAGE_URL = f"{BASE_URL}/IMINT/?locale=tw"
    SUBMIT_FORM_URL = f"{BASE_URL}/IMINT/;jsessionid={{}}?wicket:interface=:0:BookingS1Form::IFormSubmitListener"
    CONFIRM_TRAIN_URL = (
        f"{BASE_URL}/IMINT/?wicket:interface=:1:BookingS2Form::IFormSubmitListener"
    )
    CONFIRM_TICKET_URL = (
        f"{BASE_URL}/IMINT/?wicket:interface=:2:BookingS3Form::IFormSubmitListener"
    )

    class HTTPHeader:
        USER_AGENT = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
        )
        ACCEPT_HTML = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        )
        ACCEPT_IMG = "image/webp,*/*"
        ACCEPT_LANGUAGE = "zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3"
        ACCEPT_ENCODING = "gzip, deflate, br"
        BOOKING_PAGE_HOST = "irs.thsrc.com.tw"
