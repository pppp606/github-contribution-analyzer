#!/usr/bin/env python3

import subprocess
import json
import argparse
import sys
import time
from datetime import datetime
from typing import Dict, List
import concurrent.futures
from pathlib import Path

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
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
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
        print(f"Error fetching contribution data for {username}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {username}: {e}")
        return None

def load_users_from_file(filepath: str) -> List[str]:
    """
    JSONファイルからユーザーリストを読み込む
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # ユーザー検索結果ファイルからユーザー名を抽出
        if isinstance(data, list) and len(data) > 0:
            if 'login' in data[0]:  # github_users_*.json形式
                return [user['login'] for user in data]
            else:  # 単純なリスト形式
                return data
        
        return []
    except Exception as e:
        print(f"Error loading users from {filepath}: {e}")
        return []

def fetch_contributions_batch(usernames: List[str], year: int = None, max_workers: int = 5) -> Dict[str, Dict]:
    """
    複数ユーザーのコントリビューションデータを並列取得
    """
    print(f"Fetching contributions for {len(usernames)} users...")
    
    results = {}
    failed_users = []
    
    # レート制限を考慮して並列数を制限
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # タスクを投入
        future_to_username = {
            executor.submit(get_user_contributions, username, year): username 
            for username in usernames
        }
        
        for future in concurrent.futures.as_completed(future_to_username):
            username = future_to_username[future]
            try:
                result = future.result()
                if result:
                    results[username] = result
                else:
                    failed_users.append(username)
                
                # API rate limitを避けるため間隔を空ける
                time.sleep(0.2)
                
            except Exception as e:
                print(f"Error processing {username}: {e}")
                failed_users.append(username)
    
    print(f"Successfully fetched: {len(results)} users")
    if failed_users:
        print(f"Failed to fetch: {failed_users}")
    
    return results

def analyze_batch_contributions(batch_data: Dict[str, Dict]) -> Dict:
    """
    バッチ取得したコントリビューションデータを分析
    """
    print("Analyzing batch contribution data...")
    
    users_stats = {}
    aggregate_stats = {
        "total_users": len(batch_data),
        "total_contributions": 0,
        "total_commits": 0,
        "total_issues": 0,
        "total_prs": 0,
        "total_reviews": 0,
        "active_users": 0,
        "daily_aggregate": {},  # 日付別の全ユーザー合計
        "top_contributors": [],
        "monthly_aggregate": {}
    }
    
    for username, user_data in batch_data.items():
        contrib_collection = user_data["contributionsCollection"]
        calendar = contrib_collection["contributionCalendar"]
        
        # 個別ユーザー統計
        user_stats = {
            "username": username,
            "name": user_data.get("name"),
            "total_contributions": calendar["totalContributions"],
            "total_commits": contrib_collection["totalCommitContributions"],
            "total_issues": contrib_collection["totalIssueContributions"],
            "total_prs": contrib_collection["totalPullRequestContributions"],
            "total_reviews": contrib_collection["totalPullRequestReviewContributions"],
            "daily_contributions": {}
        }
        
        # 日別データの処理
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                date = day["date"]
                count = day["contributionCount"]
                
                user_stats["daily_contributions"][date] = count
                
                # 全体統計に加算
                if date not in aggregate_stats["daily_aggregate"]:
                    aggregate_stats["daily_aggregate"][date] = 0
                aggregate_stats["daily_aggregate"][date] += count
                
                # 月別統計
                month_key = date[:7]  # YYYY-MM
                if month_key not in aggregate_stats["monthly_aggregate"]:
                    aggregate_stats["monthly_aggregate"][month_key] = 0
                aggregate_stats["monthly_aggregate"][month_key] += count
        
        users_stats[username] = user_stats
        
        # 全体統計に加算
        aggregate_stats["total_contributions"] += user_stats["total_contributions"]
        aggregate_stats["total_commits"] += user_stats["total_commits"]
        aggregate_stats["total_issues"] += user_stats["total_issues"]
        aggregate_stats["total_prs"] += user_stats["total_prs"]
        aggregate_stats["total_reviews"] += user_stats["total_reviews"]
        
        if user_stats["total_contributions"] > 0:
            aggregate_stats["active_users"] += 1
    
    # トップコントリビューター
    aggregate_stats["top_contributors"] = sorted(
        [{"username": u["username"], "name": u["name"], "contributions": u["total_contributions"]} 
         for u in users_stats.values()],
        key=lambda x: x["contributions"],
        reverse=True
    )
    
    return {
        "aggregate_stats": aggregate_stats,
        "users_stats": users_stats,
        "analysis_date": datetime.now().isoformat()
    }

def create_visualization_data(analysis_data: Dict) -> Dict:
    """
    グラフ化用のデータ構造を作成
    """
    aggregate_stats = analysis_data["aggregate_stats"]
    users_stats = analysis_data["users_stats"]
    
    # 日別の合計グラフ用データ
    daily_data = []
    for date, total in sorted(aggregate_stats["daily_aggregate"].items()):
        daily_data.append({
            "date": date,
            "total_contributions": total
        })
    
    # 月別の合計グラフ用データ
    monthly_data = []
    for month, total in sorted(aggregate_stats["monthly_aggregate"].items()):
        monthly_data.append({
            "month": month,
            "total_contributions": total
        })
    
    # ユーザー別比較データ
    user_comparison = []
    for user_data in users_stats.values():
        user_comparison.append({
            "username": user_data["username"],
            "name": user_data["name"],
            "total_contributions": user_data["total_contributions"],
            "commits": user_data["total_commits"],
            "issues": user_data["total_issues"],
            "prs": user_data["total_prs"],
            "reviews": user_data["total_reviews"]
        })
    
    # 上位ユーザーのトレンド比較用データ
    top_users = aggregate_stats["top_contributors"][:10]  # 上位10ユーザー
    trend_data = {}
    
    for user in top_users:
        username = user["username"]
        if username in users_stats:
            trend_data[username] = []
            daily_contrib = users_stats[username]["daily_contributions"]
            for date in sorted(daily_contrib.keys()):
                trend_data[username].append({
                    "date": date,
                    "contributions": daily_contrib[date]
                })
    
    return {
        "daily_aggregate": daily_data,
        "monthly_aggregate": monthly_data,
        "user_comparison": sorted(user_comparison, key=lambda x: x["total_contributions"], reverse=True),
        "top_users_trend": trend_data
    }

def save_analysis_results(analysis_data: Dict, viz_data: Dict, output_prefix: str):
    """
    分析結果を複数のファイルに保存
    """
    # 完全な分析データ
    with open(f"{output_prefix}_full_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    # グラフ化用データ
    with open(f"{output_prefix}_visualization_data.json", 'w', encoding='utf-8') as f:
        json.dump(viz_data, f, indent=2, ensure_ascii=False)
    
    # サマリーレポート
    summary = {
        "summary": analysis_data["aggregate_stats"],
        "top_contributors": analysis_data["aggregate_stats"]["top_contributors"][:20]
    }
    with open(f"{output_prefix}_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis results saved:")
    print(f"  - {output_prefix}_full_analysis.json (Complete data)")
    print(f"  - {output_prefix}_visualization_data.json (Chart data)")
    print(f"  - {output_prefix}_summary.json (Summary report)")

def print_analysis_summary(analysis_data: Dict):
    """
    分析結果のサマリーを表示
    """
    aggregate = analysis_data["aggregate_stats"]
    
    print(f"\n=== Batch Contribution Analysis Summary ===")
    print(f"Total Users Analyzed: {aggregate['total_users']}")
    print(f"Active Users: {aggregate['active_users']}")
    print(f"Total Contributions: {aggregate['total_contributions']:,}")
    print(f"Total Commits: {aggregate['total_commits']:,}")
    print(f"Total Issues: {aggregate['total_issues']:,}")
    print(f"Total Pull Requests: {aggregate['total_prs']:,}")
    print(f"Total Reviews: {aggregate['total_reviews']:,}")
    
    print(f"\nTop 10 Contributors:")
    for i, user in enumerate(aggregate["top_contributors"][:10]):
        name_part = f" ({user['name']})" if user['name'] else ""
        print(f"  {i+1:2d}. {user['username']}{name_part}: {user['contributions']:,} contributions")
    
    # 最もアクティブな日を見つける
    if aggregate["daily_aggregate"]:
        max_day = max(aggregate["daily_aggregate"].items(), key=lambda x: x[1])
        print(f"\nMost Active Day: {max_day[0]} ({max_day[1]:,} total contributions)")
    
    # 最もアクティブな月を見つける
    if aggregate["monthly_aggregate"]:
        max_month = max(aggregate["monthly_aggregate"].items(), key=lambda x: x[1])
        print(f"Most Active Month: {max_month[0]} ({max_month[1]:,} total contributions)")

def main():
    parser = argparse.ArgumentParser(description='GitHub batch contribution analyzer')
    parser.add_argument('--users-file', '-f', required=True,
                       help='JSON file containing user list (from github_users_*.json)')
    parser.add_argument('--year', type=int,
                       help='Specific year to analyze (default: current year)')
    parser.add_argument('--output-prefix', '-o', default='batch_analysis',
                       help='Output files prefix (default: batch_analysis)')
    parser.add_argument('--max-workers', type=int, default=3,
                       help='Maximum parallel workers (default: 3)')
    parser.add_argument('--limit', type=int,
                       help='Limit number of users to process (for testing)')
    parser.add_argument('--summary-only', action='store_true',
                       help='Only show summary, do not save files')
    
    args = parser.parse_args()
    
    # GitHub CLIがインストールされているかチェック
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: GitHub CLI (gh) is not installed or not authenticated.")
        print("Please install gh and run 'gh auth login' first.")
        sys.exit(1)
    
    # ユーザーリストを読み込み
    usernames = load_users_from_file(args.users_file)
    if not usernames:
        print(f"No users found in {args.users_file}")
        sys.exit(1)
    
    # 制限がある場合は適用
    if args.limit:
        usernames = usernames[:args.limit]
    
    print(f"Processing {len(usernames)} users from {args.users_file}")
    
    # バッチでコントリビューションデータを取得
    batch_data = fetch_contributions_batch(usernames, args.year, args.max_workers)
    
    if not batch_data:
        print("No contribution data was retrieved.")
        sys.exit(1)
    
    # データを分析
    analysis_data = analyze_batch_contributions(batch_data)
    
    # グラフ化用データを作成
    viz_data = create_visualization_data(analysis_data)
    
    # 結果を表示
    print_analysis_summary(analysis_data)
    
    # ファイルに保存
    if not args.summary_only:
        save_analysis_results(analysis_data, viz_data, args.output_prefix)

if __name__ == "__main__":
    main()