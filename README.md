# Job Alert System

A Python-based job alert system that monitors job boards for new postings matching your criteria and sends notifications to Slack.

## Features

- Monitors Indeed and LinkedIn for new job postings
- Configurable search criteria (job title, location, keywords)
- Slack notifications for new matching jobs
- Duplicate detection to avoid repeated alerts
- Runs continuously in the background
- Detailed logging for troubleshooting

## Setup

1. Install Python 3.x if not already installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your configuration:
   ```
   SLACK_TOKEN=your-slack-bot-token
   SLACK_CHANNEL=#job-alerts
   JOB_TITLE=Software Engineer
   LOCATION=San Francisco
   KEYWORDS=python,java,aws
   ```

## Security Note

- **Never commit your `.env` file or secrets to the repository.**
- For GitHub Actions, store all secrets (like `SLACK_TOKEN`) in the repository's **Settings > Secrets and variables > Actions**.
- The `.env` file is included in `.gitignore` by default.

## Slack Setup

1. Create a new Slack App in your workspace:
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name your app and select your workspace

2. Add Bot Token Scopes:
   - Go to "OAuth & Permissions"
   - Under "Scopes", add `chat:write` permission
   - Install the app to your workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

3. Invite the bot to your channel:
   - Go to the channel where you want to receive alerts
   - Type `/invite @YourBotName`

## Usage

Run the script:
```bash
python src/main.py
```

The script will check for new jobs every 15 minutes and send Slack notifications for any new matching positions.

## Configuration

You can modify the following in the `.env` file:
- Job search criteria (title, location, keywords)
- Slack settings (token, channel)
- Check interval (default: 15 minutes)

## Logging

Logs are stored in `logs/job_alerts.log` for troubleshooting and monitoring. 