from timeit import timeit
from jira import JIRA
from atlassian import Confluence
from datetime import datetime as t
import pandas as pd
from constants import JIRASERVER, CONFLSERVER, TOKENAUTH, BATCHSIZE
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import word_tokenize

jira = JIRA(JIRASERVER, token_auth= TOKENAUTH)

components_map = {'10927':1, '10928': 1, '12519': 2, '12105': 3, '12158': 3, '10912': 4, '10913': 4}
queries = ['(project = "CN" AND component in ("Virtual Gateway - BE", "Virtual Gateway - UI"))',
           '(project = "CN" AND component in ("AppRF - BE", "AppRF - UI"))',
           '(project = "CN" AND component in ("Route Orchestrator Monitoring", "Route Orchestrator Monitoring - FE"))',
           '(project = "AOS" AND component in ("Base OS Security"))'
           ]
# queries = ['(project = "CN" AND component in ("deployment-tools"))']

def fetch_jira_all_queries(query_list):
    results = []
    for query in query_list:
        start_idx = 0
        while True:
            batch_results = fetch_jira_issues(query, start_idx)
            if not batch_results:
                break
            start_idx += BATCHSIZE
            results.extend(batch_results)
    return results

def fetch_jira_issue_by_bug(bug_id):
    return jira.issue(bug_id)
    
def fetch_jira_issues(query, start_idx, maxResults=BATCHSIZE, fields=['components', 'comment', 'summary','description']):
    fetched_jira_issues = None
    try:
        fetched_jira_issues = jira.search_issues(query, startAt=start_idx, maxResults=maxResults, fields=fields)
    except Exception as e:
        print(e)
    return fetched_jira_issues

def fetch_user_only_comments(jira_issue):
    return ''
    if not jira_issue:
        return ""
    return ' '.join([ comment.body for comment in jira_issue.fields.comment.comments if str(comment.author.displayName) != 'Jira Automation' ])

def clean_strings(input_str):
    copy_str = input_str
    if not input_str or len(input_str)<1:
        return ""

    replacements = [
        ("\xa0",' '),
        ("\n",' '),
        ("\r",' '),
        ("\*Summary:\*",' '),
        ("Test blocker",' '),
        ("TAC Ticket:",' '),
        (r'\w*\d\w*', ''),
        (r"\{code.*\{code\}",' '),
        (r"!.*!",' '),
        (r"\*.*\*",' '),
        (r"\{color.*\}", ' '),
        (r"TAC Ticket==========Ticket# :", ' '),
        (r"Issue Summary.*=.*=",' '),
        (r"Issue Description.*=.*=",' '),
        (r"=.*=", ' '),
        (r"\[~.*@hpe\.com\]", ' '),
        (r"\[.*@gmail\.com\]", ' '),
        (r"\[.*@arubanetworks\.com\]", ' '),
        (r"ubuntu@.*:~\$", ' '),
        (r"\.py:", ' '),
        (r"https://([A-Za-z0-9]+(-[A-Za-z0-9]+)+).*\.arubathena\.com/[A-Za-z0-9]*", ' '),
        ("@Assignee", ' '),
        (r'http\S+', ' '),
        (r"\*\.hpe\.com", ' '),
        (r"\[[^\]]*\]", ' '),
        (r"^[a-zA-Z0-9]{32}$", ' '),
        (r"\[(.*?)\]", ' '),
        (r"^.*\.har$", ' '),
        (r"^.*\..*hpe\.com$", ' '),
        (r'[^A-Za-z0-9]+', ' ')
    ]

    for prev, curr in replacements:
        try:
            input_str = re.sub(prev, curr, input_str)
        except Exception as e:
            print(e)
            # print(copy_str)
    
    input_str = input_str.strip().lower()
    text_tokens = word_tokenize(input_str)
    return ' '.join([i for i in text_tokens if not i.isdigit()])

def generate_csv_file(dataframe):
    df = pd.DataFrame(dataframe)
    df.to_csv("/Users/thentu/Desktop/test_scrape_no_comments.csv")

def main():

    start_t = t.now()
    all_issues = fetch_jira_all_queries(queries)
    end_t = t.now() - start_t
    dataframe = []
    print(f"Total count of issues across {len(queries)} apps = {len(all_issues)} and took {end_t} ms")

    for issue in all_issues:
        user_comments = fetch_user_only_comments(issue) or ''
        issue_summary = issue.fields.summary or ''
        issue_description = issue.fields.description or ''
        data_txt = user_comments + ' ' + issue_summary + ' ' + issue_description
        data_txt = clean_strings(data_txt)

        if not data_txt or len(data_txt)<5:
            continue

        issue_dataframe_row = {"Bug":issue.key, "Data":data_txt, "CompId":components_map[issue.fields.components[0].id]}
        dataframe.append(issue_dataframe_row)

    generate_csv_file(dataframe)

if __name__=='__main__':
    main()
