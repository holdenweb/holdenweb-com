"""Mail delivery that reports a failure instead of becoming one.

flask-security calls `send_mail` from inside its own views and catches nothing
the mail backend raises. `forgot_password` is the one that matters: an expired
SMTP credential turned "reset my password" into a 500 with a traceback, which
told the visitor nothing they could act on and the operator nothing the log
would not have said better.

Named for flask-security's own `mail_util` module, and wired the way its
documentation says to -- `mail_util_cls` at init -- rather than by wrapping the
view or catching SMTPException in an error handler. The extension point exists;
a site that needs it should use it.
"""

from flask import current_app, flash, has_request_context
from flask_security import MailUtil


class ReportingMailUtil(MailUtil):
    """Log a delivery failure, tell the visitor, and let the request finish."""

    def send_mail(  # type: ignore[no-untyped-def]
        self, template, subject, recipient, sender, body, html, **kwargs
    ):
        try:
            super().send_mail(template, subject, recipient, sender, body, html, **kwargs)
        except Exception as exc:  # noqa: BLE001
            # Every mail backend raises its own family -- smtplib, ssl and
            # socket at least -- and the useful distinction here is not which
            # one but that the message did not go. The type is in the log.
            current_app.logger.error(
                "could not send the %r email to %s: %s: %s",
                template,
                recipient,
                type(exc).__name__,
                exc,
            )
            _tell_the_visitor()


def _tell_the_visitor() -> None:
    """Say the mail failed, when saying so gives nothing away.

    flask-security flashes its own cheerful "instructions have been sent"
    immediately after this returns, and leaving that as the only message means
    somebody waits for an email that was never going to arrive.

    Held back when the site has asked for generic responses. `send_mail` is
    only reached for an address that *does* have an account, so under
    `SECURITY_RETURN_GENERIC_RESPONSES` the mere presence of this message would
    distinguish a registered address from an unregistered one -- which is the
    single thing that setting exists to prevent. This site has it off, so the
    form already answers that question outright and there is nothing left to
    protect; the guard is here so that turning it on does not quietly reopen
    the hole.
    """
    if not has_request_context():
        return
    if current_app.config.get("SECURITY_RETURN_GENERIC_RESPONSES"):
        return
    flash(
        "That email could not be sent just now -- a problem at our end, not "
        "with your account. Please try again shortly.",
        "error",
    )
