#!/usr/bin/env python3
"""
LangSmith 调试和监控工具

此脚本提供了一系列工具来监控和调试忆语 (YiYu) 的对话流程。
"""

import os
import sys
import time
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langsmith import Client
from config import Config
from memory_agent import run_conversation

# Load environment variables
load_dotenv()

class LangSmithDebugger:
    """LangSmith 调试器类"""

    def __init__(self):
        """初始化调试器"""
        self.client = None
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "YiYu")
        self._initialize_client()

    def _initialize_client(self):
        """初始化 LangSmith 客户端"""
        try:
            langsmith_config = Config.get_langsmith_config()
            if langsmith_config.get("LANGCHAIN_API_KEY"):
                self.client = Client(
                    api_url=langsmith_config["LANGCHAIN_ENDPOINT"],
                    api_key=langsmith_config["LANGCHAIN_API_KEY"]
                )

                # 验证项目是否存在
                self._verify_project()
                print(f"✅ LangSmith 客户端已初始化，项目: {self.project_name}")
            else:
                print("❌ LangSmith API Key 未配置")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 初始化 LangSmith 客户端失败: {e}")
            sys.exit(1)

    def _verify_project(self):
        """验证项目是否存在，如果不存在则列出可用项目"""
        try:
            # 尝试列出运行记录来验证项目
            runs = list(self.client.list_runs(project_name=self.project_name, limit=1))
        except Exception as e:
            if "not found" in str(e).lower():
                print(f"⚠️ 项目 '{self.project_name}' 不存在")

                # 列出可用项目
                try:
                    projects = list(self.client.list_projects())
                    if projects:
                        print(f"\n📋 可用的项目:")
                        for project in projects[:5]:  # 只显示前5个
                            print(f"  • {project.name}")

                        print(f"\n💡 解决方法:")
                        print(f"1. 修改 .env 文件中的 LANGCHAIN_PROJECT 为现有项目名")
                        print(f"2. 或运行: python setup_langsmith_project.py")

                        # 建议使用第一个可用项目
                        suggested_project = projects[0].name
                        print(f"3. 快速修复: 设置 LANGCHAIN_PROJECT={suggested_project}")
                    else:
                        print("❌ 没有找到任何可用项目")
                except:
                    print("❌ 无法获取项目列表")

                sys.exit(1)
            else:
                # 其他类型的错误，继续执行
                print(f"⚠️ 项目验证时出现警告: {e}")

    def list_recent_runs(self, limit: int = 10):
        """列出最近的运行记录"""
        print(f"\n📋 最近 {limit} 次运行记录:")
        print("=" * 80)

        try:
            runs = self.client.list_runs(
                project_name=self.project_name,
                limit=limit
            )

            if not runs:
                print("📭 没有找到运行记录")
                return

            for i, run in enumerate(runs, 1):
                print(f"{i:2d}. 【{run.name}】")
                print(f"    ID: {run.id[:8]}...")
                print(f"    状态: {run.status}")
                print(f"    开始时间: {run.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    耗时: {run.end_time - run.start_time if run.end_time else 'N/A'}")

                if run.inputs:
                    input_preview = str(run.inputs)[:100]
                    print(f"    输入预览: {input_preview}...")

                if run.error:
                    print(f"    ❌ 错误: {run.error}")

                print("-" * 40)

        except Exception as e:
            print(f"❌ 获取运行记录失败: {e}")

    def get_run_details(self, run_id: str):
        """获取指定运行的详细信息"""
        print(f"\n🔍 运行详情 (ID: {run_id})")
        print("=" * 80)

        try:
            run = self.client.read_run(run_id)

            print(f"名称: {run.name}")
            print(f"状态: {run.status}")
            print(f"开始时间: {run.start_time}")
            print(f"结束时间: {run.end_time}")
            print(f"耗时: {run.end_time - run.start_time if run.end_time else 'N/A'}")

            print(f"\n📥 输入:")
            if run.inputs:
                for key, value in run.inputs.items():
                    print(f"  {key}: {value}")

            print(f"\n📤 输出:")
            if run.outputs:
                for key, value in run.outputs.items():
                    if isinstance(value, (list, dict)):
                        print(f"  {key}: {type(value).__name__} ({len(value)} 项)")
                    else:
                        print(f"  {key}: {value}")

            if run.error:
                print(f"\n❌ 错误信息:")
                print(f"  {run.error}")

            # 获取子运行
            child_runs = self.client.list_runs(
                project_name=self.project_name,
                parent_run_id=run_id
            )

            if child_runs:
                print(f"\n🔗 子运行 ({len(child_runs)} 个):")
                for child in child_runs:
                    print(f"  • {child.name} ({child.status})")

        except Exception as e:
            print(f"❌ 获取运行详情失败: {e}")

    def analyze_performance(self, hours: int = 24):
        """分析最近几小时的性能"""
        print(f"\n📊 性能分析 (最近 {hours} 小时)")
        print("=" * 80)

        try:
            start_time = datetime.now() - timedelta(hours=hours)

            runs = list(self.client.list_runs(
                project_name=self.project_name,
                start_time=start_time
            ))

            if not runs:
                print("📭 指定时间范围内没有运行记录")
                return

            # 统计分析
            total_runs = len(runs)
            successful_runs = len([r for r in runs if r.status == "success"])
            failed_runs = len([r for r in runs if r.status == "error"])

            execution_times = []
            for run in runs:
                if run.end_time and run.start_time:
                    execution_times.append((run.end_time - run.start_time).total_seconds())

            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

            print(f"总运行次数: {total_runs}")
            print(f"成功次数: {successful_runs} ({successful_runs/total_runs*100:.1f}%)")
            print(f"失败次数: {failed_runs} ({failed_runs/total_runs*100:.1f}%)")
            print(f"平均执行时间: {avg_execution_time:.2f} 秒")

            # 按运行类型统计
            run_types = {}
            for run in runs:
                run_types[run.name] = run_types.get(run.name, 0) + 1

            print(f"\n📈 运行类型分布:")
            for run_type, count in sorted(run_types.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total_runs * 100
                print(f"  {run_type}: {count} ({percentage:.1f}%)")

            # 失败的运行
            failed_run_list = [r for r in runs if r.status == "error"]
            if failed_run_list:
                print(f"\n❌ 失败的运行:")
                for run in failed_run_list[:5]:  # 只显示前5个
                    print(f"  • {run.name} - {run.error[:80]}...")

        except Exception as e:
            print(f"❌ 性能分析失败: {e}")

    def run_test_conversation(self, user_input: str, user_id: str = "debug_user"):
        """运行测试对话并追踪"""
        print(f"\n🧪 测试对话")
        print("=" * 80)
        print(f"用户输入: {user_input}")
        print(f"用户ID: {user_id}")
        print("-" * 40)

        try:
            start_time = time.time()
            response = run_conversation(user_input, user_id)
            end_time = time.time()

            print(f"AI回复: {response}")
            print(f"\n⏱️ 执行时间: {end_time - start_time:.2f} 秒")

            # 等待一下让追踪数据上传
            time.sleep(2)

            # 获取最新的运行记录
            recent_runs = list(self.client.list_runs(
                project_name=self.project_name,
                limit=1
            ))

            if recent_runs:
                latest_run = recent_runs[0]
                print(f"🔗 追踪记录ID: {latest_run.id}")
                print(f"📊 可以在 LangSmith 控制台查看详细追踪信息")

        except Exception as e:
            print(f"❌ 测试对话失败: {e}")

    def monitor_real_time(self, duration_minutes: int = 5):
        """实时监控运行"""
        print(f"\n👁️ 实时监控 ({duration_minutes} 分钟)")
        print("=" * 80)
        print("按 Ctrl+C 停止监控...")

        start_time = datetime.now()
        last_run_count = 0

        try:
            while (datetime.now() - start_time).seconds < duration_minutes * 60:
                try:
                    runs = list(self.client.list_runs(
                        project_name=self.project_name,
                        start_time=start_time
                    ))

                    current_run_count = len(runs)
                    if current_run_count > last_run_count:
                        new_runs = current_run_count - last_run_count
                        latest_run = runs[0] if runs else None

                        if latest_run:
                            print(f"🆕 新运行: {latest_run.name} - {latest_run.status}")
                            if latest_run.status == "error":
                                print(f"   ❌ 错误: {latest_run.error[:60]}...")

                        last_run_count = current_run_count

                    time.sleep(2)  # 每2秒检查一次

                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            print("\n监控已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LangSmith 调试和监控工具")
    parser.add_argument("command", choices=[
        "list", "details", "performance", "test", "monitor"
    ], help="要执行的命令")

    parser.add_argument("--run-id", help="运行ID (用于 details 命令)")
    parser.add_argument("--limit", type=int, default=10, help="记录数量限制 (用于 list 命令)")
    parser.add_argument("--hours", type=int, default=24, help="分析时间范围小时数 (用于 performance 命令)")
    parser.add_argument("--input", help="测试输入 (用于 test 命令)")
    parser.add_argument("--user-id", default="debug_user", help="用户ID (用于 test 命令)")
    parser.add_argument("--duration", type=int, default=5, help="监控时长分钟数 (用于 monitor 命令)")

    args = parser.parse_args()

    debugger = LangSmithDebugger()

    if args.command == "list":
        debugger.list_recent_runs(args.limit)
    elif args.command == "details":
        if not args.run_id:
            print("❌ 请提供 --run-id 参数")
            sys.exit(1)
        debugger.get_run_details(args.run_id)
    elif args.command == "performance":
        debugger.analyze_performance(args.hours)
    elif args.command == "test":
        if not args.input:
            print("❌ 请提供 --input 参数")
            sys.exit(1)
        debugger.run_test_conversation(args.input, args.user_id)
    elif args.command == "monitor":
        debugger.monitor_real_time(args.duration)

if __name__ == "__main__":
    main()