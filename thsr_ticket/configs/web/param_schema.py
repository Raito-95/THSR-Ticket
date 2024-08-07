import re
from datetime import date, datetime
from typing import Mapping, Any, Optional

from pydantic import BaseModel as PydanticBaseModel, Field, field_validator

from configs.common import AVAILABLE_TIME_TABLE


BOOKING_SCHEMA: Mapping[str, Any] = {
    "type": "object",
    "properties": {
        "BookingS1Form:hf:0": {"type": "string"},
        "selectStartStation": {
            "type": "integer",
            "enum": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        },
        "selectDestinationStation": {
            "type": "integer",
            "enum": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        },
        "trainCon:trainRadioGroup": {
            "type": "integer",
            "enum": [0, 1],  # Standard car / Business car
        },
        "tripCon:typesoftrip": {
            "type": "integer",
            "enum": [0, 1],  # single trip / round trip
        },
        "seatCon:seatRadioGroup": {
            "type": "string",  # Seat preference (None / Window seat / Aisle seat)
        },
        "bookingMethod": {
            "type": "string",
            "pattern": "radio[0-9]+",
        },
        "toTimeInputField": {"type": "string"},  # format: yyyy/mm/dd
        "toTimeTable": {
            "type": "string",
            "enum": AVAILABLE_TIME_TABLE,  # Use the imported AVAILABLE_TIME_TABLE
        },
        "toTrainIDInputField": {"type": "string"},
        "backTimeInputField": {"type": "string"},
        "backTimeTable": {
            "type": "string",
            "enum": AVAILABLE_TIME_TABLE,  # Use the imported AVAILABLE_TIME_TABLE
        },
        "backTrainIDInputField": {"type": "string"},
        "ticketPanel:rows:0:ticketAmount": {
            "type": "string",  # Adult ticket
            "enum": ["0F", "1F", "2F", "3F", "4F", "5F", "6F", "7F", "8F", "9F", "10F"],
        },
        "ticketPanel:rows:1:ticketAmount": {
            "type": "string",  # Child ticket (6~11)
            "enum": ["0H", "1H", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H"],
        },
        "ticketPanel:rows:2:ticketAmount": {
            "type": "string",  # Disabled ticket (Taiwan only)
            "enum": ["0W", "1W", "2W", "3W", "4W", "5W", "6W", "7W", "8W", "9W", "10W"],
        },
        "ticketPanel:rows:3:ticketAmount": {
            "type": "string",  # Elder ticket (Taiwan only)
            "enum": ["0E", "1E", "2E", "3E", "4E", "5E", "6E", "7E", "8E", "9E", "10E"],
        },
        "ticketPanel:rows:4:ticketAmount": {
            "type": "string",  # College student ticket (Taiwan only)
            "enum": ["0P", "1P", "2P", "3P", "4P", "5P", "6P", "7P", "8P", "9P", "10P"],
        },
        "homeCaptcha:securityCode": {"type": "string"},
    },
    "required": [
        "selectStartStation",
        "selectDestinationStation",
        "toTimeTable",
        "homeCaptcha:securityCode",
    ],
    "additionalProperties": False,
}

CONFIRM_TRAIN_SCHEMA: Mapping[str, Any] = {
    "type": "object",
    "properties": {
        "BookingS2Form:hf:0": {"type": "string"},
        "TrainQueryDataViewPanel:TrainGroup": {"type": "string"},
    },
    "required": ["TrainQueryDataViewPanel:TrainGroup"],
    "additionalProperties": False,
}

CONFIRM_TICKET_SCHEMA: Mapping[str, Any] = {
    "type": "object",
    "properties": {
        "BookingS3FormSP:hf:0": {"type": "string"},
        "diffOver": {"type": "integer"},
        "idInputRadio": {"type": "integer"},
        "dummyId": {"type": "string"},
        "dummyPhone": {"type": "string"},
        "email": {"type": "string"},
        "agree": {"type": "string", "enum": ["on", ""]},
        "isGoBackM": {"type": "string"},
        "backHome": {"type": "string"},
        "TgoError": {"type": "string"},
        "TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup": {
            "type": "string"
        },
    },
    "required": ["agree", "dummyId"],
    "additionalProperties": False,
}


class BaseModel(PydanticBaseModel):
    class Config:
        populate_by_name = True
        json_encoders = {date: lambda dt: dt.strftime("%Y/%m/%d")}


class BookingModel(BaseModel):
    start_station: int = Field(..., alias="selectStartStation")
    dest_station: int = Field(..., alias="selectDestinationStation")
    search_by: str = Field(..., alias="bookingMethod")
    trip_con: int = Field(..., alias="tripCon:typesoftrip")
    outbound_date: str = Field(..., alias="toTimeInputField")
    outbound_time: str = Field(..., alias="toTimeTable")
    security_code: str = Field(..., alias="homeCaptcha:securityCode")
    seat_prefer: str = Field(..., alias="seatCon:seatRadioGroup")
    form_mark: str = Field("", alias="BookingS1Form:hf:0")
    class_type: int = Field(0, alias="trainCon:trainRadioGroup")
    inbound_date: Optional[str] = Field(None, alias="backTimeInputField")
    inbound_time: Optional[str] = Field(None, alias="backTimeTable")
    to_train_id: Optional[str] = Field(None, alias="toTrainIDInputField")
    back_train_id: Optional[str] = Field(None, alias="backTrainIDInputField")
    adult_ticket_num: str = Field("1F", alias="ticketPanel:rows:0:ticketAmount")
    child_ticket_num: str = Field("0H", alias="ticketPanel:rows:1:ticketAmount")
    disabled_ticket_num: str = Field("0W", alias="ticketPanel:rows:2:ticketAmount")
    elder_ticket_num: str = Field("0E", alias="ticketPanel:rows:3:ticketAmount")
    college_ticket_num: str = Field("0P", alias="ticketPanel:rows:4:ticketAmount")

    @field_validator("start_station", "dest_station")
    def check_station(cls, value):
        if value not in range(1, 13):
            raise ValueError(f"Unknown station number: {value}")
        return value

    @field_validator("search_by")
    def check_search_by(cls, value):
        if not re.match(r"radio\d+", value):
            raise ValueError(f"Invalid search_by format: {value}")
        return value

    @field_validator("trip_con")
    def check_types_of_trip(cls, value):
        if value not in [0, 1]:
            raise ValueError(f"Invalid type of trip: {value}")
        return value

    @field_validator("outbound_date", "inbound_date", mode="before")
    def check_date(cls, value):
        if value is None:
            return date.today().strftime("%Y/%m/%d")
        if matched := re.match(r"\d{8}", value):
            # 20220101
            target_date = datetime.strptime(matched.string, "%Y%m%d").date()
        elif matched := re.match(r"\d{4}-[0]?\d+-[0]?\d+", value):
            # 2022-01-01, 2022-1-1
            target_date = datetime.strptime(matched.string, "%Y-%m-%d").date()
        elif matched := re.match(r"\d{4}/[0]?\d+/[0]?\d+", value):
            # 2022/01/01, 2022/10/1
            target_date = datetime.strptime(matched.string, "%Y/%m/%d").date()
        else:
            raise ValueError(f"Failed to parse the date string: {value}")

        if target_date < date.today():
            raise ValueError(
                f"Target date should not be earlier than today: {target_date}"
            )
        return target_date.strftime("%Y/%m/%d")

    @field_validator("outbound_time", "inbound_time", mode="before")
    def check_time(cls, value):
        if value is None:
            return value
        if value not in AVAILABLE_TIME_TABLE:
            raise ValueError(f"Unknown time string: {value}")
        return value

    @field_validator("adult_ticket_num")
    def check_adult_ticket_num(cls, value):
        if not re.match(r"\d+F", value):
            raise ValueError(f"Invalid adult ticket num format: {value}")
        return value

    @field_validator("child_ticket_num")
    def check_child_ticket_num(cls, value):
        if not re.match(r"\d+H", value):
            raise ValueError(f"Invalid child ticket num format: {value}")
        return value

    @field_validator("disabled_ticket_num")
    def check_disabled_ticket_num(cls, value):
        if not re.match(r"\d+W", value):
            raise ValueError(f"Invalid disabled ticket num format: {value}")
        return value

    @field_validator("elder_ticket_num")
    def check_elder_ticket_num(cls, value):
        if not re.match(r"\d+E", value):
            raise ValueError(f"Invalid elder ticket num format: {value}")
        return value

    @field_validator("college_ticket_num")
    def check_college_ticket_num(cls, value):
        if not re.match(r"\d+P", value):
            raise ValueError(f"Invalid college ticket num format: {value}")
        return value


class Train(BaseModel):
    id: int
    depart: str
    arrive: str
    travel_time: str
    discount_str: str
    form_value: str


class ConfirmTrainModel(BaseModel):
    selected_train: str = Field(..., alias="TrainQueryDataViewPanel:TrainGroup")
    form_mark: str = Field("", alias="BookingS2Form:hf:0")


class ConfirmTicketModel(BaseModel):
    personal_id: str = Field(..., alias="dummyId")
    phone_num: str = Field(..., alias="dummyPhone")
    member_radio: str = Field(
        ...,
        alias="TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup",
        description="非高鐵會員, 企業會員 / 高鐵會員 / 企業會員統編",
    )
    form_mark: str = Field("", alias="BookingS3FormSP:hf:0")
    id_input_radio: int = Field(
        0, alias="idInputRadio", description="0: 身份證字號 / 1: 護照號碼"
    )
    diff_over: int = Field(1, alias="diffOver")
    email: str = Field("", alias="email")
    agree: str = Field("on", alias="agree")
    go_back_m: str = Field("", alias="isGoBackM")
    back_home: str = Field("", alias="backHome")
    tgo_error: int = Field(1, alias="TgoError")
