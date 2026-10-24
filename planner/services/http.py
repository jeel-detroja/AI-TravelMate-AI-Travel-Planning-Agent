import logging
import time

import requests
from django.conf import settings

log = logging.getLogger("planner")


class ServiceError(Exception):
    """Raised when an external service fails after handling."""


def get_json(url, params=None, method="GET", data=None, headers=None, retries=2, timeout=None):
    cfg = settings.TRAVELMATE
    hdrs = {"User-Agent": cfg["USER_AGENT"]}
    if headers:
        hdrs.update(headers)
    effective_timeout = timeout or cfg["HTTP_TIMEOUT"]
    last = None

    for attempt in range(retries + 1):
        try:
            resp = requests.request(
                method,
                url,
                params=params,
                data=data,
                headers=hdrs,
                timeout=effective_timeout,
            )
            if resp.status_code in (429, 504):
                wait = min(2**attempt, 4)
                log.warning("%s from %s, backing off %ss", resp.status_code, url, wait)
                time.sleep(wait)
                last = ServiceError("The provider is busy or rate-limited.")
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            last = ServiceError("The service timed out.")
            log.warning("Timeout calling %s", url)
        except requests.exceptions.RequestException as exc:
            last = ServiceError("The service is temporarily unavailable.")
            log.warning("Request error calling %s: %s", url, exc.__class__.__name__)
        except ValueError:
            last = ServiceError("The service returned invalid data.")
            log.warning("Non-JSON response from %s", url)
            break

    raise last or ServiceError("Unknown service error.")
