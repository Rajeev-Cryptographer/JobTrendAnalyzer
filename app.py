import os
import logging
import pandas as pd
import json
import csv
import pandas as pd
import os
from flask import Flask, jsonify
from wordcloud import WordCloud
from io import BytesIO
import base64
import google.generativeai as genai
import hashlib
import re
from datetime import datetime
from flask import Flask, request, jsonify, redirect, url_for, send_file, session, Response, send_from_directory
from scraper import scrape_internshala, fetch_remotive_jobs
from analyzer import process_data, generate_india_heatmap, generate_world_heatmap

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "job-trends-analyzer-secret")

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAllPOBYm1JtERq4RaxHTsqfQmiqRDVyz0"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found. AI predictions will not work.")

# File paths for CSV storage
INTERNSHALA_CSV = 'internshala_jobs.csv'
REMOTIVE_CSV = 'remotive_jobs.csv'
COMBINED_CSV = 'combined_jobs.csv'
USERS_CSV = 'users.csv'

# Create users.csv if it doesn't exist
if not os.path.exists(USERS_CSV):
    try:
        with open(USERS_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'email', 'password_hash', 'created_at'])
            logger.info(f"Created new users database: {USERS_CSV}")
    except Exception as e:
        logger.error(f"Error creating users CSV: {str(e)}")

