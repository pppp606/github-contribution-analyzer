#!/usr/bin/env python3

import subprocess
import json
import time
import sys

def search_github_users_with_gh(query="example", max_pages=18):
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
                    "score": user["score"]
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

def save_users_to_file(users, filename="github_users_search.json"):
    """
    ユーザー情報をJSONファイルに保存
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(users)} users to {filename}")

def main():
    # GitHub CLIがインストールされているかチェック
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: GitHub CLI (gh) is not installed or not authenticated.")
        print("Please install gh and run 'gh auth login' first.")
        sys.exit(1)
    
    users = search_github_users_with_gh()
    
    if users:
        save_users_to_file(users)
        print(f"\nTotal users found: {len(users)}")
        print("\nFirst 5 users:")
        for i, user in enumerate(users[:5]):
            print(f"{i+1}. {user['login']} - {user['html_url']}")
    else:
        print("No users found.")

if __name__ == "__main__":
    main()