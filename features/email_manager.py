import smtplib
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Dict, Optional, Tuple
import time
import re
from datetime import datetime

class EmailManager:
    def __init__(self):
        # Default email configuration
        self.email_address = os.getenv("EMAIL_ADDRESS", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")  # App password for Gmail
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        
        # Track connections
        self.smtp_connection = None
        self.imap_connection = None
        
    def connect_smtp(self) -> bool:
        """Connect to SMTP server for sending emails."""
        try:
            # Close any existing connection
            if self.smtp_connection:
                try:
                    self.smtp_connection.quit()
                except:
                    pass
                
            # Create new connection
            self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp_connection.ehlo()
            self.smtp_connection.starttls()
            self.smtp_connection.login(self.email_address, self.email_password)
            return True
        except Exception as e:
            print(f"SMTP Connection Error: {e}")
            return False
            
    def connect_imap(self) -> bool:
        """Connect to IMAP server for reading emails."""
        try:
            # Close any existing connection
            if self.imap_connection:
                try:
                    self.imap_connection.logout()
                except:
                    pass
                    
            # Create new connection
            self.imap_connection = imaplib.IMAP4_SSL(self.imap_server)
            self.imap_connection.login(self.email_address, self.email_password)
            return True
        except Exception as e:
            print(f"IMAP Connection Error: {e}")
            return False
            
    def send_email(self, to_address: str, subject: str, body: str, 
                   attachments: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Send an email with optional attachments."""
        if not self.email_address or not self.email_password:
            return False, "Email credentials not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables."
            
        try:
            # Connect to SMTP server if not already connected
            if not self.smtp_connection:
                if not self.connect_smtp():
                    return False, "Failed to connect to SMTP server."
                    
            # Create message
            message = MIMEMultipart()
            message['From'] = self.email_address
            message['To'] = to_address
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachments if any
            if attachments:
                for attachment_path in attachments:
                    try:
                        # Check if file exists
                        if not os.path.isfile(attachment_path):
                            continue
                            
                        # Attach file
                        with open(attachment_path, "rb") as file:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(attachment_path)
                            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            message.attach(part)
                    except Exception as e:
                        print(f"Error attaching file {attachment_path}: {e}")
            
            # Send email
            self.smtp_connection.send_message(message)
            return True, "Email sent successfully!"
        except Exception as e:
            print(f"Send Email Error: {e}")
            # Try to reconnect and send again
            try:
                if self.connect_smtp():
                    self.smtp_connection.send_message(message)
                    return True, "Email sent successfully after reconnection!"
            except Exception as reconnect_error:
                print(f"Reconnection Error: {reconnect_error}")
            
            return False, f"Failed to send email: {str(e)}"
            
    def get_unread_emails(self, limit: int = 5) -> List[Dict]:
        """Get unread emails from the inbox."""
        if not self.email_address or not self.email_password:
            print("Email credentials not configured.")
            return []
            
        try:
            # Connect to IMAP server if not already connected
            if not self.imap_connection:
                if not self.connect_imap():
                    return []
                    
            # Select inbox
            self.imap_connection.select('INBOX')
            
            # Search for unread emails
            status, messages = self.imap_connection.search(None, 'UNSEEN')
            if status != 'OK':
                return []
                
            email_ids = messages[0].split()
            # Limit the number of emails to fetch
            if limit > 0:
                email_ids = email_ids[-limit:]
                
            emails = []
            for email_id in reversed(email_ids):  # Latest first
                status, data = self.imap_connection.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                    
                raw_email = data[0][1]
                parsed_email = email.message_from_bytes(raw_email)
                
                # Get basic info
                from_address = self._parse_email_field(parsed_email['From'])
                subject = self._parse_email_field(parsed_email['Subject'])
                date = self._parse_email_field(parsed_email['Date'])
                
                # Get body
                body = self._get_email_body(parsed_email)
                
                emails.append({
                    'id': email_id.decode(),
                    'from': from_address,
                    'subject': subject,
                    'date': date,
                    'body': body
                })
                
            return emails
        except Exception as e:
            print(f"Get Unread Emails Error: {e}")
            return []
            
    def _parse_email_field(self, field: Optional[str]) -> str:
        """Parse and clean an email header field."""
        if not field:
            return ""
            
        # Handle encoding
        decoded = email.header.decode_header(field)
        value = ""
        for part, encoding in decoded:
            if isinstance(part, bytes):
                if encoding:
                    value += part.decode(encoding)
                else:
                    value += part.decode('utf-8', errors='replace')
            else:
                value += part
                
        return value
            
    def _get_email_body(self, msg) -> str:
        """Extract body from an email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                # Return plain text content
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        return body
                    except:
                        pass
                        
            # If no plain text found, try to extract HTML content
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" not in content_disposition and content_type == "text/html":
                    try:
                        html = part.get_payload(decode=True).decode()
                        # Very simple HTML to text conversion
                        body = re.sub('<[^<]+?>', '', html)
                        return body
                    except:
                        pass
        else:
            # Not multipart - get payload directly
            try:
                body = msg.get_payload(decode=True).decode()
                return body
            except:
                pass
                
        return "Unable to extract email content"
        
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        try:
            if not self.imap_connection:
                if not self.connect_imap():
                    return False
                    
            self.imap_connection.select('INBOX')
            self.imap_connection.store(email_id.encode(), '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            print(f"Mark As Read Error: {e}")
            return False
            
    def search_emails(self, query: str, limit: int = 5) -> List[Dict]:
        """Search emails based on a query."""
        if not self.email_address or not self.email_password:
            print("Email credentials not configured.")
            return []
            
        try:
            if not self.imap_connection:
                if not self.connect_imap():
                    return []
                    
            self.imap_connection.select('INBOX')
            
            # Convert natural language query to IMAP search criteria
            search_criteria = self._convert_query_to_criteria(query)
            status, messages = self.imap_connection.search(None, search_criteria)
            
            if status != 'OK':
                return []
                
            email_ids = messages[0].split()
            # Limit results
            if limit > 0 and len(email_ids) > limit:
                email_ids = email_ids[-limit:]
                
            emails = []
            for email_id in reversed(email_ids):  # Latest first
                status, data = self.imap_connection.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                    
                raw_email = data[0][1]
                parsed_email = email.message_from_bytes(raw_email)
                
                # Get basic info
                from_address = self._parse_email_field(parsed_email['From'])
                subject = self._parse_email_field(parsed_email['Subject'])
                date = self._parse_email_field(parsed_email['Date'])
                
                # Get body
                body = self._get_email_body(parsed_email)
                
                emails.append({
                    'id': email_id.decode(),
                    'from': from_address,
                    'subject': subject,
                    'date': date,
                    'body': body[:300] + ('...' if len(body) > 300 else '')  # Truncate long bodies
                })
                
            return emails
        except Exception as e:
            print(f"Search Emails Error: {e}")
            return []
            
    def _convert_query_to_criteria(self, query: str) -> str:
        """Convert a natural language query to IMAP search criteria."""
        query = query.lower()
        
        # Default to all emails
        if not query:
            return 'ALL'
            
        # Check for common search patterns
        if 'unread' in query or 'unseen' in query:
            return 'UNSEEN'
            
        if 'today' in query:
            today = datetime.now().strftime("%d-%b-%Y")
            return f'(ON {today})'
            
        if 'yesterday' in query:
            # Simple approximation - not exactly accurate
            return 'NEWER 2'
            
        # Check for from/sender
        from_match = re.search(r'from\s+([^\s]+)', query)
        if from_match:
            sender = from_match.group(1)
            return f'(FROM "{sender}")'
            
        # Check for subject
        subject_match = re.search(r'subject\s+([^\s]+)', query)
        if subject_match:
            subject = subject_match.group(1)
            return f'(SUBJECT "{subject}")'
            
        # Default to searching in the subject
        return f'(SUBJECT "{query}")'
        
    def close_connections(self):
        """Close all email connections."""
        try:
            if self.smtp_connection:
                self.smtp_connection.quit()
        except:
            pass
            
        try:
            if self.imap_connection:
                self.imap_connection.logout()
        except:
            pass
            
        self.smtp_connection = None
        self.imap_connection = None 