# US Visa Appointment Finder

An automated tool that checks for available US visa appointment slots in Canada and sends email notifications when slots become available.

## Tech Stack

- **Python 3.12**
- **Selenium WebDriver** for web automation
- **Chrome Browser** with ChromeDriver
- **GitHub Actions** for automated scheduling
- **SMTP** for email notifications
- **Environment Variables** for configuration

## Features

- Automated hourly checks for visa appointment availability
- Multi-recipient email notifications
- Detailed logging system
- Headless browser support for GitHub Actions
- Support for both local and CI/CD environments
- Secure credential management

## Prerequisites

- Python 3.12+
- Chrome Browser
- Gmail account (for SMTP notifications)
- GitHub account (for automated runs)

## Environment Variables

Create a `.env` file with the following variables:

```plaintext
URL="https://ais.usvisa-info.com/en-ca/niv"
EMAIL="your-visa-account@email.com"
PASSWORD="your-visa-account-password"
FACILITY_ID="89"
SCHEDULE_ID="your-schedule-id"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="your-smtp-email@gmail.com"
SMTP_PASSWORD="your-smtp-app-password"
NOTIFICATION_EMAIL=["email1@example.com", "email2@example.com"]
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/visa_appointment_finder.git
cd visa_appointment_finder
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env` file

## Usage

### Local Development

```bash
python visa.py
```

### GitHub Actions Setup

1. Go to your repository's Settings > Secrets and Variables > Actions
2. Add all environment variables as repository secrets
3. Create an environment named `visa_keys`
4. The workflow will automatically run every hour

## How It Works

1. The script launches a Chrome browser (headless in GitHub Actions)
2. Navigates to the US visa appointment website
3. Logs in using provided credentials
4. Checks for available appointment slots
5. If slots are found:
   - Captures available dates
   - Sends email notifications to configured recipients
6. Logs all actions and errors
7. Uploads logs as GitHub Actions artifacts

## Logging

- Logs are stored in `logs/` directory
- Each run creates a timestamped log file
- Both console and file logging enabled
- Debug level logging for detailed troubleshooting

## Security Notes

- Use Gmail App Passwords instead of regular passwords
- Store sensitive data in GitHub Secrets
- Never commit `.env` file
- Credentials are masked in logs

## Troubleshooting

Common issues and solutions:

- Check logs in GitHub Actions artifacts
- Verify environment variables are properly set
- Ensure Gmail App Password is correct
- Check Chrome/ChromeDriver compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Author

Rahul Jassal