@app.route('/')
def index():
    """Serve the home page."""
    return send_from_directory('templates', 'index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Scrape jobs from Internshala."""
    try:
        jobs = scrape_internshala()
        if jobs:
            jobs_df = pd.DataFrame(jobs)
            jobs_df.to_csv(INTERNSHALA_CSV, index=False)
            session['internshala_scraped'] = True
            return jsonify({'success': True, 'count': len(jobs)})
        return jsonify({'success': False, 'error': 'No jobs found'})
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/fetch', methods=['POST'])
def fetch():
    """Fetch jobs from Remotive API."""
    try:
        jobs = fetch_remotive_jobs()
        if jobs:
            jobs_df = pd.DataFrame(jobs)
            jobs_df.to_csv(REMOTIVE_CSV, index=False)
            session['remotive_fetched'] = True
            return jsonify({'success': True, 'count': len(jobs)})
        return jsonify({'success': False, 'error': 'No jobs found'})
    except Exception as e:
        logger.error(f"Error fetching API data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze')
def analyze():
    """Analyze and display job data."""
    try:
        internshala_exists = os.path.exists(INTERNSHALA_CSV)
        remotive_exists = os.path.exists(REMOTIVE_CSV)
        
        if not (internshala_exists or remotive_exists):
            return send_from_directory('templates', 'analysis.html')
        
        # Combine datasets if both exist
        if internshala_exists and remotive_exists and session.get('internshala_scraped') and session.get('remotive_fetched'):
            internshala_df = pd.read_csv(INTERNSHALA_CSV)
            remotive_df = pd.read_csv(REMOTIVE_CSV)
            combined_df = process_data(internshala_df, remotive_df)
            combined_df.to_csv(COMBINED_CSV, index=False)
            jobs = combined_df.to_dict('records')
        elif internshala_exists and session.get('internshala_scraped'):
            jobs = pd.read_csv(INTERNSHALA_CSV).to_dict('records')
        elif remotive_exists and session.get('remotive_fetched'):
            jobs = pd.read_csv(REMOTIVE_CSV).to_dict('records')
        else:
            jobs = []
            
        # Get unique values for filters
        locations = sorted(list(set([job.get('location', '') for job in jobs if job.get('location')])))
        companies = sorted(list(set([job.get('company', '') for job in jobs if job.get('company')])))
        
        # Store the data in session for JavaScript to access
        session['jobs_data'] = jobs
        session['locations'] = locations
        session['companies'] = companies
        
        return send_from_directory('templates', 'analysis.html')
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        session['error'] = str(e)
        return send_from_directory('templates', 'analysis.html')

@app.route('/predict')
def predict():
    """Generate AI predictions using Gemini API."""
    if not GEMINI_API_KEY:
        session['prediction_error'] = "Gemini API key not configured."
        return send_from_directory('templates', 'prediction.html')
    
    try:
        if os.path.exists(COMBINED_CSV):
            df = pd.read_csv(COMBINED_CSV)
        elif os.path.exists(INTERNSHALA_CSV) and os.path.exists(REMOTIVE_CSV):
            internshala_df = pd.read_csv(INTERNSHALA_CSV)
            remotive_df = pd.read_csv(REMOTIVE_CSV)
            df = process_data(internshala_df, remotive_df)
        elif os.path.exists(INTERNSHALA_CSV):
            df = pd.read_csv(INTERNSHALA_CSV)
        elif os.path.exists(REMOTIVE_CSV):
            df = pd.read_csv(REMOTIVE_CSV)
        else:
            session['prediction_error'] = "No job data available for prediction."
            return send_from_directory('templates', 'prediction.html')
        
        # Get top job titles and skills for context
        top_jobs = df['title'].value_counts().head(15).to_dict()
        skills_list = []
        for skills in df['skills'].dropna():
            if isinstance(skills, str):
                skills_list.extend([s.strip() for s in skills.split(',')])
        top_skills = pd.Series(skills_list).value_counts().head(20).to_dict()
        
        # Prepare prompt for Gemini
        prompt = f"""
        Based on the following job market data:
        
        Top Job Titles: {top_jobs}
        Top Skills: {top_skills}
        
        Please provide:
        1. Future trending jobs for the next 5 years
        2. Emerging important skills in the job market
        3. Advice for job seekers based on this data
        
        Format your response in clear sections with bullet points.
        """
        
        # Call Gemini API
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        response = model.generate_content(prompt)
        prediction = response.text
        
        # Store prediction in session
        session['prediction'] = prediction
        return send_from_directory('templates', 'prediction.html')
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        session['prediction_error'] = str(e)
        return send_from_directory('templates', 'prediction.html')

@app.route('/heatmaps')
def heatmaps():
    """Generate and display job distribution heatmaps."""
    try:
        # Don't pre-generate maps here, we'll use the API endpoint instead
        # This prevents session cookie from growing too large
        return send_from_directory('templates', 'heatmaps.html')
    except Exception as e:
        logger.error(f"Error serving heatmaps page: {str(e)}")
        return redirect(url_for('index'))
# import pandas as pd
# import os
# from flask import Flask, jsonify
# from wordcloud import WordCloud
# from io import BytesIO
# import base64

# from flask import jsonify, session
# import pandas as pd
# import os
# import base64
# from io import BytesIO
# from wordcloud import WordCloud
# import matplotlib.pyplot as plt

# @app.route('/wordcloud')
# def wordcloud():
#     try:
#         # Load data
#         REMOTIVE_CSV = 'remotive_jobs.csv'
#         INTERNSHALA_CSV = 'internshala_jobs.csv'
#         COMBINED_CSV = 'combined_jobs.csv'

#         if os.path.exists(COMBINED_CSV):
#             df = pd.read_csv(COMBINED_CSV)
#         elif os.path.exists(INTERNSHALA_CSV) and os.path.exists(REMOTIVE_CSV):
#             internshala_df = pd.read_csv(INTERNSHALA_CSV)
#             remotive_df = pd.read_csv(REMOTIVE_CSV)
#             df = pd.concat([internshala_df, remotive_df])
#         elif os.path.exists(INTERNSHALA_CSV):
#             df = pd.read_csv(INTERNSHALA_CSV)
#         elif os.path.exists(REMOTIVE_CSV):
#             df = pd.read_csv(REMOTIVE_CSV)
#         else:
#             return jsonify({'error': 'No job data available for word cloud.'}), 404
        
#         # Generate word cloud data
#         # df.head
#         all_skills = df['skills'].dropna().str.lower().str.split(', ')
        
#         skill_list = [skill for sublist in all_skills for skill in sublist]
        
#         if not skill_list:
#             return jsonify({'error': 'No skills found for word cloud.'}), 400
        
#         from collections import Counter
#         skill_counts = Counter(skill_list)

#         # Generate image
#         wc = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(skill_counts)
#         img_io = BytesIO()
#         wc.to_image().save(img_io, 'PNG')
#         img_io.seek(0)
#         base64_image = base64.b64encode(img_io.read()).decode('utf-8')

#         # Top skills (optional)
#         top_skills = [{'skill': skill, 'count': count} for skill, count in skill_counts.most_common(10)]

#         return jsonify({
#             'image': base64_image,
#             'top_skills': top_skills
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get job data."""
    try:
        jobs = []
        if os.path.exists(COMBINED_CSV):
            df = pd.read_csv(COMBINED_CSV)
            jobs = clean_dataframe_for_json(df)
        elif os.path.exists(INTERNSHALA_CSV) and os.path.exists(REMOTIVE_CSV):
            internshala_df = pd.read_csv(INTERNSHALA_CSV)
            remotive_df = pd.read_csv(REMOTIVE_CSV)
            combined_df = process_data(internshala_df, remotive_df)
            jobs = clean_dataframe_for_json(combined_df)
        elif os.path.exists(INTERNSHALA_CSV):
            df = pd.read_csv(INTERNSHALA_CSV)
            jobs = clean_dataframe_for_json(df)
        elif os.path.exists(REMOTIVE_CSV):
            df = pd.read_csv(REMOTIVE_CSV)
            jobs = clean_dataframe_for_json(df)
            
        return jsonify(jobs)
    except Exception as e:
        logger.error(f"Error getting job data: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
def clean_dataframe_for_json(df):
    """Clean DataFrame to ensure it can be serialized to JSON."""
    # Fill NaN values
    df = df.fillna({
        'title': 'Untitled Job',
        'company': 'Unknown Company',
        'location': 'Location Not Specified',
        'salary': 'Not Specified',
        'skills': '',
        'link': '#',
        'source': 'Unknown'
    })
    
    # Convert to records
    records = df.to_dict('records')
    
    # Additional cleaning for each record
    for record in records:
        for key, value in record.items():
            # Handle any remaining non-serializable values
            if pd.isna(value) or pd.isnull(value):
                record[key] = None
    
    return records

@app.route('/api/prediction')
def api_prediction():
    """API endpoint to get prediction data."""
    try:
        if 'prediction' in session:
            return jsonify({'prediction': session['prediction']})
        
        if not GEMINI_API_KEY:
            return jsonify({'error': 'Gemini API key not configured'}), 400
        
        if os.path.exists(COMBINED_CSV):
            df = pd.read_csv(COMBINED_CSV)
        elif os.path.exists(INTERNSHALA_CSV) and os.path.exists(REMOTIVE_CSV):
            internshala_df = pd.read_csv(INTERNSHALA_CSV)
            remotive_df = pd.read_csv(REMOTIVE_CSV)
            df = process_data(internshala_df, remotive_df)
        elif os.path.exists(INTERNSHALA_CSV):
            df = pd.read_csv(INTERNSHALA_CSV)
        elif os.path.exists(REMOTIVE_CSV):
            df = pd.read_csv(REMOTIVE_CSV)
        else:
            return jsonify({'error': 'No job data available for prediction'}), 404
        
        # Get top job titles and skills for context
        top_jobs = df['title'].value_counts().head(15).to_dict()
        skills_list = []
        for skills in df['skills'].dropna():
            if isinstance(skills, str):
                skills_list.extend([s.strip() for s in skills.split(',')])
        top_skills = pd.Series(skills_list).value_counts().head(20).to_dict()
        
        # Create a fallback prediction in case of API issues
        try:
            # Try to list available models first
            available_models = genai.list_models()
            logger.info(f"Available Gemini models: {[model.name for model in available_models]}")
            
            # Find the correct model name
            gemini_model = None
            for model in available_models:
                if 'gemini' in model.name.lower():
                    gemini_model = model.name
                    logger.info(f"Using Gemini model: {gemini_model}")
                    break
            
            # If no Gemini model found, try the default
            if not gemini_model:
                gemini_model = 'models/gemini-1.5-pro'
                logger.info(f"Using default model: {gemini_model}")
                
            prompt = f"""
            Based on the following job market data:
            
            Top Job Titles: {top_jobs}
            Top Skills: {top_skills}
            
            Please provide:
            1. Future trending jobs for the next 5 years
            2. Emerging important skills in the job market
            3. Advice for job seekers based on this data
            
            Format your response in clear sections with bullet points.
            """
            
            # Create the model with the found name
            model = genai.GenerativeModel(gemini_model)
            response = model.generate_content(prompt)
            prediction = response.text
            
            session['prediction'] = prediction
            return jsonify({'prediction': prediction})
        
        except Exception as inner_e:
            logger.error(f"Error with Gemini API: {str(inner_e)}")
            
            # Create a simple analysis based on the data
            prediction = create_analysis_from_data(top_jobs, top_skills)
            session['prediction'] = prediction
            return jsonify({'prediction': prediction})
            
    except Exception as e:
        logger.error(f"Error generating prediction data: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
def create_analysis_from_data(top_jobs, top_skills):
    """Create a simple job market analysis when AI prediction is unavailable."""
    job_titles = list(top_jobs.keys())[:5]
    skills = list(top_skills.keys())[:10]
    
    analysis = f"""
## Future Trending Jobs

Based on current job market data, these job titles show high demand:

* {job_titles[0] if len(job_titles) > 0 else 'Software Developer'}
* {job_titles[1] if len(job_titles) > 1 else 'Data Scientist'}
* {job_titles[2] if len(job_titles) > 2 else 'Product Manager'} 
* {job_titles[3] if len(job_titles) > 3 else 'UX/UI Designer'}
* {job_titles[4] if len(job_titles) > 4 else 'DevOps Engineer'}

These roles are likely to continue growing in demand over the next 5 years, with increasing opportunities in remote work arrangements.

## Emerging Important Skills

The following skills appear frequently in job listings and are worth developing:

* {skills[0] if len(skills) > 0 else 'Python'}
* {skills[1] if len(skills) > 1 else 'JavaScript'}
* {skills[2] if len(skills) > 2 else 'SQL'}
* {skills[3] if len(skills) > 3 else 'AWS'}
* {skills[4] if len(skills) > 4 else 'React'}
* {skills[5] if len(skills) > 5 else 'Data Analysis'}
* {skills[6] if len(skills) > 6 else 'Machine Learning'}
* {skills[7] if len(skills) > 7 else 'Communication Skills'}
* {skills[8] if len(skills) > 8 else 'Project Management'}
* {skills[9] if len(skills) > 9 else 'Problem-Solving'}

## Advice for Job Seekers

* Focus on developing the top skills listed above to maximize employability
* Consider roles with high demand and growth potential
* Build a portfolio demonstrating your practical abilities
* Network with professionals in your target industry
* Stay current with industry trends and continuously update your skills
* Don't underestimate the importance of soft skills alongside technical abilities
* Consider remote work opportunities to expand your job search geographically
* Tailor your resume to highlight the specific skills each job posting requests
    """
    
    return analysis

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return  send_from_directory(directory='templates', path='login.html')
        
        try:
            # Check if username exists in users.csv
            user = None
            with open(USERS_CSV, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Check if username or email matches
                    if row['username'] == username or row['email'] == username:
                        user = row
                        break
            
            if not user:
                return  send_from_directory(directory='templates', path='login.html',error='Invalid username or password')
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != user['password_hash']:
                 return  send_from_directory(directory='templates', path='login.html', error='Invalid username or password')
            
            # Set session data
            session['logged_in'] = True
            session['username'] = user['username']
            
            # Redirect to home page
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return  send_from_directory(directory='templates', path='login.html',error='An error occurred. Please try again.')
    
    # GET request
    return send_from_directory('templates', 'login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not email or not password or not confirm_password:
            send_from_directory(directory='templates', path='signup.html',error='An Fields are required')
        
        if password != confirm_password:
            send_from_directory(directory='templates', path='signup.html',error='Password do not match')
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
           send_from_directory(directory='templates', path='signup.html',error='Invalid email format')
            
        # Validate password strength
        if len(password) < 6:
            return send_from_directory(directory='templates', path='signup.html',error='Password must be at least 6 characters long')
        
        try:
            # Check if username or email already exists
            with open(USERS_CSV, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['username'] == username:
                        return send_from_directory(directory='templates', path='signup.html',error='Username already exists')
                    if row['email'] == email:
                        return send_from_directory(directory='templates', path='signup.html',error='Email already exists')
            
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Add user to CSV
            with open(USERS_CSV, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, email, password_hash, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            
            # Log success
            logger.info(f"New user registered: {username}")
            
            # Redirect to login page with success message
            return send_from_directory(directory='templates', path='login.html',success=f'Account created successfully. Please log in, {username}!')
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            return send_from_directory(directory='templates', path='signup.html',error='An error occurred. Please try again.')
    
    # GET request
    return send_from_directory('templates', 'signup.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/api/maps')
def api_maps():
    """API endpoint to get map data."""
    try:
        results = {'india_map': None, 'world_map': None}
        
        if os.path.exists(INTERNSHALA_CSV):
            india_map = generate_india_heatmap(pd.read_csv("internshala_jobs.csv"))
            if india_map:
                results['india_map'] = india_map
        
        if os.path.exists(REMOTIVE_CSV):
            world_map = generate_world_heatmap(pd.read_csv("remotive_jobs.csv"))
            if world_map:
                results['world_map'] = world_map
        
        if not results['india_map'] and not results['world_map']:
            return jsonify({'error': 'No location data available for maps'}), 404
            
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error generating map data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/charts')
def charts():
    """Display interactive charts and visualizations."""
    return send_from_directory('templates', 'charts.html')

@app.route('/download/<dataset>')
def download(dataset):
    """Download specified CSV dataset."""
    try:
        if dataset == 'internshala' and os.path.exists(INTERNSHALA_CSV):
            logger.info(f"Downloading Internshala CSV: {INTERNSHALA_CSV}")
            return send_file(
                INTERNSHALA_CSV, 
                as_attachment=True,
                download_name="internshala_jobs.csv",
                mimetype="text/csv"
            )
        elif dataset == 'remotive' and os.path.exists(REMOTIVE_CSV):
            logger.info(f"Downloading Remotive CSV: {REMOTIVE_CSV}")
            return send_file(
                REMOTIVE_CSV, 
                as_attachment=True,
                download_name="remotive_jobs.csv",
                mimetype="text/csv"
            )
        elif dataset == 'combined' and os.path.exists(COMBINED_CSV):
            logger.info(f"Downloading Combined CSV: {COMBINED_CSV}")
            return send_file(
                COMBINED_CSV, 
                as_attachment=True,
                download_name="combined_jobs.csv",
                mimetype="text/csv"
            )
        else:
            # If file doesn't exist, log the error and redirect
            logger.warning(f"Requested CSV file not found: {dataset}")
            session['download_error'] = f"The requested dataset '{dataset}' is not available. Please scrape or fetch job data first."
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error downloading file '{dataset}': {str(e)}")
        session['download_error'] = f"Error downloading file: {str(e)}"
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
