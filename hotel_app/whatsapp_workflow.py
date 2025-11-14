"""
Core WhatsApp workflow orchestration for the hotel guest experience.

This module handles:
    * Conversation state management for WhatsApp guests
    * Automatic greetings, menus, and ticket creation
    * Request type detection using keyword mappings
    * Feedback collection flows after checkout
    * Proactive notifications for check-in / check-out events
    * Logging of inbound / outbound WhatsApp messages
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Department,
    FeedbackQuestion,
    FeedbackResponse,
    FeedbackSession,
    Guest,
    RequestKeyword,
    RequestType,
    ServiceRequest,
    UnmatchedRequest,
    Voucher,
    WhatsAppConversation,
    WhatsAppMessage,
)
from .twilio_service import twilio_service

logger = logging.getLogger(__name__)


GREETING_KEYWORDS = {
    "hi",
    "hello",
    "hey",
    "hola",
    "namaste",
    "good morning",
    "good afternoon",
    "good evening",
}

AFFIRMATIVE_KEYWORDS = {"yes", "yeah", "yup", "sure", "ok", "okay", "y"}

NEGATIVE_KEYWORDS = {"no", "nope", "nah", "n"}


@dataclass
class DetectedRequest:
    """Container for detected request metadata."""

    request_type: RequestType
    matched_keywords: List[str]
    score: int
    matched_keywords: Sequence[str]
    score: int


class WhatsAppWorkflow:
    """Central handler for WhatsApp message flows."""

    MENU_MESSAGE_PROMPT = "Please choose one of the options below:"

    UNKNOWN_GUEST_MESSAGE = (
        "Hi! We couldn’t find a booking linked to this number. "
        "Please contact the reception to link your number."
    )
    REQUEST_PROMPT_MESSAGE = (
        "Please describe your issue (for example: 'Need housekeeping', 'TV not working', etc.)"
    )
    UNMATCHED_CONFIRMATION = (
        "We are working on your request. Our team will assist you shortly."
    )
    INVALID_OPTION_MESSAGE = "Sorry, I didn’t understand that. Please choose an option from the menu."
    EMPTY_MESSAGE_PROMPT = (
        "Sorry, I didn’t catch that. Please reply with a valid option or describe your request."
    )

    FEEDBACK_THANK_YOU_BASE = (
        "Thank you for your valuable feedback, {guest_name}. We truly appreciate your time!"
    )

    def normalize_incoming_number(self, number: str) -> str:
        """Normalize Twilio WhatsApp numbers into +<digits> format."""
        if not number:
            return ""
        number = number.strip()
        if number.startswith("whatsapp:"):
            number = number[len("whatsapp:") :]
        number = number.lstrip("+")
        digits = re.sub(r"\D", "", number)
        if not digits:
            return ""
        return f"+{digits}"

    def _strip_country_code_tail(self, number: str) -> str:
        digits = re.sub(r"\D", "", number or "")
        return digits[-10:] if len(digits) >= 10 else digits

    def find_guest_by_number(self, number: str) -> Optional[Guest]:
        digits = self._strip_country_code_tail(number)
        if not digits:
            return None
        return (
            Guest.objects.filter(
                Q(phone__icontains=digits) | Q(room_number__icontains=digits)
            )
            .order_by("-updated_at")
            .first()
        )

    def find_voucher_by_number(self, number: str) -> Optional[Voucher]:
        digits = self._strip_country_code_tail(number)
        if not digits:
            return None
        return (
            Voucher.objects.filter(phone_number__icontains=digits)
            .order_by("-created_at")
            .first()
        )

    def _attach_context_from_number(
        self, conversation: WhatsAppConversation, number: str
    ) -> Tuple[Optional[Guest], Optional[Voucher], str]:
        guest = conversation.guest or self.find_guest_by_number(number)
        voucher = conversation.voucher or self.find_voucher_by_number(number)

        if guest and conversation.guest_id != guest.pk:
            conversation.guest = guest
        if voucher and conversation.voucher_id != voucher.pk:
            conversation.voucher = voucher

        guest_status = WhatsAppConversation.GUEST_STATUS_UNKNOWN
        if guest:
            guest_status = guest.get_current_status()
        elif voucher:
            # Check voucher dates to determine status
            from datetime import datetime, time as time_cls
            reference_time = timezone.now()
            
            checkin_date = voucher.check_in_date
            checkout_date = voucher.check_out_date
            
            if checkin_date and checkout_date:
                checkin_dt = datetime.combine(checkin_date, time_cls(15, 0))
                if timezone.is_naive(checkin_dt):
                    checkin_dt = timezone.make_aware(checkin_dt, timezone.get_current_timezone())
                
                checkout_dt = datetime.combine(checkout_date, time_cls(11, 0))
                if timezone.is_naive(checkout_dt):
                    checkout_dt = timezone.make_aware(checkout_dt, timezone.get_current_timezone())
                
                if checkin_dt <= reference_time <= checkout_dt:
                    guest_status = WhatsAppConversation.GUEST_STATUS_CHECKED_IN
                elif reference_time < checkin_dt:
                    guest_status = WhatsAppConversation.GUEST_STATUS_PRE_CHECKIN
                elif reference_time > checkout_dt:
                    guest_status = WhatsAppConversation.GUEST_STATUS_CHECKED_OUT

        if conversation.last_known_guest_status != guest_status:
            conversation.last_known_guest_status = guest_status

        conversation.save(update_fields=["guest", "voucher", "last_known_guest_status", "updated_at"])
        return guest, voucher, guest_status

    def _log_inbound_message(
        self,
        conversation: WhatsAppConversation,
        body: str,
        payload: Dict[str, str],
    ) -> None:
        try:
            WhatsAppMessage.objects.create(
                conversation=conversation,
                guest=conversation.guest,
                direction=WhatsAppMessage.DIRECTION_INBOUND,
                body=body,
                payload=payload,
                sent_at=timezone.now(),
            )
        except Exception:
            logger.exception("Failed to log inbound WhatsApp message.")

    def _log_outbound_message(
        self,
        conversation: WhatsAppConversation,
        body: str,
        status: Optional[str] = None,
        message_sid: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        try:
            WhatsAppMessage.objects.create(
                conversation=conversation,
                guest=conversation.guest,
                direction=WhatsAppMessage.DIRECTION_OUTBOUND,
                body=body,
                status=status,
                message_sid=message_sid,
                error=error,
                sent_at=timezone.now(),
            )
        except Exception:
            logger.exception("Failed to log outbound WhatsApp message.")

    def _menu_message(self, guest_status: str):
        buttons = [
            {"id": "MENU_RAISE_REQUEST", "title": "Raise a Request", "payload": "1"},
            {"id": "MENU_CHECK_STATUS", "title": "Check Request Status", "payload": "2"},
        ]
        if guest_status == WhatsAppConversation.GUEST_STATUS_CHECKED_OUT:
            buttons.append(
                {"id": "MENU_FEEDBACK", "title": "Give Feedback", "payload": "3"}
            )

        button_titles = [button["title"] for button in buttons]
        if not button_titles:
            fallback = self.MENU_MESSAGE_PROMPT
        elif len(button_titles) == 1:
            fallback = f"{self.MENU_MESSAGE_PROMPT} {button_titles[0]}."
        elif len(button_titles) == 2:
            fallback = f"{self.MENU_MESSAGE_PROMPT} {button_titles[0]} or {button_titles[1]}."
        else:
            fallback = (
                f"{self.MENU_MESSAGE_PROMPT} "
                f"{', '.join(button_titles[:-1])}, or {button_titles[-1]}."
            )

        return {
            "type": "menu_buttons",
            "body": self.MENU_MESSAGE_PROMPT,
            "buttons": buttons,
            "fallback": fallback,
        }

    def _prepare_greeting(self, guest: Optional[Guest], voucher: Optional[Voucher], guest_status: str) -> List[str]:
        # Determine guest name from guest or voucher
        guest_name = "Guest"
        if guest and guest.full_name:
            guest_name = guest.full_name
        elif voucher and voucher.guest_name:
            guest_name = voucher.guest_name
        
        if not guest and not voucher:
            return [self.UNKNOWN_GUEST_MESSAGE]

        # Get hotel name from settings or use default
        from django.conf import settings
        hotel_name = getattr(settings, 'HOTEL_NAME', 'our hotel')
        
        # Check if guest has future booking or is not yet checked in
        has_future_booking = False
        if guest:
            current_status = guest.get_current_status()
            has_future_booking = current_status in ('pre_checkin', 'unknown')
        elif voucher:
            from datetime import datetime, time as time_cls
            reference_time = timezone.now()
            checkin_date = voucher.check_in_date
            if checkin_date:
                checkin_dt = datetime.combine(checkin_date, time_cls(15, 0))
                if timezone.is_naive(checkin_dt):
                    checkin_dt = timezone.make_aware(checkin_dt, timezone.get_current_timezone())
                has_future_booking = reference_time < checkin_dt
        
        if guest_status in (
            WhatsAppConversation.GUEST_STATUS_PRE_CHECKIN,
            WhatsAppConversation.GUEST_STATUS_UNKNOWN,
        ) or has_future_booking:
            greeting = (
                f"Hello {guest_name}, welcome to {hotel_name}! "
                "You can raise any service request directly through this chat."
            )
        elif guest_status == WhatsAppConversation.GUEST_STATUS_CHECKED_IN:
            greeting = (
                f"Hello {guest_name}, welcome to {hotel_name}! "
                "We're delighted to have you with us. You can raise service requests directly in this chat anytime."
            )
        else:  # checked out
            greeting = (
                f"Hello {guest_name}! We hope you enjoyed your stay. "
                "Feel free to raise any follow-up requests or share your feedback."
            )
        return [greeting]

    def _detect_request_type(self, message: str) -> Optional[DetectedRequest]:
        normalized = message.lower()
        tokens = set(re.findall(r"[a-zA-Z0-9']+", normalized))
        if not tokens:
            return None

        keyword_map: Dict[int, Tuple[int, List[str]]] = {}
        for keyword in RequestKeyword.objects.select_related("request_type").all():
            kw_lower = keyword.keyword.lower()
            matched = False
            if kw_lower in normalized:
                matched = True
            elif kw_lower in tokens:
                matched = True

            if not matched:
                continue

            current_score, matches = keyword_map.get(
                keyword.request_type_id, (0, [])
            )
            current_score += keyword.weight
            matches = matches + [kw_lower]
            keyword_map[keyword.request_type_id] = (current_score, matches)

        # Fallback: use RequestType name/description tokens when no explicit keywords matched
        if not keyword_map:
            for rt in RequestType.objects.filter(active=True).only("request_type_id", "name", "description", "default_department_id"):
                rt_id = rt.request_type_id
                score, matches = keyword_map.get(rt_id, (0, []))

                # Strong boost if full name appears in text
                rt_name_norm = (rt.name or "").strip().lower()
                if rt_name_norm and rt_name_norm in normalized:
                    score += 5
                    matches = matches + [rt_name_norm]

                # Token-level soft matches for name + description
                name_tokens = set(re.findall(r"[a-zA-Z0-9']+", rt.name.lower())) if rt.name else set()
                desc_tokens = set(re.findall(r"[a-zA-Z0-9']+", rt.description.lower())) if rt.description else set()
                potential_tokens = name_tokens.union(desc_tokens)

                token_hits = [t for t in potential_tokens if t and t in tokens]
                if token_hits:
                    score += len(token_hits)  # 1 point per token hit
                    matches = matches + token_hits

                if score > 0:
                    keyword_map[rt_id] = (score, matches)

        best_type_id = max(keyword_map, key=lambda key: keyword_map[key][0])
        score, matches = keyword_map[best_type_id]
        request_type = RequestType.objects.filter(pk=best_type_id).first()
        if not request_type:
            return None
        return DetectedRequest(request_type=request_type, matched_keywords=matches, score=score)

    def _create_service_request(
        self,
        conversation: WhatsAppConversation,
        detected: Optional[DetectedRequest],
        description: str,
    ) -> ServiceRequest:
        guest = conversation.guest
        department: Optional[Department] = None
        request_type: Optional[RequestType] = None

        if detected:
            request_type = detected.request_type
            department = request_type.default_department

        if not department and conversation.context.get("pending_department_id"):
            department = Department.objects.filter(
                pk=conversation.context["pending_department_id"]
            ).first()

        # Calculate SLA deadline if department has SLA settings
        due_at = None
        if department and hasattr(department, 'sla_response_time'):
            from datetime import timedelta
            due_at = timezone.now() + timedelta(minutes=department.sla_response_time or 60)

        service_request = ServiceRequest.objects.create(
            request_type=request_type,
            guest=guest,
            department=department,
            priority="normal",
            status="pending",
            source="whatsapp",
            notes=f"WhatsApp message:\n{description}",
            due_at=due_at,
        )
        return service_request

    def _create_unmatched_entry(
        self,
        conversation: WhatsAppConversation,
        body: str,
        detected: Optional[DetectedRequest] = None,
    ) -> UnmatchedRequest:
        keywords = []
        if detected:
            keywords = list(detected.matched_keywords)
        return UnmatchedRequest.objects.create(
            conversation=conversation,
            guest=conversation.guest,
            phone_number=conversation.phone_number,
            message_body=body,
            keywords=keywords,
            request_type=detected.request_type if detected else None,
            department=detected.request_type.default_department if detected and detected.request_type.default_department else None,
            context={"auto_detected": bool(detected)},
        )

    def _summarize_requests(self, guest: Optional[Guest]) -> List[str]:
        if not guest:
            return [
                "We could not find any active service requests for you. "
                "If this seems incorrect, please contact the reception."
            ]

        requests = (
            ServiceRequest.objects.filter(guest=guest)
            .order_by("-created_at")[:5]
        )
        if not requests:
            return ["You currently have no open requests."]

        lines = ["Here are your recent requests:"]
        for req in requests:
            status_display = req.get_status_display() if hasattr(req, "get_status_display") else req.status
            request_name = req.request_type.name if req.request_type else "General"
            lines.append(f"- {request_name}: {status_display}")
        return ["\n".join(lines)]

    def _get_active_feedback_session(
        self, conversation: WhatsAppConversation
    ) -> Optional[FeedbackSession]:
        session_id = conversation.context.get("feedback_session_id")
        if session_id:
            return FeedbackSession.objects.filter(pk=session_id).first()
        return (
            FeedbackSession.objects.filter(
                conversation=conversation, status__in=["pending", "active"]
            )
            .order_by("-created_at")
            .first()
        )

    def _start_feedback_session(
        self, conversation: WhatsAppConversation
    ) -> Tuple[Optional[FeedbackSession], List[str]]:
        questions = list(
            FeedbackQuestion.objects.filter(is_active=True).order_by("order", "id")
        )
        if not questions:
            conversation.current_state = WhatsAppConversation.STATE_IDLE
            conversation.save(update_fields=["current_state", "updated_at"])
            return None, ["Thank you! Currently there are no feedback questions available."]

        session = FeedbackSession.objects.create(
            conversation=conversation,
            guest=conversation.guest,
            booking=conversation.voucher.booking if conversation.voucher and conversation.voucher.booking_id else None,
            status=FeedbackSession.STATUS_ACTIVE,
            started_at=timezone.now(),
            current_question_index=0,
        )
        conversation.current_state = WhatsAppConversation.STATE_COLLECTING_FEEDBACK
        conversation.context = {
            **conversation.context,
            "feedback_session_id": session.pk,
            "feedback_question_count": len(questions),
        }
        conversation.save(update_fields=["current_state", "context", "updated_at"])

        prompt = questions[0].prompt
        return session, [prompt]

    def _progress_feedback(
        self,
        conversation: WhatsAppConversation,
        incoming_text: str,
    ) -> List[str]:
        session = self._get_active_feedback_session(conversation)
        if not session:
            conversation.current_state = WhatsAppConversation.STATE_IDLE
            conversation.save(update_fields=["current_state", "updated_at"])
            return ["Feedback session not found. Please type 'Hi' to start over."]

        questions = list(
            FeedbackQuestion.objects.filter(is_active=True).order_by("order", "id")
        )
        if not questions:
            session.status = FeedbackSession.STATUS_COMPLETED
            session.completed_at = timezone.now()
            session.save(update_fields=["status", "completed_at"])
            conversation.current_state = WhatsAppConversation.STATE_IDLE
            conversation.context.pop("feedback_session_id", None)
            conversation.save(update_fields=["current_state", "context", "updated_at"])
            
            # Get guest name for thank you message
            guest_name = "Guest"
            if conversation.guest and conversation.guest.full_name:
                guest_name = conversation.guest.full_name
            elif conversation.voucher and conversation.voucher.guest_name:
                guest_name = conversation.voucher.guest_name
            
            return [self.FEEDBACK_THANK_YOU_BASE.format(guest_name=guest_name)]

        if session.current_question_index >= len(questions):
            session.status = FeedbackSession.STATUS_COMPLETED
            session.completed_at = timezone.now()
            session.save(update_fields=["status", "completed_at"])
            conversation.current_state = WhatsAppConversation.STATE_IDLE
            conversation.context.pop("feedback_session_id", None)
            conversation.save(update_fields=["current_state", "context", "updated_at"])
            
            # Get guest name for thank you message
            guest_name = "Guest"
            if conversation.guest and conversation.guest.full_name:
                guest_name = conversation.guest.full_name
            elif conversation.voucher and conversation.voucher.guest_name:
                guest_name = conversation.voucher.guest_name
            
            return [self.FEEDBACK_THANK_YOU_BASE.format(guest_name=guest_name)]

        question = questions[session.current_question_index]
        FeedbackResponse.objects.update_or_create(
            session=session,
            question=question,
            defaults={
                "answer": incoming_text.strip(),
                "received_at": timezone.now(),
            },
        )

        session.current_question_index += 1
        session.save(update_fields=["current_question_index", "updated_at"])

        if session.current_question_index >= len(questions):
            session.status = FeedbackSession.STATUS_COMPLETED
            session.completed_at = timezone.now()
            session.save(update_fields=["status", "completed_at"])
            conversation.current_state = WhatsAppConversation.STATE_IDLE
            conversation.context.pop("feedback_session_id", None)
            conversation.save(update_fields=["current_state", "context", "updated_at"])
            
            # Get guest name for thank you message
            guest_name = "Guest"
            if conversation.guest and conversation.guest.full_name:
                guest_name = conversation.guest.full_name
            elif conversation.voucher and conversation.voucher.guest_name:
                guest_name = conversation.voucher.guest_name
            
            return [self.FEEDBACK_THANK_YOU_BASE.format(guest_name=guest_name)]

        next_question = questions[session.current_question_index].prompt
        return [next_question]

    def handle_incoming_message(self, payload: Dict[str, str]) -> Tuple[List[str], WhatsAppConversation]:
        """
        Main entry point for webhook requests.

        Returns a tuple of (messages_to_reply, conversation_instance).
        """
        body = (payload.get("Body") or "").strip()
        button_payload = (
            payload.get("ButtonPayload")
            or payload.get("button_payload")
            or payload.get("payload")
        )
        button_text = payload.get("ButtonText") or payload.get("button_text")
        interactive_payload = payload.get("interactive")
        if isinstance(interactive_payload, dict):
            if interactive_payload.get("type") == "button_reply":
                reply = interactive_payload.get("button_reply") or {}
                button_payload = reply.get("id") or reply.get("payload") or button_payload
                button_text = reply.get("title") or button_text
            elif interactive_payload.get("type") == "list_reply":
                reply = interactive_payload.get("list_reply") or {}
                button_payload = reply.get("id") or button_payload
                button_text = reply.get("title") or button_text

        if not body and button_text:
            body = button_text.strip()

        from_number = payload.get("From") or payload.get("WaId") or ""
        normalized_number = self.normalize_incoming_number(from_number)

        if not normalized_number:
            logger.warning("Received WhatsApp message without valid phone number.")
            return ([self.UNKNOWN_GUEST_MESSAGE], None)

        conversation, _ = WhatsAppConversation.objects.get_or_create(
            phone_number=normalized_number
        )
        conversation.context = conversation.context or {}

        guest, voucher, guest_status = self._attach_context_from_number(
            conversation, normalized_number
        )

        conversation.last_guest_message_at = timezone.now()
        conversation.save(update_fields=["last_guest_message_at", "updated_at"])

        self._log_inbound_message(conversation, body, payload)

        if not body:
            return ([self.EMPTY_MESSAGE_PROMPT, self._menu_message(guest_status)], conversation)

        composite_input = button_payload or button_text or body
        lower_body = str(composite_input or "").strip().lower()
        button_aliases = {
            "raise a request": "1",
            "raise request": "1",
            "menu_raise_request": "1",
            "check request status": "2",
            "check status": "2",
            "menu_check_status": "2",
            "give feedback": "3",
            "menu_feedback": "3",
        }
        lower_body = button_aliases.get(lower_body, lower_body)

        messages: List[str] = []

        # Feedback flow
        if conversation.current_state == WhatsAppConversation.STATE_COLLECTING_FEEDBACK:
            messages.extend(self._progress_feedback(conversation, body))
            return messages, conversation

        if conversation.current_state == WhatsAppConversation.STATE_FEEDBACK_INVITED:
            if lower_body in AFFIRMATIVE_KEYWORDS:
                session, prompts = self._start_feedback_session(conversation)
                if prompts:
                    messages.extend(prompts)
            elif lower_body in NEGATIVE_KEYWORDS:
                conversation.current_state = WhatsAppConversation.STATE_IDLE
                conversation.save(update_fields=["current_state", "updated_at"])
                messages.append("No worries! If you change your mind, just type 'Hi' to begin.")
            else:
                messages.append("Please reply 'Yes' if you would like to share feedback, or 'No' to skip.")
            return messages, conversation

        is_greeting = lower_body in GREETING_KEYWORDS
        if (
            is_greeting
            or conversation.current_state == WhatsAppConversation.STATE_IDLE
            and not conversation.menu_presented_at
        ):
            greeting_messages = self._prepare_greeting(guest, voucher, guest_status)
            messages.extend(greeting_messages)

            if guest or voucher:
                conversation.current_state = WhatsAppConversation.STATE_AWAITING_MENU
                conversation.menu_presented_at = timezone.now()
                conversation.welcome_sent_at = conversation.welcome_sent_at or timezone.now()
                conversation.save(
                    update_fields=["current_state", "menu_presented_at", "welcome_sent_at", "updated_at"]
                )
                messages.append(self._menu_message(guest_status))

                # If the user's initial message already contains recognizable keywords,
                # create a matched review entry so it appears pre-filled in the dashboard.
                try:
                    detected_pre = self._detect_request_type(body)
                    if detected_pre:
                        self._create_unmatched_entry(conversation, body, detected_pre)
                except Exception:
                    pass
            else:
                # Unknown guest/voucher; still attempt to detect and persist matched request type
                detected = self._detect_request_type(body)
                self._create_unmatched_entry(conversation, body, detected)
                conversation.current_state = WhatsAppConversation.STATE_IDLE
                conversation.save(update_fields=["current_state", "updated_at"])
            return messages, conversation

        if conversation.current_state == WhatsAppConversation.STATE_AWAITING_MENU:
            if lower_body == "1":
                conversation.current_state = WhatsAppConversation.STATE_AWAITING_DESCRIPTION
                conversation.context["pending_request_started_at"] = timezone.now().isoformat()
                conversation.save(update_fields=["current_state", "context", "updated_at"])
                messages.append(self.REQUEST_PROMPT_MESSAGE)
                return messages, conversation

            if lower_body == "2":
                messages.extend(self._summarize_requests(guest))
                conversation.current_state = WhatsAppConversation.STATE_AWAITING_MENU
                conversation.save(update_fields=["current_state", "updated_at"])
                messages.append(self._menu_message(guest_status))
                return messages, conversation

            if lower_body == "3" and guest_status == WhatsAppConversation.GUEST_STATUS_CHECKED_OUT:
                conversation.current_state = WhatsAppConversation.STATE_FEEDBACK_INVITED
                conversation.save(update_fields=["current_state", "updated_at"])
                messages.append("We would love to hear about your stay. Reply 'Yes' to begin or 'No' to skip.")
                return messages, conversation

            # If the message doesn't match a menu option, try to detect request intent
            detected_mid = self._detect_request_type(body)
            if detected_mid:
                # Create a matched review entry and acknowledge
                self._create_unmatched_entry(conversation, body, detected_mid)
                messages.append(self.UNMATCHED_CONFIRMATION)
                conversation.current_state = WhatsAppConversation.STATE_IDLE
                conversation.save(update_fields=["current_state", "updated_at"])
                return messages, conversation

            messages.append(self.INVALID_OPTION_MESSAGE)
            messages.append(self._menu_message(guest_status))
            return messages, conversation

        if conversation.current_state == WhatsAppConversation.STATE_AWAITING_DESCRIPTION:
            if len(body) < 3:
                messages.append("Could you share a bit more detail so we can assist you better?")
                return messages, conversation

            detected = self._detect_request_type(body)

            with transaction.atomic():
                # Do not create a ticket directly. Always create a review entry.
                # If matched, assign the request type and its default department.
                self._create_unmatched_entry(conversation, body, detected)
                messages.append(self.UNMATCHED_CONFIRMATION)

            conversation.current_state = WhatsAppConversation.STATE_IDLE
            conversation.context.pop("pending_request_started_at", None)
            conversation.menu_presented_at = None
            conversation.save(
                update_fields=["current_state", "context", "menu_presented_at", "updated_at"]
            )
            return messages, conversation

        messages.append(self._menu_message(guest_status))
        return messages, conversation

    def send_outbound_messages(
        self,
        conversation: WhatsAppConversation,
        messages: Iterable[str],
    ) -> None:
        for outgoing in messages:
            body_to_log = outgoing
            status = None
            sid = None
            error = None
            result = None
            try:
                if isinstance(outgoing, dict):
                    if outgoing.get("type") == "menu_buttons":
                        body_text = outgoing.get("body") or "Please choose an option:"
                        buttons = outgoing.get("buttons") or []
                        fallback_text = outgoing.get("fallback") or self.MENU_MESSAGE_PROMPT
                        result = twilio_service.send_button_message(
                            conversation.phone_number,
                            body_text,
                            buttons,
                            fallback_text=fallback_text,
                        )
                        if not result or not result.get("success", False):
                            result = twilio_service.send_text_message(
                                conversation.phone_number, fallback_text
                            )
                            body_to_log = fallback_text
                        else:
                            body_to_log = f"{body_text} [buttons]"
                    else:
                        payload_text = (
                            outgoing.get("body")
                            or outgoing.get("text")
                            or self.MENU_MESSAGE_PROMPT
                        )
                        result = twilio_service.send_text_message(
                            conversation.phone_number, payload_text
                        )
                        body_to_log = payload_text
                else:
                    result = twilio_service.send_text_message(
                        conversation.phone_number, outgoing
                    )
                    body_to_log = outgoing

                status = result.get("status") if isinstance(result, dict) else None
                sid = result.get("message_id") if isinstance(result, dict) else None
                error = result.get("error") if isinstance(result, dict) else None
                if not result or not result.get("success", True):
                    logger.warning(
                        "Failed to send WhatsApp message to %s: %s",
                        conversation.phone_number,
                        error,
                    )
                self._log_outbound_message(
                    conversation,
                    str(body_to_log),
                    status=status,
                    message_sid=sid,
                    error=error,
                )
            except Exception as exc:
                logger.exception("Twilio send_text_message failed.")
                self._log_outbound_message(
                    conversation,
                    str(body_to_log),
                    status="failed",
                    error=str(exc),
                )

        conversation.last_system_message_at = timezone.now()
        conversation.save(update_fields=["last_system_message_at", "updated_at"])

    def send_welcome_for_checkin(self, guest: Guest) -> None:
        """Send welcome message when guest checks in."""
        if not guest.phone:
            return
        phone = self.normalize_incoming_number(guest.phone)
        if not phone:
            return

        conversation, _ = WhatsAppConversation.objects.get_or_create(phone_number=phone)
        conversation.guest = guest
        conversation.last_known_guest_status = WhatsAppConversation.GUEST_STATUS_CHECKED_IN
        conversation.welcome_sent_at = timezone.now()
        conversation.current_state = WhatsAppConversation.STATE_AWAITING_MENU
        conversation.save(update_fields=["guest", "last_known_guest_status", "welcome_sent_at", "current_state", "updated_at"])

        guest_name = guest.full_name or "Guest"
        from django.conf import settings
        hotel_name = getattr(settings, 'HOTEL_NAME', 'our hotel')
        
        messages = [
            f"Welcome {guest_name}! We're delighted to have you with us. You can raise service requests directly in this chat anytime."
        ]
        messages.append(self._menu_message(WhatsAppConversation.GUEST_STATUS_CHECKED_IN))
        self.send_outbound_messages(conversation, messages)

    def send_checkout_feedback_invite(self, guest: Guest) -> None:
        """Send checkout message and feedback invitation when guest checks out."""
        if not guest.phone:
            return

        phone = self.normalize_incoming_number(guest.phone)
        if not phone:
            return

        conversation, _ = WhatsAppConversation.objects.get_or_create(phone_number=phone)
        conversation.guest = guest
        conversation.last_known_guest_status = WhatsAppConversation.GUEST_STATUS_CHECKED_OUT
        conversation.current_state = WhatsAppConversation.STATE_FEEDBACK_INVITED
        conversation.feedback_prompt_sent_at = timezone.now()
        conversation.save(update_fields=[
            "guest",
            "last_known_guest_status",
            "current_state",
            "feedback_prompt_sent_at",
            "updated_at",
        ])

        guest_name = guest.full_name or "Guest"
        messages = [
            f"Thank you for staying with us, {guest_name}! We hope you had a pleasant stay.",
            "Would you like to share your feedback about your stay? Please reply 'Yes' to begin.",
        ]
        self.send_outbound_messages(conversation, messages)


workflow_handler = WhatsAppWorkflow()

    