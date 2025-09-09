#!/usr/bin/env python3

import subprocess
import json
import time
import sys
import argparse
from typing import List, Dict

def search_github_users_with_gh(query: str, max_pages: int = 18) -> List[Dict]:
    """
    GitHub CLI (gh)を使用してユーザーを検索する
    """
    all_users = []
    per_page = 100  # GitHub APIの最大値
    
    print(f"Searching for users matching '{query}' using GitHub CLI...")
    
    for page in range(1, max_pages + 1):
        print(f"Fetching page {page}/{max_pages}...")
        
        try:
            # gh api コマンドを使用してGitHub REST APIを直接呼び出し
            api_url = f"search/users?q={query}&per_page={per_page}&page={page}"
            cmd = ["gh", "api", api_url]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            users = data.get("items", [])
            if not users:
                print(f"No more users found on page {page}")
                break
            
            for user in users:
                user_info = {
                    "login": user["login"],
                    "id": user["id"],
                    "avatar_url": user["avatar_url"],
                    "html_url": user["html_url"],
                    "type": user["type"],
                    "score": user.get("score", 0),
                    "source": "search"
                }
                all_users.append(user_info)
            
            print(f"Found {len(users)} users on page {page}")
            
            # API rate limitを避けるため少し待機
            time.sleep(0.5)
            
        except subprocess.CalledProcessError as e:
            print(f"Error on page {page}: {e}")
            print(f"stderr: {e.stderr}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON decode error on page {page}: {e}")
            break
    
    return all_users

def get_organization_members(org_name: str, max_pages: int = 50) -> List[Dict]:
    """
    特定のOrganizationのメンバー一覧を取得する
    """
    all_members = []
    per_page = 100  # GitHub APIの最大値
    
    print(f"Fetching members of organization '{org_name}'...")
    
    for page in range(1, max_pages + 1):
        print(f"Fetching page {page}...")
        
        try:
            # Organization のメンバー一覧を取得
            api_url = f"orgs/{org_name}/members?per_page={per_page}&page={page}"
            cmd = ["gh", "api", api_url]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            members = json.loads(result.stdout)
            
            if not members:
                print(f"No more members found on page {page}")
                break
            
            for member in members:
                member_info = {
                    "login": member["login"],
                    "id": member["id"],
                    "avatar_url": member["avatar_url"],
                    "html_url": member["html_url"],
                    "type": member["type"],
                    "site_admin": member.get("site_admin", False),
                    "source": f"org_member:{org_name}"
                }
                all_members.append(member_info)
            
            print(f"Found {len(members)} members on page {page}")
            
            # API rate limitを避けるため少し待機
            time.sleep(0.5)
            
        except subprocess.CalledProcessError as e:
            print(f"Error on page {page}: {e}")
            if "Not Found" in e.stderr:
                print(f"Organization '{org_name}' not found or no public members")
                break
            print(f"stderr: {e.stderr}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON decode error on page {page}: {e}")
            break
    
    return all_members

def get_organization_public_members(org_name: str) -> List[Dict]:
    """
    特定のOrganizationのpublicメンバー一覧を取得する（権限不要版）
    """
    all_members = []
    per_page = 100
    max_pages = 50
    
    print(f"Fetching public members of organization '{org_name}'...")
    
    for page in range(1, max_pages + 1):
        try:
            api_url = f"orgs/{org_name}/public_members?per_page={per_page}&page={page}"
            cmd = ["gh", "api", api_url]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            members = json.loads(result.stdout)
            
            if not members:
                break
            
            for member in members:
                member_info = {
                    "login": member["login"],
                    "id": member["id"],
                    "avatar_url": member["avatar_url"],
                    "html_url": member["html_url"],
                    "type": member["type"],
                    "site_admin": member.get("site_admin", False),
                    "source": f"org_public_member:{org_name}"
                }
                all_members.append(member_info)
            
            print(f"Found {len(members)} public members on page {page}")
            time.sleep(0.5)
            
        except subprocess.CalledProcessError as e:
            if "Not Found" in e.stderr:
                print(f"Organization '{org_name}' not found")
                break
            break
    
    return all_members

def save_users_to_file(users: List[Dict], filename: str):
    """
    ユーザー情報をJSONファイルに保存
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(users)} users to {filename}")

def main():
    parser = argparse.ArgumentParser(description='GitHub users fetcher')
    parser.add_argument('--mode', choices=['search', 'org', 'org-public'], default='search',
                       help='Mode: search users, get org members, or get org public members')
    parser.add_argument('--query', '-q', required=True,
                       help='Search query (for search mode) or organization name (for org mode)')
    parser.add_argument('--max-pages', type=int, default=18,
                       help='Maximum pages to fetch (default: 18)')
    parser.add_argument('--output', '-o',
                       help='Output filename (auto-generated if not specified)')
    
    args = parser.parse_args()
    
    # GitHub CLIがインストールされているかチェック
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: GitHub CLI (gh) is not installed or not authenticated.")
        print("Please install gh and run 'gh auth login' first.")
        sys.exit(1)
    
    # 出力ファイル名を決定
    if args.output:
        output_file = args.output
    else:
        safe_query = args.query.replace('/', '_').replace(' ', '_')
        if args.mode == 'search':
            output_file = f"github_users_search_{safe_query}.json"
        elif args.mode == 'org':
            output_file = f"github_org_members_{safe_query}.json"
        else:  # org-public
            output_file = f"github_org_public_members_{safe_query}.json"
    
    # モードに応じて処理を実行
    users = []
    if args.mode == 'search':
        users = search_github_users_with_gh(args.query, args.max_pages)
    elif args.mode == 'org':
        users = get_organization_members(args.query, args.max_pages)
    elif args.mode == 'org-public':
        users = get_organization_public_members(args.query)
    
    if users:
        save_users_to_file(users, output_file)
        print(f"\nTotal users found: {len(users)}")
        print(f"Output saved to: {output_file}")
        print("\nFirst 5 users:")
        for i, user in enumerate(users[:5]):
            print(f"{i+1}. {user['login']} - {user['html_url']}")
    else:
        print("No users found.")

if __name__ == "__main__":
    main()