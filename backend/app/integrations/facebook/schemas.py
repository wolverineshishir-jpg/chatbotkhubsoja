from dataclasses import dataclass, field


@dataclass(slots=True)
class FacebookPageCandidate:
    page_id: str
    page_name: str
    page_access_token: str
    category: str | None = None
    tasks: list[str] = field(default_factory=list)
    picture_url: str | None = None


@dataclass(slots=True)
class FacebookPageProfile:
    page_id: str
    page_name: str
    category: str | None
    followers_count: int | None
    picture_url: str | None


@dataclass(slots=True)
class ParsedMessengerEvent:
    page_id: str
    sender_id: str
    recipient_id: str | None
    message_id: str
    text: str
    created_time: str | None
    raw_payload: dict


@dataclass(slots=True)
class ParsedCommentEvent:
    page_id: str
    comment_id: str
    post_id: str | None
    parent_id: str | None
    commenter_id: str | None
    commenter_name: str | None
    message: str
    created_time: str | None
    raw_payload: dict


@dataclass(slots=True)
class ParsedFacebookWebhook:
    messages: list[ParsedMessengerEvent] = field(default_factory=list)
    comments: list[ParsedCommentEvent] = field(default_factory=list)
