# Internshala Scraping Configuration
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import logging
from datetime import datetime
from requests.exceptions import RequestException

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://internshala.com"
LISTING_URL = f"{BASE_URL}/jobs"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

def scrape_internshala(page_limit=150):
    jobs = []
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = f"internshala_jobs_{timestamp}.csv"

    try:
        for page in range(52, page_limit + 1):
            url = f"{LISTING_URL}/page-{page}/"
            logger.info(f"Scraping {url}...")

            time.sleep(random.uniform(0.1, 0.3))  # Polite delay
            response = requests.get(url, headers=get_random_headers(), timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            job_containers = soup.select('.individual_internship')

            if not job_containers:
                logger.info(f"No jobs found on page {page}. Stopping early.")
                break

            for job in job_containers:
                try:
                    title_tag = job.select_one('.job-title-href')
                    company_tag = job.select_one('.company-name')
                    location_tag = job.select_one('.locations a')
                    salary_tags = job.find_all('span', class_='desktop')

                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    link = BASE_URL + title_tag['href'] if title_tag and title_tag.get('href') else "N/A"
                    company = company_tag.get_text(strip=True) if company_tag else "N/A"
                    location = location_tag.get_text(strip=True) if location_tag else "N/A"
                    salary = salary_tags[0].get_text(strip=True) if salary_tags else "N/A"

                    skills = "N/A"
                    if link != "N/A":
                        try:
                            job_response = requests.get(link, headers=get_random_headers(), timeout=20)
                            job_soup = BeautifulSoup(job_response.text, 'html.parser')
                            skills_container = job_soup.select('.round_tabs_container .round_tabs')
                            if skills_container:
                                skills = ', '.join([skill.get_text(strip=True) for skill in skills_container])
                            time.sleep(0.1)
                        except Exception as e:
                            logger.warning(f"Error fetching skills from {link}: {str(e)}")

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'salary': salary,
                        'skills': skills,
                        'link': link,
                        'source': 'Internshala'
                    }

                    jobs.append(job_data)

                    # Dynamically save to CSV
                    pd.DataFrame([job_data]).to_csv(output_file, mode='a', header=not pd.io.common.file_exists(output_file), index=False)

                    logger.info(f"Saved: {title} at {company}")
                except Exception as e:
                    logger.error(f"Error parsing job listing: {str(e)}")
                    continue

        logger.info(f"Total jobs scraped and saved: {len(jobs)}")
        return jobs

    except RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return []


def fetch_remotive_jobs():
    """
    Fetch remote jobs from Remotive.io API
    
    Returns:
        List of job dictionaries with title, company, location, salary, skills, link
    """
    api_url = "https://remotive.com/api/remote-jobs"
    output_file = "remotive_jobs.csv"
    
    try:
        logger.info(f"Fetching jobs from Remotive API: {api_url}")
        
        # Send API request
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        print(response.status_code)
        print(response.headers)
        print(response.text)
        
        data = response.json()
        jobs = data.get('jobs', [])
        
        if not jobs:
            logger.warning("No jobs found in Remotive API response")
            return []
            
        logger.info(f"Received {len(jobs)} jobs from Remotive")
        
        # Transform to consistent format
        formatted_jobs = []
        for job in jobs:
            # Extract skills from tags and categories
            skills = []
            if 'tags' in job and job['tags']:
                skills.extend(job['tags'])
            if 'category' in job and job['category']:
                skills.append(job['category'])
                
            # Format job data
            job_data = {
                'title': job.get('title', ''),
                'company': job.get('company_name', ''),
                'location': job.get('candidate_required_location', 'Remote'),
                'salary': job.get('salary', ''),
                'skills': ', '.join(skills) if skills else '',
                'link': job.get('url', ''),
                'source': 'Remotive'
            }
            
            formatted_jobs.append(job_data)
        
        # Save to CSV for later use
        if formatted_jobs:
            jobs_df = pd.DataFrame(formatted_jobs)
            jobs_df.to_csv(output_file, index=False)
            logger.info(f"Successfully fetched {len(formatted_jobs)} jobs from Remotive")
            
        return formatted_jobs
    
    except RequestException as e:
        logger.error(f"Request error during Remotive API fetch: {str(e)}")
        return []
    
    except ValueError as e:
        logger.error(f"JSON parsing error with Remotive API: {str(e)}")
        return []
    
    except Exception as e:
        logger.error(f"Unexpected error during Remotive API fetch: {str(e)}")
        return []

# For testing the script directly
if __name__ == "__main__":
    print("Scraping Internshala jobs...")
    internshala_jobs = scrape_internshala(page_limit=150)
    print(f"Scraped {len(internshala_jobs)} jobs from Internshala")
    
    print("\nFetching Remotive jobs...")
    remotive_jobs = fetch_remotive_jobs()
    print(f"Fetched {len(remotive_jobs)} jobs from Remotive")
