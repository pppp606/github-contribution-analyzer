#!/usr/bin/env python3

import json
import argparse
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import pandas as pd
import seaborn as sns
from pathlib import Path

# 日本語フォントの設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")

def load_visualization_data(filepath: str) -> dict:
    """
    グラフ化用データを読み込む
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading visualization data: {e}")
        return None

def create_daily_contributions_chart(data: dict, output_path: str):
    """
    日別コントリビューション合計のグラフを作成
    """
    daily_data = data["daily_aggregate"]
    
    if not daily_data:
        print("No daily data available for charting")
        return
    
    # データフレームに変換
    df = pd.DataFrame(daily_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # グラフ作成
    plt.figure(figsize=(15, 6))
    plt.plot(df['date'], df['total_contributions'], linewidth=1, alpha=0.8)
    plt.fill_between(df['date'], df['total_contributions'], alpha=0.3)
    
    plt.title('Daily Total Contributions - All Users Combined', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Total Contributions', fontsize=12)
    
    # X軸の日付フォーマット
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{output_path}_daily_contributions.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Daily contributions chart saved: {output_path}_daily_contributions.png")

def create_monthly_contributions_chart(data: dict, output_path: str):
    """
    月別コントリビューション合計のグラフを作成
    """
    monthly_data = data["monthly_aggregate"]
    
    if not monthly_data:
        print("No monthly data available for charting")
        return
    
    # データフレームに変換
    df = pd.DataFrame(monthly_data)
    df['month'] = pd.to_datetime(df['month'])
    df = df.sort_values('month')
    
    # グラフ作成
    plt.figure(figsize=(12, 6))
    bars = plt.bar(df['month'], df['total_contributions'], width=20, alpha=0.8)
    
    # バーの値を表示
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=9)
    
    plt.title('Monthly Total Contributions - All Users Combined', fontsize=16, fontweight='bold')
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Total Contributions', fontsize=12)
    
    # X軸の日付フォーマット
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(f"{output_path}_monthly_contributions.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Monthly contributions chart saved: {output_path}_monthly_contributions.png")

def create_user_comparison_chart(data: dict, output_path: str, top_n: int = 20):
    """
    ユーザー別コントリビューション比較グラフを作成
    """
    user_data = data["user_comparison"][:top_n]
    
    if not user_data:
        print("No user data available for charting")
        return
    
    # データフレームに変換
    df = pd.DataFrame(user_data)
    
    # グラフ作成
    plt.figure(figsize=(14, 8))
    
    # 横棒グラフ
    bars = plt.barh(range(len(df)), df['total_contributions'], alpha=0.8)
    
    # ユーザー名を表示（名前がある場合は名前も）
    labels = []
    for _, row in df.iterrows():
        if row['name']:
            labels.append(f"{row['username']}\n({row['name']})")
        else:
            labels.append(row['username'])
    
    plt.yticks(range(len(df)), labels)
    
    # バーの値を表示
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                f'{int(width):,}',
                ha='left', va='center', fontsize=9)
    
    plt.title(f'Top {top_n} Contributors - Total Contributions', fontsize=16, fontweight='bold')
    plt.xlabel('Total Contributions', fontsize=12)
    plt.ylabel('Users', fontsize=12)
    
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(f"{output_path}_user_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"User comparison chart saved: {output_path}_user_comparison.png")

def create_contribution_breakdown_chart(data: dict, output_path: str, top_n: int = 15):
    """
    上位ユーザーのコントリビューション内訳（積み上げ棒グラフ）を作成
    """
    user_data = data["user_comparison"][:top_n]
    
    if not user_data:
        print("No user data available for breakdown chart")
        return
    
    # データフレームに変換
    df = pd.DataFrame(user_data)
    
    # グラフ作成
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 積み上げ棒グラフ
    bottom = [0] * len(df)
    
    categories = ['commits', 'prs', 'issues', 'reviews']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, (category, color) in enumerate(zip(categories, colors)):
        values = df[category].tolist()
        bars = ax.barh(range(len(df)), values, left=bottom, 
                      label=category.replace('prs', 'Pull Requests').title(), 
                      color=color, alpha=0.8)
        bottom = [b + v for b, v in zip(bottom, values)]
    
    # ユーザー名を表示
    labels = [row['username'] for _, row in df.iterrows()]
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels)
    
    ax.set_title(f'Top {top_n} Contributors - Contribution Breakdown', fontsize=16, fontweight='bold')
    ax.set_xlabel('Number of Contributions', fontsize=12)
    ax.set_ylabel('Users', fontsize=12)
    
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(f"{output_path}_contribution_breakdown.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Contribution breakdown chart saved: {output_path}_contribution_breakdown.png")

def create_top_users_trend_chart(data: dict, output_path: str, top_n: int = 5):
    """
    上位ユーザーの日別コントリビューショントレンドを作成
    """
    trend_data = data["top_users_trend"]
    
    if not trend_data:
        print("No trend data available for charting")
        return
    
    plt.figure(figsize=(15, 8))
    
    colors = plt.cm.Set1(range(len(trend_data)))
    
    for i, (username, user_trend) in enumerate(list(trend_data.items())[:top_n]):
        if not user_trend:
            continue
        
        df = pd.DataFrame(user_trend)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 7日移動平均を計算（スムージング）
        df['contributions_smooth'] = df['contributions'].rolling(window=7, center=True).mean()
        
        plt.plot(df['date'], df['contributions_smooth'], 
                label=username, linewidth=2, color=colors[i], alpha=0.8)
    
    plt.title(f'Top {top_n} Contributors - Daily Contribution Trends (7-day moving average)', 
              fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Daily Contributions (smoothed)', fontsize=12)
    
    # X軸の日付フォーマット
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{output_path}_top_users_trend.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Top users trend chart saved: {output_path}_top_users_trend.png")

def create_all_charts(data: dict, output_prefix: str):
    """
    すべてのグラフを作成
    """
    print("Creating all visualization charts...")
    
    create_daily_contributions_chart(data, output_prefix)
    create_monthly_contributions_chart(data, output_prefix)
    create_user_comparison_chart(data, output_prefix)
    create_contribution_breakdown_chart(data, output_prefix)
    create_top_users_trend_chart(data, output_prefix)
    
    print(f"\nAll charts created with prefix: {output_prefix}")

def main():
    parser = argparse.ArgumentParser(description='GitHub contribution data visualizer')
    parser.add_argument('--data-file', '-f', required=True,
                       help='Visualization data JSON file (from github_batch_analyzer.py)')
    parser.add_argument('--output-prefix', '-o', default='contrib_charts',
                       help='Output charts prefix (default: contrib_charts)')
    parser.add_argument('--chart-type', choices=['daily', 'monthly', 'users', 'breakdown', 'trend', 'all'],
                       default='all', help='Type of chart to create (default: all)')
    parser.add_argument('--top-n', type=int, default=20,
                       help='Number of top users to show in charts (default: 20)')
    
    args = parser.parse_args()
    
    # データを読み込み
    data = load_visualization_data(args.data_file)
    if not data:
        sys.exit(1)
    
    # 出力ディレクトリを作成
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # チャートタイプに応じてグラフを作成
    if args.chart_type == 'all':
        create_all_charts(data, args.output_prefix)
    elif args.chart_type == 'daily':
        create_daily_contributions_chart(data, args.output_prefix)
    elif args.chart_type == 'monthly':
        create_monthly_contributions_chart(data, args.output_prefix)
    elif args.chart_type == 'users':
        create_user_comparison_chart(data, args.output_prefix, args.top_n)
    elif args.chart_type == 'breakdown':
        create_contribution_breakdown_chart(data, args.output_prefix, args.top_n)
    elif args.chart_type == 'trend':
        create_top_users_trend_chart(data, args.output_prefix, args.top_n)

if __name__ == "__main__":
    main()