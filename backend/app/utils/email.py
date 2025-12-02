"""
Email utility for sending emails via AWS SES
"""

import boto3
import logging
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """AWS SES Email Service"""

    def __init__(self):
        self.client = boto3.client(
            'ses',
            region_name=settings.AWS_REGION
        )
        self.sender_email = settings.SES_SENDER_EMAIL

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email with reset link

        Args:
            to_email: Recipient email address
            reset_token: Password reset token

        Returns:
            True if email sent successfully, False otherwise
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        subject = "[Legal Evidence Hub] 비밀번호 재설정"
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h2>비밀번호 재설정 요청</h2>
            <p>안녕하세요,</p>
            <p>Legal Evidence Hub 계정의 비밀번호 재설정이 요청되었습니다.</p>
            <p>아래 버튼을 클릭하여 새 비밀번호를 설정해주세요:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color: #1e40af; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; font-weight: bold;">
                    비밀번호 재설정
                </a>
            </p>
            <p>또는 아래 링크를 브라우저에 복사하여 붙여넣으세요:</p>
            <p style="color: #666; word-break: break-all;">{reset_url}</p>
            <p style="margin-top: 30px; color: #999; font-size: 12px;">
                이 링크는 1시간 후에 만료됩니다.<br>
                본인이 요청하지 않으셨다면 이 이메일을 무시해주세요.
            </p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 11px;">
                Legal Evidence Hub - AI 기반 법률 증거 관리 시스템
            </p>
        </body>
        </html>
        """

        body_text = f"""
비밀번호 재설정 요청

안녕하세요,

Legal Evidence Hub 계정의 비밀번호 재설정이 요청되었습니다.

아래 링크를 클릭하여 새 비밀번호를 설정해주세요:
{reset_url}

이 링크는 1시간 후에 만료됩니다.
본인이 요청하지 않으셨다면 이 이메일을 무시해주세요.

Legal Evidence Hub - AI 기반 법률 증거 관리 시스템
        """

        return self._send_email(to_email, subject, body_html, body_text)

    def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str
    ) -> bool:
        """
        Send email via AWS SES

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sender_email:
            logger.error("SES_SENDER_EMAIL not configured")
            return False

        try:
            response = self.client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body_text,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            logger.info(f"Email sent to {to_email}, MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send email: {error_code} - {error_message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False


# Global instance
email_service = EmailService()
