import json
import requests
import logging
from google.oauth2 import service_account
import google.auth.transport.requests
from django.conf import settings
from .models import FCMToken

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = settings.BASE_DIR / "firebase-service-account.json"
PROJECT_ID = "guestconnect2-341a2"


# --------------------------------------------------
# AUTH
# --------------------------------------------------
def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token


# --------------------------------------------------
# LOW LEVEL SEND
# --------------------------------------------------
def send_fcm_message(token, title, body, device_type="web", data=None):
    access_token = get_access_token()
    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

    message = {
        "message": {
            "token": token,
            "notification": {
                "title": title,
                "body": body,
            }
        }
    }

    # Optional DATA payload
    if data:
        message["message"]["data"] = {k: str(v) for k, v in data.items()}

    if device_type == "android":
        message["message"]["android"] = {
            "priority": "HIGH",
            "notification": {"sound": "default"},
        }

    if device_type == "ios":
        message["message"]["apns"] = {
            "payload": {
                "aps": {
                    "alert": {"title": title, "body": body},
                    "sound": "default",
                }
            }
        }

    if device_type == "web":
        message["message"]["webpush"] = {
            "headers": {"TTL": "86400"},
            "notification": {
                "icon": "/static/images/icon-192.png"
            }
        }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    response = requests.post(url, headers=headers, json=message)

    if response.status_code != 200:
        logger.error(f"FCM error: {response.text}")
        return response.json()

    return response.json()


# --------------------------------------------------
# USER LEVEL SEND (USED BY create_notification)
# --------------------------------------------------
def send_push_notification_to_user(user, title, body, data=None):
    tokens = FCMToken.objects.filter(user=user, is_active=True)

    if not tokens.exists():
        logger.debug(f"No active FCM tokens for user: {user}")
        return

    for token in tokens:
        result = send_fcm_message(
            token.token,
            title,
            body,
            device_type=token.device_type,
            data=data,
        )

        if "error" in result:
            error_code = result["error"].get("details", [{}])[0].get("errorCode")
            if error_code in ["UNREGISTERED", "INVALID_ARGUMENT", "SENDER_ID_MISMATCH"]:
                token.deactivate()
                continue

        token.mark_as_used()


# --------------------------------------------------
# MULTI USER SEND (USED BY bulk notifications)
# --------------------------------------------------
def send_push_notification_to_users(users, title, body, data=None):
    for user in users:
        send_push_notification_to_user(user, title, body, data)
