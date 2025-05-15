import os

# Use GITHUB_WORKSPACE if available (for GitHub Actions), else use current working directory
REPO_ROOT = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
LOGS_DIR = os.path.join(REPO_ROOT, 'logs')
DATA_DIR = os.path.join(REPO_ROOT, 'data')
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

import json
import time
import logging
import schedule
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'job_alerts.log')),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

class JobAlertSystem:
    def __init__(self):
        self.seen_jobs_file = os.path.join(DATA_DIR, 'seen_jobs.json')
        self.seen_jobs = self._load_seen_jobs()
        self.job_title = os.getenv('JOB_TITLE', 'Software Engineer')
        self.location = os.getenv('LOCATION', 'San Francisco')
        self.keywords = os.getenv('KEYWORDS', '').split(',')
        
        # Slack configuration
        self.slack_token = os.getenv('SLACK_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#job-alerts')
        self.slack_client = WebClient(token=self.slack_token) if self.slack_token else None

    def _load_seen_jobs(self):
        """Load previously seen jobs from JSON file."""
        try:
            if os.path.exists(self.seen_jobs_file):
                with open(self.seen_jobs_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading seen jobs: {e}")
            return {}

    def _save_seen_jobs(self):
        """Save seen jobs to JSON file."""
        try:
            with open(self.seen_jobs_file, 'w') as f:
                json.dump(self.seen_jobs, f)
        except Exception as e:
            logging.error(f"Error saving seen jobs: {e}")

    def _send_slack_alert(self, job):
        """Send Slack notification for a new job posting."""
        if not self.slack_client:
            logging.warning("Slack configuration incomplete. Skipping Slack alert.")
            return

        try:
            # Create a formatted message for Slack
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎯 New Job Alert: {job['title']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Company:*\n{job['company']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Location:*\n{job['location']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{job['description'][:300]}..."
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Source:* {job['source']}\n<{job['url']}|View Job Posting>"
                    }
                }
            ]

            self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                blocks=blocks,
                text=f"New Job Alert: {job['title']} at {job['company']}"
            )

            logging.info(f"Slack alert sent for job: {job['title']}")
        except SlackApiError as e:
            logging.error(f"Error sending Slack alert: {e.response['error']}")
        except Exception as e:
            logging.error(f"Error sending Slack alert: {e}")

    def _check_indeed(self):
        """Check Indeed for new job postings."""
        try:
            # Indeed URL with search parameters
            url = f"https://www.indeed.com/jobs?q={self.job_title}&l={self.location}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards:
                job_id = card.get('data-jk', '')
                if job_id in self.seen_jobs:
                    continue

                title = card.find('h2', class_='jobTitle').text.strip()
                company = card.find('span', class_='companyName').text.strip()
                location = card.find('div', class_='companyLocation').text.strip()
                description = card.find('div', class_='job-snippet').text.strip()
                
                # Check if job matches keywords
                if not any(keyword.lower() in description.lower() for keyword in self.keywords):
                    continue

                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'url': f"https://www.indeed.com/viewjob?jk={job_id}",
                    'source': 'Indeed',
                    'timestamp': datetime.now().isoformat()
                }

                self.seen_jobs[job_id] = job_data
                self._send_slack_alert(job_data)
                logging.info(f"New job found on Indeed: {title} at {company}")

        except Exception as e:
            logging.error(f"Error checking Indeed: {e}")

    def _check_linkedin(self):
        """Check LinkedIn for new job postings."""
        try:
            # LinkedIn URL with search parameters
            url = f"https://www.linkedin.com/jobs/search/?keywords={self.job_title}&location={self.location}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='job-card-container')
            
            for card in job_cards:
                job_id = card.get('data-job-id', '')
                if job_id in self.seen_jobs:
                    continue

                title = card.find('h3', class_='job-card-title').text.strip()
                company = card.find('h4', class_='job-card-company').text.strip()
                location = card.find('span', class_='job-card-location').text.strip()
                description = card.find('div', class_='job-card-description').text.strip()
                
                # Check if job matches keywords
                if not any(keyword.lower() in description.lower() for keyword in self.keywords):
                    continue

                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'url': f"https://www.linkedin.com/jobs/view/{job_id}",
                    'source': 'LinkedIn',
                    'timestamp': datetime.now().isoformat()
                }

                self.seen_jobs[job_id] = job_data
                self._send_slack_alert(job_data)
                logging.info(f"New job found on LinkedIn: {title} at {company}")

        except Exception as e:
            logging.error(f"Error checking LinkedIn: {e}")

    def check_jobs(self):
        """Check all job sites for new postings."""
        logging.info("Starting job check...")
        self._check_indeed()
        self._check_linkedin()
        self._save_seen_jobs()
        logging.info("Job check completed")

def main():
    job_alert = JobAlertSystem()
    job_alert.check_jobs()

if __name__ == "__main__":
    main() 