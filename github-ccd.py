import argparse
import requests
from datetime import datetime, timedelta
import csv

def get_github_api(url, token, debug):
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    if debug:
        print(f"Requesting URL: {url}")
    response.raise_for_status()
    return response.json()

def get_repositories(org, token, base_url, exclude_filter, debug):
    repos = []
    page = 1
    total_fetched_repos = 0
    while True:
        url = f'{base_url}/orgs/{org}/repos?page={page}&per_page=100'
        try:
            result = get_github_api(url, token, debug)
            fetched_repos_count = len(result)
            total_fetched_repos += fetched_repos_count
            if debug:
                print(f"Fetched {fetched_repos_count} repositories on page {page}.")
                for repo in result:
                    print(f"Repo name: {repo['name']}")

            if not result:
                break

            for repo in result:
                repo_name = repo['name']
                # Apply filtering only if exclude_filter is non-empty
                if exclude_filter and exclude_filter.lower() in repo_name.lower():
                    continue
                repos.append(repo_name)

            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            break

    if debug:
        print(f"Total repositories fetched: {total_fetched_repos}")
        print(f"Total repositories found (after filtering): {len(repos)}")
    return repos

def get_recent_contributors(org, repo, token, base_url, debug):
    contributors = set()
    since_date = (datetime.now() - timedelta(days=90)).isoformat()
    page = 1
    while True:
        url = f'{base_url}/repos/{org}/{repo}/commits?since={since_date}&page={page}&per_page=100'
        commits = get_github_api(url, token, debug)
        if not commits:
            break
        for commit in commits:
            if commit['author']:
                contributors.add(commit['author']['login'])
                if debug:
                    print(f"Added contributor '{commit['author']['login']}' from repository '{repo}'.")
        page += 1
        if debug:
            print(f"Processed page {page} of commits for repository '{repo}'.")
    return contributors

def write_to_csv(contributors_repo_count, filename, debug):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Developer', 'Number of Repos'])
        for developer, count in contributors_repo_count.items():
            writer.writerow([developer, count])
            if debug:
                print(f"Wrote developer '{developer}' with count {count} to CSV.")
    if debug:
        print(f"CSV file '{filename}' has been created.")

def main():
    parser = argparse.ArgumentParser(description='Get the count of unique developers who have committed in the past 90 days in a GitHub organization.')
    parser.add_argument('--token', help='Personal access token for GitHub', required=True)
    parser.add_argument('--org', help='GitHub organization name', required=True)
    parser.add_argument('--github_url', help='Base URL for GitHub API (for GitHub Enterprise)', default='https://api.github.com')
    parser.add_argument('--exclude', help='Exclude repositories containing this string in their name', default='')
    parser.add_argument('--output_csv', help='Output CSV file name', required=True)
    parser.add_argument('--debug', help='Enable debug mode for more verbose output', action='store_true')
    args = parser.parse_args()

    contributors_repo_count = {}
    repos = get_repositories(args.org, args.token, args.github_url, args.exclude, args.debug)
    for repo in repos:
        contributors = get_recent_contributors(args.org, repo, args.token, args.github_url, args.debug)
        for contributor in contributors:
            contributors_repo_count[contributor] = contributors_repo_count.get(contributor, 0) + 1
            if args.debug:
                print(f"Updating count for contributor '{contributor}'.")

    print(f"Total unique developers in {args.org} who have committed in the past 90 days: {len(contributors_repo_count)}")
    write_to_csv(contributors_repo_count, args.output_csv, args.debug)

if __name__ == "__main__":
    main()
