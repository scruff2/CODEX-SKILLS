import argparse
import getpass
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

from garminconnect import Garmin


DEFAULT_TOKENSTORE = "~/.garminconnect"
DEFAULT_ACTIVITY_NAME_FRAGMENT = "hike"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Add one existing Garmin Connect gear item to matching activities "
            "that do not already list it. Dry-run is enabled by default."
        )
    )
    parser.add_argument(
        "--gear-uuid",
        help="UUID of the gear item. If omitted, --gear-name is used.",
    )
    parser.add_argument(
        "--gear-name",
        help="Case-insensitive substring used to select the gear by name.",
    )
    parser.add_argument(
        "--start-date",
        help=(
            "Optional local start date filter, YYYY-MM-DD. If omitted, the "
            "script uses the earliest dated activity already linked to the gear."
        ),
    )
    parser.add_argument(
        "--end-date",
        help="Optional local end date filter, YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--activity-name-fragment",
        default=DEFAULT_ACTIVITY_NAME_FRAGMENT,
        help=(
            "Case-insensitive activity-name fragment used to identify target "
            "activities when Garmin labels them as another activity type."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually update Garmin Connect. Without this, only prints a dry run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Garmin page size for activity reads. Default: 100.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Seconds to sleep between update calls. Default: 1.0.",
    )
    parser.add_argument(
        "--tokenstore",
        default=DEFAULT_TOKENSTORE,
        help=f"Token cache directory. Default: {DEFAULT_TOKENSTORE}",
    )
    parser.add_argument(
        "--force-login",
        action="store_true",
        help="Prompt for Garmin credentials even if a token cache already exists.",
    )
    return parser.parse_args()


def build_client(tokenstore: str, force_login: bool) -> Garmin:
    token_path = Path(tokenstore).expanduser()
    has_cached_tokens = (
        not force_login and token_path.exists() and any(token_path.iterdir())
    )
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not has_cached_tokens and not email:
        email = input("Garmin email: ").strip()
    if not has_cached_tokens and not password:
        password = getpass.getpass("Garmin password: ")

    return Garmin(
        email,
        password,
        prompt_mfa=lambda: input("Garmin MFA code: ").strip(),
    )


def coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("activityList", "gear", "gearDTOs", "items"):
            if isinstance(value.get(key), list):
                return value[key]
        return [value]
    return []


def first_present(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def gear_uuid(gear: dict[str, Any]) -> str | None:
    value = first_present(gear, ("uuid", "gearUUID", "gearUuid", "gearPk"))
    return str(value) if value is not None else None


def gear_name(gear: dict[str, Any]) -> str:
    value = first_present(
        gear,
        (
            "displayName",
            "gearName",
            "name",
            "customMakeModel",
            "model",
            "gearDisplayName",
        ),
    )
    return str(value) if value is not None else "(unnamed gear)"


def activity_id(activity: dict[str, Any]) -> str | None:
    value = first_present(activity, ("activityId", "id"))
    return str(value) if value is not None else None


def activity_name(activity: dict[str, Any]) -> str:
    value = first_present(activity, ("activityName", "name"))
    return str(value) if value is not None else "(unnamed activity)"


def activity_date(activity: dict[str, Any]) -> str:
    value = first_present(
        activity,
        ("startTimeLocal", "startTimeGMT", "beginTimestamp", "calendarDate"),
    )
    return str(value)[:10] if value is not None else ""


def in_date_window(activity: dict[str, Any], start_date: str | None, end_date: str | None) -> bool:
    current = activity_date(activity)
    if (start_date or end_date) and not current:
        return False
    if start_date and current < start_date:
        return False
    if end_date and current > end_date:
        return False
    return True


def find_profile_identifier(value: Any) -> str | None:
    preferred_keys = {
        "userprofilepk",
        "userprofileid",
        "profilepk",
        "profileid",
    }

    if isinstance(value, dict):
        for key, nested_value in value.items():
            if key.lower() in preferred_keys and nested_value not in (None, ""):
                return str(nested_value)
        for nested_value in value.values():
            found = find_profile_identifier(nested_value)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_profile_identifier(item)
            if found:
                return found
    return None


def get_user_profile_number(api: Garmin) -> str | None:
    for profile in (
        api.get_user_profile(),
        api.get_userprofile_settings(),
        api.connectapi("/userprofile-service/socialProfile"),
    ):
        found = find_profile_identifier(profile)
        if found:
            return found
    return None


def list_user_gear(api: Garmin) -> list[dict[str, Any]]:
    profile_number = get_user_profile_number(api)
    if not profile_number:
        raise RuntimeError("Could not determine Garmin user profile number.")

    return [item for item in coerce_list(api.get_gear(profile_number)) if isinstance(item, dict)]


def select_gear(api: Garmin, args: argparse.Namespace) -> tuple[str, str]:
    gear_items = list_user_gear(api)

    if args.gear_uuid:
        for item in gear_items:
            if gear_uuid(item) == args.gear_uuid:
                return args.gear_uuid, gear_name(item)
        return args.gear_uuid, "(gear UUID supplied)"

    if args.gear_name:
        matches = [
            item
            for item in gear_items
            if args.gear_name.lower() in gear_name(item).lower()
        ]
        if len(matches) == 1:
            return gear_uuid(matches[0]) or "", gear_name(matches[0])
        if len(matches) > 1:
            print("Multiple gear items matched --gear-name:")
            for item in matches:
                print(f"  {gear_uuid(item)}  {gear_name(item)}")
            raise SystemExit(2)
        print(f"No gear matched --gear-name {args.gear_name!r}.")

    print("Available Garmin gear:")
    for item in gear_items:
        print(f"  {gear_uuid(item)}  {gear_name(item)}")
    print()
    raise SystemExit("Re-run with --gear-uuid <uuid> or --gear-name <name fragment>.")


def iter_matching_activities(
    api: Garmin,
    page_size: int,
    start_date: str | None,
    end_date: str | None,
    activity_name_fragment: str,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    start = 0
    while True:
        page = coerce_list(api.get_activities(start=start, limit=page_size))
        if not page:
            return matches
        dated_items = [item for item in page if isinstance(item, dict) and activity_date(item)]
        matches.extend(
            item
            for item in dated_items
            if in_date_window(item, start_date, end_date)
            and activity_name_fragment.lower() in activity_name(item).lower()
        )
        if start_date and dated_items and all(activity_date(item) < start_date for item in dated_items):
            return matches
        if len(page) < page_size:
            return matches
        start += page_size


def linked_gear_uuids(api: Garmin, garmin_activity_id: str) -> set[str]:
    linked = coerce_list(api.get_activity_gear(garmin_activity_id))
    uuids: set[str] = set()
    for item in linked:
        if isinstance(item, dict):
            uid = gear_uuid(item)
            if uid:
                uuids.add(uid)
    return uuids


def infer_start_date_from_gear_history(api: Garmin, selected_uuid: str) -> tuple[str | None, str]:
    gear_activities = [
        activity
        for activity in coerce_list(api.get_gear_activities(selected_uuid, limit=1000))
        if isinstance(activity, dict) and activity_date(activity)
    ]
    if not gear_activities:
        return None, "gear history did not contain any dated activities"
    return min(activity_date(activity) for activity in gear_activities), "gear activity history"


def main() -> int:
    args = parse_args()
    tokenstore = str(Path(args.tokenstore).expanduser())
    api = build_client(tokenstore, args.force_login)

    api.login(tokenstore)

    selected_uuid, selected_name = select_gear(api, args)
    if not selected_uuid:
        raise RuntimeError("Selected gear did not have a UUID.")

    print(f"Selected gear: {selected_name} ({selected_uuid})")
    print("Mode:", "APPLY" if args.apply else "DRY RUN")

    if args.start_date:
        effective_start_date = args.start_date
        start_source = "command line --start-date"
    else:
        effective_start_date, start_source = infer_start_date_from_gear_history(
            api,
            selected_uuid,
        )
        if not effective_start_date:
            raise RuntimeError(
                "Could not infer a start date from Garmin gear history. "
                "Re-run with --start-date YYYY-MM-DD."
            )
    effective_end_date = args.end_date or date.today().isoformat()

    activities = iter_matching_activities(
        api,
        args.limit,
        effective_start_date,
        effective_end_date,
        args.activity_name_fragment,
    )
    print(f"Date window: {effective_start_date} through {effective_end_date}")
    print(f"Start date source: {start_source}")
    print(f"Found {len(activities)} matching activities in scope.")

    to_update: list[dict[str, Any]] = []
    already_linked = 0
    missing_id = 0

    for activity in activities:
        garmin_activity_id = activity_id(activity)
        if not garmin_activity_id:
            missing_id += 1
            continue
        if selected_uuid in linked_gear_uuids(api, garmin_activity_id):
            already_linked += 1
            continue
        to_update.append(activity)

    print(f"Already had selected gear: {already_linked}")
    print(f"Missing activity id: {missing_id}")
    print(f"Would update: {len(to_update)}")

    for activity in to_update:
        garmin_activity_id = activity_id(activity)
        label = f"{activity_date(activity)}  {garmin_activity_id}  {activity_name(activity)}"
        if args.apply:
            api.add_gear_to_activity(selected_uuid, garmin_activity_id)
            print(f"updated  {label}")
            time.sleep(args.sleep)
        else:
            print(f"dry-run  {label}")

    if not args.apply:
        print()
        print("No changes made. Re-run with --apply to update Garmin Connect.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit("\nInterrupted.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
