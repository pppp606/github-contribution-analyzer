#!/usr/bin/env python3

import json
import argparse
import sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter, WeekdayLocator
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

def create_weekly_group_trends(data: dict, output_path: str):
    """
    週次グループ全体のコントリビューショントレンドグラフを作成（完全な7日間の週のみ）
    """
    daily_data = data["daily_aggregate"]
    
    if not daily_data:
        print("No daily data available for weekly charting")
        return
    
    # データフレームに変換
    df = pd.DataFrame(daily_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 週の開始日（月曜日）を計算
    df['week_start'] = df['date'] - pd.to_timedelta(df['date'].dt.dayofweek, unit='d')
    
    # 週次集計（日数もカウント）
    weekly_df = df.groupby('week_start').agg({
        'total_contributions': 'sum',
        'date': 'count'  # 各週の日数をカウント
    }).reset_index()
    weekly_df.rename(columns={'date': 'days_in_week'}, inplace=True)
    
    # 完全な7日間の週のみを保持
    complete_weeks = weekly_df[weekly_df['days_in_week'] == 7].copy()
    
    print(f"Total weeks found: {len(weekly_df)}")
    print(f"Complete weeks (7 days): {len(complete_weeks)}")
    print(f"Excluded incomplete weeks: {len(weekly_df) - len(complete_weeks)}")
    
    # グラフ作成
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # 上段: 週次棒グラフ
    bars = ax1.bar(complete_weeks['week_start'], complete_weeks['total_contributions'], 
                   width=5, alpha=0.8, color='#2E86C1')
    
    # 棒の値を表示
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=9)
    
    ax1.set_title('Weekly Total Contributions - Group Overview (Complete 7-day weeks only)', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Week (Starting Monday)', fontsize=12)
    ax1.set_ylabel('Weekly Total Contributions', fontsize=12)
    ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 下段: 週次推移線グラフ + 移動平均
    ax2.plot(complete_weeks['week_start'], complete_weeks['total_contributions'], 
             marker='o', linewidth=2, markersize=4, alpha=0.8, 
             color='#2E86C1', label='Weekly Contributions')
    
    # 4週移動平均を追加
    complete_weeks['4week_ma'] = complete_weeks['total_contributions'].rolling(window=4, center=True).mean()
    ax2.plot(complete_weeks['week_start'], complete_weeks['4week_ma'], 
             linewidth=3, alpha=0.7, color='#E74C3C', 
             label='4-Week Moving Average')
    
    ax2.set_title('Weekly Contribution Trend with Moving Average', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Week (Starting Monday)', fontsize=12)
    ax2.set_ylabel('Weekly Total Contributions', fontsize=12)
    ax2.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(f"{output_path}_weekly_group_trends.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Weekly group trends chart saved: {output_path}_weekly_group_trends.png")
    
    # 週次統計を出力
    print(f"\n=== Weekly Statistics (Complete 7-day weeks only) ===")
    print(f"Complete weeks analyzed: {len(complete_weeks)}")
    print(f"Average weekly contributions: {complete_weeks['total_contributions'].mean():.0f}")
    print(f"Peak week: {complete_weeks.loc[complete_weeks['total_contributions'].idxmax(), 'week_start'].strftime('%Y-%m-%d')} ({complete_weeks['total_contributions'].max():,} contributions)")
    print(f"Lowest week: {complete_weeks.loc[complete_weeks['total_contributions'].idxmin(), 'week_start'].strftime('%Y-%m-%d')} ({complete_weeks['total_contributions'].min():,} contributions)")

def create_weekly_heatmap(data: dict, output_path: str):
    """
    週次コントリビューションのヒートマップを作成
    """
    daily_data = data["daily_aggregate"]
    
    if not daily_data:
        print("No daily data available for heatmap")
        return
    
    # データフレームに変換
    df = pd.DataFrame(daily_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 週と年を追加
    df['year'] = df['date'].dt.year
    df['week'] = df['date'].dt.isocalendar().week
    
    # 週次集計
    weekly_heatmap = df.groupby(['year', 'week']).agg({
        'total_contributions': 'sum'
    }).reset_index()
    
    # ピボットテーブル作成
    pivot_data = weekly_heatmap.pivot(index='year', columns='week', values='total_contributions')
    pivot_data = pivot_data.fillna(0)
    
    # ヒートマップ作成
    plt.figure(figsize=(20, 6))
    sns.heatmap(pivot_data, 
                annot=False, 
                cmap='YlOrRd', 
                cbar_kws={'label': 'Weekly Contributions'},
                linewidths=0.5)
    
    plt.title('Weekly Contribution Heatmap - Group Activity by Year/Week', fontsize=16, fontweight='bold')
    plt.xlabel('Week of Year', fontsize=12)
    plt.ylabel('Year', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(f"{output_path}_weekly_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Weekly heatmap saved: {output_path}_weekly_heatmap.png")

def create_weekly_growth_analysis(data: dict, output_path: str):
    """
    週次成長率分析グラフを作成
    """
    daily_data = data["daily_aggregate"]
    
    if not daily_data:
        print("No daily data available for growth analysis")
        return
    
    # データフレームに変換
    df = pd.DataFrame(daily_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 週の開始日を計算
    df['week_start'] = df['date'] - pd.to_timedelta(df['date'].dt.dayofweek, unit='d')
    
    # 週次集計
    weekly_df = df.groupby('week_start').agg({
        'total_contributions': 'sum'
    }).reset_index()
    
    # 成長率計算
    weekly_df['week_over_week_change'] = weekly_df['total_contributions'].pct_change() * 100
    weekly_df['week_over_week_absolute'] = weekly_df['total_contributions'].diff()
    
    # グラフ作成
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # 上段: 週次絶対変化量
    colors = ['red' if x < 0 else 'green' for x in weekly_df['week_over_week_absolute']]
    bars1 = ax1.bar(weekly_df['week_start'], weekly_df['week_over_week_absolute'], 
                    width=5, alpha=0.7, color=colors)
    
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_title('Week-over-Week Change in Contributions (Absolute)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Week (Starting Monday)', fontsize=12)
    ax1.set_ylabel('Change in Contributions', fontsize=12)
    ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 下段: 週次成長率（%）
    colors = ['red' if x < 0 else 'green' for x in weekly_df['week_over_week_change']]
    bars2 = ax2.bar(weekly_df['week_start'], weekly_df['week_over_week_change'], 
                    width=5, alpha=0.7, color=colors)
    
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_title('Week-over-Week Growth Rate (%)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Week (Starting Monday)', fontsize=12)
    ax2.set_ylabel('Growth Rate (%)', fontsize=12)
    ax2.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f"{output_path}_weekly_growth_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Weekly growth analysis saved: {output_path}_weekly_growth_analysis.png")

def create_all_weekly_charts(data: dict, output_prefix: str):
    """
    週次分析グラフをすべて作成
    """
    print("Creating weekly group trend analysis charts...")
    
    create_weekly_group_trends(data, output_prefix)
    create_weekly_heatmap(data, output_prefix)
    create_weekly_growth_analysis(data, output_prefix)
    
    print(f"\nAll weekly charts created with prefix: {output_prefix}")

def main():
    parser = argparse.ArgumentParser(description='GitHub group weekly trend analyzer')
    parser.add_argument('--data-file', '-f', required=True,
                       help='Visualization data JSON file (from github_batch_analyzer.py)')
    parser.add_argument('--output-prefix', '-o', default='weekly_trends',
                       help='Output charts prefix (default: weekly_trends)')
    
    args = parser.parse_args()
    
    # データを読み込み
    data = load_visualization_data(args.data_file)
    if not data:
        sys.exit(1)
    
    # 出力ディレクトリを作成
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 週次グループトレンドのみを作成
    create_weekly_group_trends(data, args.output_prefix)

if __name__ == "__main__":
    main()