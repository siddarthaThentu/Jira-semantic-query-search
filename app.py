from flask import Flask, render_template, request, jsonify
from jira import JIRA
from jira_scrape import fetch_jira_issue_by_bug, clean_strings
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')
app = Flask(__name__)

JIRASERVER = 'https://jira.arubanetworks.com'
CONFLSERVER = 'https://confluence.arubanetworks.com'
TOKENAUTH = "xxxx"
embeddings = np.load("/Users/thentu/Desktop/embeddings.npy")
df = pd.read_csv("/Users/thentu/Desktop/test_scrape_no_comments.csv")

@app.route('/')
def index():
    return render_template('index.html')

def return_relevant_bugs(data_txt, bug_id=None):
    data_txt = clean_strings(data_txt)
    data_vec = model.encode([data_txt])
    val = cosine_similarity(data_vec, embeddings)
    sorted_val = np.argsort(-val)[0][:11]
    returned_bugs = []
    if bug_id:
        returned_bugs = [ (df.Bug[val], f"https://jira.arubanetworks.com/browse/{df.Bug[val]}") for val in sorted_val if df.Bug[val] != bug_id]
    else:
        returned_bugs = [ (df.Bug[val], f"https://jira.arubanetworks.com/browse/{df.Bug[val]}") for val in sorted_val ]
    return returned_bugs

@app.route('/shortenurl')
def shortenurl():
    summary=request.args['shortcode']
    returned_bugs = return_relevant_bugs(summary)
    return render_template('shortenurl.html', shortcode=returned_bugs[:10])

@app.route('/shortenurl2')
def shortenurl2():
    shortcode=request.args['shortcode2']
    issue = fetch_jira_issue_by_bug(shortcode)
    issue_summary = issue.fields.summary or ''
    issue_description = issue.fields.description or ''
    data_txt = issue_summary + ' ' + issue_description
    returned_bugs = []
    if not data_txt:
        return "No valid data found in bug"
    returned_bugs = return_relevant_bugs(data_txt, bug_id=shortcode)
    return render_template('shortenurl.html', shortcode=returned_bugs[:10])

if __name__ == '__main__':
    app.run(debug=True, port=5001)