import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


def send_email(receiver_email):

    sender = "netapp-automation@chevron.com"

    smtp_server = "smtp.chevron.com"
    smtp_port = 25

    msg = MIMEMultipart()

    msg["From"] = sender
    msg["To"] = receiver_email
    msg["Subject"] = "NetApp Command Report"

    files = [
        "reports/output.xlsx",
        "reports/output.html"
    ]

    for file in files:
        with open(file, "rb") as f:
            part = MIMEApplication(
                f.read(),
                Name=file
            )
            part['Content-Disposition'] = f'attachment; filename="{file}"'
            msg.attach(part)

    server = smtplib.SMTP(
        smtp_server,
        smtp_port
    )

    server.sendmail(
        sender,
        receiver_email,
        msg.as_string()
    )

    server.quit()