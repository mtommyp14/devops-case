"""Pure event-contract logic, kept independent of broker and database clients."""


def build_events(count):
    events = []
    for i in range(1, count + 1):
        event = {
            "event_id": "evt-%03d" % i,
            "customer_id": "customer-%03d" % i,
            "occurred_at": "2026-01-01T00:%02d:00Z" % (i % 60),
            "schema_version": 1,
            "consent": (i % 2 == 0),
        }
        if i > count - 3:
            event.pop("consent")
            event["consent_v2"] = i % 2 == 0
            event["schema_version"] = 2
        events.append(event)
    return events


def validate_event(event):
    required = ("event_id", "customer_id", "occurred_at", "schema_version")
    missing = [field for field in required if not event.get(field)]
    if missing:
        return None, "missing required fields: " + ", ".join(missing)
    if "consent" not in event:
        if "consent_v2" in event:
            return None, "schema v2 field consent_v2 is unsupported by the current adapter"
        return None, "missing required field: consent"
    if not isinstance(event["consent"], bool):
        return None, "field consent must be boolean"
    return event["consent"], None


def adapt_event(event):
    """Map a reviewed v2 payload to the canonical consent field."""
    if "consent" in event:
        return validate_event(event)
    if "consent_v2" not in event:
        return validate_event(event)
    adapted = dict(event)
    adapted["consent"] = adapted.pop("consent_v2")
    return validate_event(adapted)
