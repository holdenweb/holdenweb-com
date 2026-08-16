"""Ask the mail server whether it accepts our credentials, and nothing else.

Written after an afternoon spent deciding whether a rejected Gmail App
Password was the password, the username, the wrong file, or the site -- a
question a password-reset round trip answers slowly and ambiguously, because
a failure there could be any of the above. This opens the SMTP connection,
authenticates, and stops.

It reports what the connection *would* use as well as the outcome, since a
correct password authenticating as the wrong account fails identically to a
wrong password. The password itself is never printed: only its length and
whether it has the shape of a Google App Password, which is sixteen lowercase
letters with the spaces of Google's four-by-four display removed.

Run it against a container -- `scripts/` is not copied into the image, so pipe
it in rather than expecting it to be there:

    podman exec -i holdenweb-com-web-1 python - < scripts/smtpcheck.py

or on the host, against whatever the local environment names:

    uv run python scripts/smtpcheck.py

Exit status is 0 if authentication succeeded and 1 if it did not, so it can
gate a deployment step.
"""

import sys

import holdenweb


def describe_credentials(config) -> None:
    """Report the shape of what we are about to authenticate with."""
    print(f"  server    : {config.get('MAIL_SERVER')}:{config.get('MAIL_PORT')}"
          f"  SSL={config.get('MAIL_USE_SSL')}  TLS={config.get('MAIL_USE_TLS')}")
    print(f"  username  : {config.get('MAIL_USERNAME')}")

    password = config.get("MAIL_PASSWORD") or ""
    if not password:
        print("  password  : NOT SET")
        return
    stripped = password.replace(" ", "")
    looks_right = len(stripped) == 16 and stripped.isalpha() and stripped.islower()
    print(f"  password  : {len(password)} characters"
          f"{' (spaces present)' if ' ' in password else ''}")
    if looks_right:
        print("              shape matches a Google App Password")
    else:
        # The failure that cost the most time: a perfectly good password from
        # the wrong page of Google's security site. App Passwords live under
        # 2-Step Verification; passwords.google.com holds saved site logins.
        print("              NOT the shape of a Google App Password, which is"
              " 16 lowercase letters")


def main() -> int:
    app = holdenweb.create_app()
    print("mail configuration:")
    describe_credentials(app.config)

    with app.app_context():
        connection = app.extensions["mailman"].get_connection()
        try:
            connection.open()
        except Exception as exc:
            print(f"\nSMTP auth FAILED: {type(exc).__name__}")
            print(f"  {exc}")
            return 1
        connection.close()

    print("\nSMTP auth OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
