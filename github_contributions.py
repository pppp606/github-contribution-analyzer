#!/usr/bin/env python3

import subprocess
import json
import argparse
import sys
from datetime import datetime
from typing import Dict, List

def get_user_contributions(username: str, year: int = None) -> Dict:
    """
    指定したユーザーのコントリビューションデータを取得
    """
    print(f"Fetching contribution data for user: {username}")
    
    # 年指定がある場合のクエリ調整
    from_date = ""
    to_date = ""
    if year:
        from_date = f'{year}-01-01T00:00:00Z'
        to_date = f'{year}-12-31T23:59:59Z'
        print(f"Year filter: {year}")
    
    # GraphQLクエリ
    query = '''
    query($username: String!, $from: DateTime, $to: DateTime) {
      user(login: $username) {
        name
        login
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          totalRepositoriesWithContributedCommits
          totalRepositoriesWithContributedIssues
          totalRepositoriesWithContributedPullRequests
          totalRepositoriesWithContributedPullRequestReviews
          contributionCalendar {
            totalContributions
            months {
              name
              year
              totalWeeks
            }
            weeks {
              contributionDays {
                date
                contributionCount
                color
                weekday
              }
            }
          }
          commitContributionsByRepository(maxRepositories: 100) {
            repository {
              name
              owner {
                login
              }
            }
            contributions(first: 100) {
              totalCount
            }
          }
        }
      }
    }
    '''
    
    try:
        cmd = ["gh", "api", "graphql", "-f", f"query={query}", "-f", f"username={username}"]
        if from_date and to_date:
            cmd.extend(["-f", f"from={from_date}", "-f", f"to={to_date}"])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        if data.get("data", {}).get("user") is None:
            print(f"User '{username}' not found")
            return None
        
        return data["data"]["user"]
        
    except subprocess.CalledProcessError as e:
        print(f"Error fetching contribution data: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None

def analyze_contributions(user_data: Dict) -> Dict:
    """
    コントリビューションデータを分析して統計を作成
    """
    if not user_data:
        return {}
    
    contrib_collection = user_data["contributionsCollection"]
    calendar = contrib_collection["contributionCalendar"]
    
    # 基本統計
    stats = {
        "username": user_data["login"],
        "name": user_data.get("name"),
        "total_contributions": calendar["totalContributions"],
        "total_commits": contrib_collection["totalCommitContributions"],
        "total_issues": contrib_collection["totalIssueContributions"],
        "total_prs": contrib_collection["totalPullRequestContributions"],
        "total_pr_reviews": contrib_collection["totalPullRequestReviewContributions"],
        "total_repos_contributed": {
            "commits": contrib_collection["totalRepositoriesWithContributedCommits"],
            "issues": contrib_collection["totalRepositoriesWithContributedIssues"],
            "prs": contrib_collection["totalRepositoriesWithContributedPullRequests"],
            "reviews": contrib_collection["totalRepositoriesWithContributedPullRequestReviews"]
        }
    }
    
    # 日別データの分析
    daily_contributions = []
    max_contributions_day = {"date": "", "count": 0}
    active_days = 0
    monthly_stats = {}
    
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            daily_data = {
                "date": day["date"],
                "count": day["contributionCount"],
                "color": day["color"],
                "weekday": day["weekday"]
            }
            daily_contributions.append(daily_data)
            
            if day["contributionCount"] > 0:
                active_days += 1
            
            if day["contributionCount"] > max_contributions_day["count"]:
                max_contributions_day = {
                    "date": day["date"],
                    "count": day["contributionCount"]
                }
            
            # 月別統計
            month_key = day["date"][:7]  # YYYY-MM
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {"total": 0, "active_days": 0}
            monthly_stats[month_key]["total"] += day["contributionCount"]
            if day["contributionCount"] > 0:
                monthly_stats[month_key]["active_days"] += 1
    
    stats.update({
        "active_days": active_days,
        "max_contributions_day": max_contributions_day,
        "average_daily_contributions": round(stats["total_contributions"] / len(daily_contributions), 2),
        "monthly_breakdown": monthly_stats,
        "daily_contributions": daily_contributions
    })
    
    # リポジトリ別コミット統計
    repo_contributions = []
    for repo_contrib in contrib_collection["commitContributionsByRepository"]:
        repo_info = {
            "repository": f"{repo_contrib['repository']['owner']['login']}/{repo_contrib['repository']['name']}",
            "commit_count": repo_contrib["contributions"]["totalCount"]
        }
        repo_contributions.append(repo_info)
    
    stats["repository_contributions"] = sorted(repo_contributions, key=lambda x: x["commit_count"], reverse=True)
    
    return stats

def save_contributions_to_file(data: Dict, filename: str):
    """
    コントリビューションデータをJSONファイルに保存
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Contribution data saved to {filename}")

def print_contribution_summary(stats: Dict):
    """
    コントリビューション統計の概要を表示
    """
    print(f"\n=== Contribution Summary for {stats['username']} ===")
    if stats.get('name'):
        print(f"Name: {stats['name']}")
    
    print(f"\nOverall Statistics:")
    print(f"  Total Contributions: {stats['total_contributions']}")
    print(f"  Total Commits: {stats['total_commits']}")
    print(f"  Total Issues: {stats['total_issues']}")
    print(f"  Total Pull Requests: {stats['total_prs']}")
    print(f"  Total PR Reviews: {stats['total_pr_reviews']}")
    print(f"  Active Days: {stats['active_days']}")
    print(f"  Average Daily Contributions: {stats['average_daily_contributions']}")
    
    print(f"\nMost Active Day:")
    print(f"  Date: {stats['max_contributions_day']['date']}")
    print(f"  Contributions: {stats['max_contributions_day']['count']}")
    
    print(f"\nRepositories Contributed To:")
    print(f"  Commits: {stats['total_repos_contributed']['commits']} repos")
    print(f"  Issues: {stats['total_repos_contributed']['issues']} repos")
    print(f"  Pull Requests: {stats['total_repos_contributed']['prs']} repos")
    print(f"  Reviews: {stats['total_repos_contributed']['reviews']} repos")
    
    print(f"\nTop 5 Repository Contributions (by commits):")
    for i, repo in enumerate(stats['repository_contributions'][:5]):
        print(f"  {i+1}. {repo['repository']}: {repo['commit_count']} commits")

def main():
    parser = argparse.ArgumentParser(description='GitHub contribution data fetcher')
    parser.add_argument('username', help='GitHub username')
    parser.add_argument('--year', type=int, help='Specific year to fetch (default: current year)')
    parser.add_argument('--output', '-o', help='Output filename (auto-generated if not specified)')
    parser.add_argument('--summary-only', action='store_true', 
                       help='Only show summary, do not save full data')
    
    args = parser.parse_args()
    
    # GitHub CLIがインストールされているかチェック
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: GitHub CLI (gh) is not installed or not authenticated.")
        print("Please install gh and run 'gh auth login' first.")
        sys.exit(1)
    
    # データ取得
    user_data = get_user_contributions(args.username, args.year)
    if not user_data:
        sys.exit(1)
    
    # 分析
    stats = analyze_contributions(user_data)
    
    # 結果表示
    print_contribution_summary(stats)
    
    # ファイル保存
    if not args.summary_only:
        if args.output:
            output_file = args.output
        else:
            year_suffix = f"_{args.year}" if args.year else ""
            output_file = f"github_contributions_{args.username}{year_suffix}.json"
        
        save_contributions_to_file(stats, output_file)

if __name__ == "__main__":
    main()