import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.mrb.common.config import EmailConfiguration


class EmailService:
    def __init__(self):
        self.smtp_server = EmailConfiguration.SMTP_SERVER
        self.smtp_port = EmailConfiguration.SMTP_PORT
        self.enviado = False
        self.mensagem = ""

    def send_email(self, to_address, subject, body) -> bool:
        try:
            self.enviado = True
            msg = MIMEMultipart()
            msg["From"] = EmailConfiguration.ADDRESS
            msg["To"] = to_address
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html"))

            if EmailConfiguration.SMTP_AUDITORIA:
                msg["Bcc"] = EmailConfiguration.SMTP_AUDITORIA
                to_address += ";" + EmailConfiguration.SMTP_AUDITORIA

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if EmailConfiguration.SMTP_AUTENTICACAO:
                    server.starttls()
                    server.login(
                        EmailConfiguration.ADDRESS, EmailConfiguration.PASSWORD
                    )
                server.sendmail(EmailConfiguration.ADDRESS, to_address, msg.as_string())

            self.mensagem = "Email enviado com sucesso!"
        except Exception as e:
            self.enviado = False
            self.mensagem = f"Falha ao enviar email: {e}"
            print(self.mensagem)

        return self.enviado
