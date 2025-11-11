from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from twilio.twiml.messaging_response import MessagingResponse

from .whatsapp_workflow import workflow_handler


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    Twilio WhatsApp webhook endpoint.

    Twilio sends POST requests containing form-encoded data. We process the
    message via the WhatsApp workflow handler and respond with TwiML to deliver
    replies back to the guest.
    """
    if request.method == "GET":
        # Health-check endpoint for debugging
        return JsonResponse({"status": "ok"})

    payload = request.POST.dict()
    messages, conversation = workflow_handler.handle_incoming_message(payload)

    response = MessagingResponse()
    for message in messages:
        response.message(message)

    xml = str(response)
    return HttpResponse(xml, content_type="application/xml")

