import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

from .forms import ContactForm


def index(request):
    return render(request, 'core/index.html', {
        'contact_form':  ContactForm(),
        'contact_email': settings.EMAIL_HOST_USER,
    })


@require_POST
def contact_submit(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        contact = form.save()  # always stored in DB (visible in admin, even if email fails)
        _email_contact(contact)
        messages.success(request, _("Contact success msg"))
    else:
        messages.error(request, _("Contact error msg"))

    return redirect(reverse('core:index') + '#contact')


def _email_contact(contact):
    """Email a contact submission to CONTACT_RECIPIENT_EMAIL. Never breaks the request."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.warning("Contact email skipped: SMTP not configured (EMAIL_HOST_USER/PASSWORD empty). "
                       "Message #%s saved in DB only.", contact.pk)
        return
    try:
        msg = EmailMessage(
            subject=f"[Nihol AI] Yangi xabar: {contact.subject or 'Mavzusiz'}",
            body=(
                f"Ism: {contact.name}\n"
                f"Email: {contact.email}\n"
                f"Mavzu: {contact.subject or '—'}\n\n"
                f"Xabar:\n{contact.message}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_RECIPIENT_EMAIL],
            reply_to=[contact.email],  # reply goes straight to the sender
        )
        msg.send(fail_silently=False)
    except Exception:
        logger.exception("Contact email failed for message #%s (saved in DB).", contact.pk)
