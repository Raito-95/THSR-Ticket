import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from bs4 import BeautifulSoup

from controller.confirm_train_flow import ConfirmTrainFlow
from controller.confirm_ticket_flow import ConfirmTicketFlow
from controller.first_page_flow import FirstPageFlow
from configs.web.param_schema import ConfirmTrainModel, ConfirmTrainRequestParams
from remote.http_request import HTTPRequest
from view_model.avail_trains import AvailTrains


@dataclass
class HTTPMeta:
    step: str
    url: str
    status_code: int
    cookies: Dict[str, str]


def parse_profile(profile_path: Optional[str]) -> Dict[str, Any]:
    if not profile_path:
        return {
            "start_station": 2,
            "dest_station": 7,
            "date": datetime.now().strftime("%Y/%m/%d"),
            "time": "15:00",
            "ID_number": "",
            "phone_number": "",
            "email_address": "",
        }

    with open(profile_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    return data


def analyze_html(html: bytes) -> Dict[str, Any]:
    page = BeautifulSoup(html, features="html.parser")

    def tag_attrs(tag: Any, keys: List[str]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for key in keys:
            val = tag.get(key)
            if val is not None:
                out[key] = str(val)
        return out

    inputs = [
        tag_attrs(t, ["name", "id", "type", "value", "checked"])
        for t in page.find_all("input")
    ]
    selects = [
        {
            **tag_attrs(t, ["name", "id"]),
            "options": [
                {
                    "value": str(o.get("value", "")),
                    "text": o.get_text(strip=True),
                    "selected": o.has_attr("selected"),
                }
                for o in t.find_all("option")
            ],
        }
        for t in page.find_all("select")
    ]
    textareas = [
        {
            **tag_attrs(t, ["name", "id"]),
            "text": t.get_text(strip=True),
        }
        for t in page.find_all("textarea")
    ]
    forms = [
        {
            **tag_attrs(f, ["name", "id", "method", "action"]),
            "input_count": len(f.find_all("input")),
            "select_count": len(f.find_all("select")),
            "textarea_count": len(f.find_all("textarea")),
        }
        for f in page.find_all("form")
    ]

    return {
        "title": (page.title.get_text(strip=True) if page.title else ""),
        "form_count": len(forms),
        "forms": forms,
        "inputs": inputs,
        "selects": selects,
        "textareas": textareas,
    }


def detect_primary_form_id(html: bytes) -> str:
    page = BeautifulSoup(html, features="html.parser")
    form = page.find("form")
    if not form:
        return ""
    form_id = form.get("id")
    return str(form_id) if form_id is not None else ""


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_html(path: Path, html: bytes) -> None:
    path.write_bytes(html)


def save_http_meta(path: Path, step: str, resp: Any, sess: Any) -> None:
    meta = HTTPMeta(
        step=step,
        url=resp.url,
        status_code=resp.status_code,
        cookies=sess.cookies.get_dict(),
    )
    write_json(path, asdict(meta))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect THSR booking page structure from local host."
    )
    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        default=None,
        help="Path to profile json (same format as main.py test mode).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="debug_dump",
        help="Output directory root.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output from booking flow helpers.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=1,
        help="Max attempts for S1 submit (captcha-sensitive).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout seconds for each request.",
    )
    parser.add_argument(
        "--go-s4",
        action="store_true",
        help="Submit S3 form and capture S4 page (may create a real booking).",
    )
    parser.add_argument(
        "--allow-booking",
        action="store_true",
        help="Allow submitting S3 (can create a real booking). Disabled by default.",
    )
    args = parser.parse_args()

    profile = parse_profile(args.profile)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output) / f"thsr_structure_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = HTTPRequest(timeout=max(5, args.timeout))

    # Step 1: booking page
    s1_resp = client.request_booking_page()
    write_html(out_dir / "s1_booking_page.html", s1_resp.content)
    write_json(out_dir / "s1_booking_page.structure.json", analyze_html(s1_resp.content))
    save_http_meta(out_dir / "s1_booking_page.meta.json", "s1_booking_page", s1_resp, client.sess)

    # Step 2: submit first page and inspect trains page/error page
    first_flow = FirstPageFlow(client=client, data_dict=profile, verbose=args.verbose)
    attempt_logs: List[Dict[str, Any]] = []
    s1_form_data: Dict[str, Any] = {}
    s2_resp = None
    reached_s2 = False

    for attempt in range(1, max(1, args.max_attempts) + 1):
        captcha_resp = client.request_security_code_img(s1_resp.content)
        (out_dir / f"s1_captcha_image.attempt{attempt}.bin").write_bytes(
            captcha_resp.content
        )
        save_http_meta(
            out_dir / f"s1_captcha.attempt{attempt}.meta.json",
            f"s1_captcha_attempt_{attempt}",
            captcha_resp,
            client.sess,
        )

        s1_form_data = first_flow.compose_form_data(
            BeautifulSoup(s1_resp.content, features="html.parser"), captcha_resp.content
        )
        write_json(out_dir / f"s1_submit.attempt{attempt}.params.json", s1_form_data)

        try:
            s2_resp = client.submit_booking_form(s1_form_data)
        except Exception as e:
            attempt_logs.append(
                {
                    "attempt": attempt,
                    "submit_error": str(e),
                }
            )
            continue
        form_id = detect_primary_form_id(s2_resp.content)
        attempt_logs.append(
            {
                "attempt": attempt,
                "form_id": form_id,
                "url": s2_resp.url,
                "status_code": s2_resp.status_code,
            }
        )
        if form_id == "BookingS2Form":
            reached_s2 = True
            break

    write_json(out_dir / "attempts.json", attempt_logs)
    write_json(out_dir / "s1_submit.params.json", s1_form_data)

    if s2_resp is None:
        summary = {
            "output_dir": str(out_dir.resolve()),
            "profile_used": profile,
            "reached_s2": False,
            "final_form_id": "",
            "attempt_count": len(attempt_logs),
            "has_trains_in_s2": False,
            "train_count": 0,
            "error": "No response received after S1 submit attempts.",
        }
        write_json(out_dir / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    write_html(out_dir / "s2_after_s1_submit.html", s2_resp.content)
    write_json(out_dir / "s2_after_s1_submit.structure.json", analyze_html(s2_resp.content))
    save_http_meta(out_dir / "s2_after_s1_submit.meta.json", "s2_after_s1_submit", s2_resp, client.sess)

    trains = AvailTrains().parse(s2_resp.content) if reached_s2 else []
    write_json(
        out_dir / "s2_trains.parsed.json",
        [
            {
                "id": t.id,
                "depart": t.depart,
                "arrive": t.arrive,
                "travel_time": t.travel_time,
                "discount_str": t.discount_str,
                "discount_tags": t.discount_tags,
                "has_early_bird": t.has_early_bird,
                "form_value": t.form_value,
            }
            for t in trains
        ],
    )

    # Step 3: submit selected train if available (inspect ticket confirmation page)
    if len(trains) > 0:
        used_fallback = False
        try:
            confirm_train_flow = ConfirmTrainFlow(
                client=client,
                book_resp=s2_resp,
                data_dict=profile,
                verbose=args.verbose,
            )
            s3_resp, s2_model = confirm_train_flow.run()
        except ValueError:
            # Structure inspection should continue even if time-window filter finds no train.
            used_fallback = True
            fallback_train = trains[0]
            fallback_params = {
                "TrainQueryDataViewPanel:TrainGroup": fallback_train.form_value,
                "BookingS2Form:hf:0": "",
            }
            s2_model = ConfirmTrainModel(**fallback_params)
            s3_resp = client.submit_train(
                cast(
                    ConfirmTrainRequestParams,
                    json.loads(s2_model.model_dump_json(by_alias=True)),
                )
            )

        write_json(
            out_dir / "s2_train_submit.params.json",
            json.loads(s2_model.model_dump_json(by_alias=True)),
        )
        if used_fallback:
            write_json(
                out_dir / "s2_train_submit.fallback.json",
                {
                    "reason": "no_train_in_time_window",
                    "selected_train_id": trains[0].id,
                    "selected_train_depart": trains[0].depart,
                    "selected_train_arrive": trains[0].arrive,
                },
            )
        write_html(out_dir / "s3_after_train_submit.html", s3_resp.content)
        write_json(
            out_dir / "s3_after_train_submit.structure.json",
            analyze_html(s3_resp.content),
        )
        save_http_meta(
            out_dir / "s3_after_train_submit.meta.json",
            "s3_after_train_submit",
            s3_resp,
            client.sess,
        )

        if not args.allow_booking:
            write_json(
                out_dir / "booking_skipped.json",
                {
                    "reason": "booking_disabled_by_default",
                    "hint": "Use --allow-booking to submit S3 (real booking risk).",
                },
            )
        elif args.go_s4:
            has_required_profile = all(
                profile.get(k)
                for k in ["ID_number", "phone_number", "email_address"]
            )
            if has_required_profile:
                confirm_ticket_flow = ConfirmTicketFlow(
                    client=client,
                    train_resp=s3_resp,
                    user_profile=profile,
                    verbose=args.verbose,
                )
                s4_resp, s3_model = confirm_ticket_flow.run()
                write_json(
                    out_dir / "s3_ticket_submit.params.json",
                    json.loads(s3_model.model_dump_json(by_alias=True)),
                )
                write_html(out_dir / "s4_after_ticket_submit.html", s4_resp.content)
                write_json(
                    out_dir / "s4_after_ticket_submit.structure.json",
                    analyze_html(s4_resp.content),
                )
                save_http_meta(
                    out_dir / "s4_after_ticket_submit.meta.json",
                    "s4_after_ticket_submit",
                    s4_resp,
                    client.sess,
                )
            else:
                write_json(
                    out_dir / "s4_skipped.json",
                    {
                        "reason": "missing_profile_fields",
                        "required": ["ID_number", "phone_number", "email_address"],
                    },
                )

    summary = {
        "output_dir": str(out_dir.resolve()),
        "profile_used": profile,
        "reached_s2": reached_s2,
        "final_form_id": detect_primary_form_id(s2_resp.content),
        "attempt_count": len(attempt_logs),
        "has_trains_in_s2": len(trains) > 0,
        "train_count": len(trains),
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
