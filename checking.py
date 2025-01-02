import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json
import os


# Load configuration from JSON file
def load_config(file_path):
    with open(file_path, 'r') as config_file:
        return json.load(config_file)


# Email sending functionality
def send_email(smtp_host, smtp_port, smtp_user, smtp_password, from_email, subject, message, to, attachments=[]):
    try:
        with smtplib.SMTP(host=smtp_host, port=smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            for file in attachments:
                try:
                    with open(file, 'rb') as file_in:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file_in.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file)}")
                        msg.attach(part)
                except FileNotFoundError:
                    print(f"Warning: File {file} not found. Skipping attachment.")

            server.send_message(msg)
            print(f"Email sent to {to} with subject: {subject}")
    except Exception as e:
        print(f"Error sending email: {e}")


# Execute dead man's switch emails
def execute_deadman_switch(counter_file, count_sent_mail, dead_man_subject, dead_man_message, family_members, attachments, config):
    try:
        counter = 0
        if os.path.exists(counter_file):
            with open(counter_file, "r") as file:
                counter = int(file.read())
    except ValueError:
        print("Counter file is corrupted. Resetting counter to 0.")

    if counter < count_sent_mail:
        send_email(
            config['smtp_host'], config['smtp_port'], config['smtp_user'], config['smtp_password'],
            config['from_email'], dead_man_subject, dead_man_message,
            ', '.join(family_members), attachments
        )
        with open(counter_file, "w") as file:
            file.write(str(counter + 1))
    else:
        print("All dead man's switch emails have been sent.")


# Check if the dead man's switch needs to be activated
def check_deadman(config):
    try:
        with open(config['checkin_file'], "r") as file:
            last_checkin_time = float(file.read().strip())
    except FileNotFoundError:
        print("Check-in file not found. Assuming no check-in has been recorded.")
        last_checkin_time = 0

    time_difference = time.time() - last_checkin_time
    if time_difference > config['DAYS_REMINDER'] * config['SECONDS_IN_A_DAY']:
        if time_difference > config['DAYS_DEADMAN'] * config['SECONDS_IN_A_DAY']:
            send_email(
                config['smtp_host'], config['smtp_port'], config['smtp_user'], config['smtp_password'],
                config['from_email'], config['dead_man_activation_subject'], config['dead_man_activation_message'],
                config['to_email']
            )
            execute_deadman_switch(
                config['counter_file'], config['count_sent_mail'], config['dead_man_subject'], config['dead_man_message'],
                config['family_members'], config['files_to_attach'], config
            )
        else:
            send_email(
                config['smtp_host'], config['smtp_port'], config['smtp_user'], config['smtp_password'],
                config['from_email'], config['reminder_subject'], config['reminder_message'],
                config['to_email']
            )
    else:
        print("No action required. Last check-in is within the safe time frame.")


if __name__ == '__main__':
    try:
        CONFIG_FILE_PATH = 'config.json'
        config = load_config(CONFIG_FILE_PATH)
        check_deadman(config)
    except Exception as e:
        print(f"Error: {e}")
