#!/usr/bin/env python3
"""
LangSmith 项目设置工具

自动创建或切换 LangSmith 项目
支持交互式和命令行模式
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

def list_projects():
    """列出所有可用项目"""
    try:
        client = Client(
            api_key=os.getenv("LANGCHAIN_API_KEY"),
            api_url=os.getenv("LANGCHAIN_ENDPOINT")
        )

        projects = list(client.list_projects())
        if not projects:
            print("📭 没有找到任何项目")
            return []

        print("📋 可用的 LangSmith 项目:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project.name} (ID: {project.id[:8]}...)")

        return projects
    except Exception as e:
        print(f"❌ 获取项目列表失败: {e}")
        return []

def create_project(project_name: str, quiet: bool = False):
    """创建新项目"""
    try:
        client = Client(
            api_key=os.getenv("LANGCHAIN_API_KEY"),
            api_url=os.getenv("LANGCHAIN_ENDPOINT")
        )

        project = client.create_project(project_name)
        if not quiet:
            print(f"✅ 项目 '{project_name}' 创建成功 (ID: {project.id})")
        return project
    except Exception as e:
        if not quiet:
            print(f"❌ 创建项目失败: {e}")
        return None

def quick_setup(project_name: str = "YiYu"):
    """快速设置默认项目"""
    print(f"🚀 快速创建 LangSmith 项目: {project_name}")

    # 检查配置
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("❌ 请先在 .env 文件中配置 LANGCHAIN_API_KEY")
        return False

    # 创建项目
    project = create_project(project_name, quiet=False)
    if project:
        # 更新环境配置
        if update_env_project(project_name):
            print(f"🎉 项目 '{project_name}' 设置完成！")
            print("📊 现在可以在 LangSmith 中追踪对话数据了")
            return True
    return False

def update_env_project(project_name: str):
    """更新 .env 文件中的项目名称"""
    env_file = ".env"

    if not os.path.exists(env_file):
        print(f"❌ 文件 {env_file} 不存在")
        return False

    try:
        # 读取现有内容
        with open(env_file, 'r') as f:
            lines = f.readlines()

        # 更新项目名称
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("LANGCHAIN_PROJECT="):
                lines[i] = f"LANGCHAIN_PROJECT={project_name}\n"
                updated = True
                break

        # 如果没有找到该行，添加到文件末尾
        if not updated:
            lines.append(f"LANGCHAIN_PROJECT={project_name}\n")

        # 写回文件
        with open(env_file, 'w') as f:
            f.writelines(lines)

        print(f"✅ 已更新 {env_file} 中的项目名称为: {project_name}")
        return True
    except Exception as e:
        print(f"❌ 更新 {env_file} 失败: {e}")
        return False

def interactive_mode():
    """交互式模式"""
    print("🔧 LangSmith 项目设置工具")
    print("=" * 50)

    # 检查配置
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("❌ 请先在 .env 文件中配置 LANGCHAIN_API_KEY")
        sys.exit(1)

    current_project = os.getenv("LANGCHAIN_PROJECT", "YiYu")
    print(f"📊 当前项目: {current_project}")

    # 列出所有项目
    projects = list_projects()
    existing_names = [p.name for p in projects]

    print(f"\n🎯 选择操作:")
    print("1. 使用现有项目")
    print("2. 创建新项目")
    print("3. 查看当前配置")

    try:
        choice = input("\n请选择 (1-3): ").strip()
    except KeyboardInterrupt:
        print("\n👋 操作已取消")
        return

    if choice == "1":
        # 使用现有项目
        if not projects:
            print("❌ 没有可用的现有项目")
            return

        print(f"\n选择现有项目:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project.name}")

        try:
            project_choice = input(f"请选择项目 (1-{len(projects)}): ").strip()
            project_index = int(project_choice) - 1

            if 0 <= project_index < len(projects):
                selected_project = projects[project_index]
                update_env_project(selected_project.name)
                print(f"✅ 已切换到项目: {selected_project.name}")
            else:
                print("❌ 无效的选择")
        except ValueError:
            print("❌ 请输入有效的数字")

    elif choice == "2":
        # 创建新项目
        print(f"\n创建新项目:")
        project_name = input("项目名称: ").strip()

        if not project_name:
            print("❌ 项目名称不能为空")
            return

        if project_name in existing_names:
            print(f"⚠️ 项目 '{project_name}' 已存在")
            overwrite = input("是否切换到该项目? (y/N): ").strip().lower()
            if overwrite == 'y':
                update_env_project(project_name)
                print(f"✅ 已切换到现有项目: {project_name}")
            return

        # 创建新项目
        project = create_project(project_name)
        if project:
            update_env_project(project_name)
            print(f"✅ 新项目 '{project_name}' 设置完成")

    elif choice == "3":
        # 查看当前配置
        print(f"\n📋 当前配置:")
        print(f"  API Key: {'已配置' if api_key else '未配置'}")
        print(f"  Endpoint: {os.getenv('LANGCHAIN_ENDPOINT')}")
        print(f"  Project: {current_project}")
        print(f"  Tracing: {os.getenv('LANGCHAIN_TRACING_V2')}")

    else:
        print("❌ 无效的选择")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="LangSmith 项目设置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python setup_langsmith_project.py              # 交互式模式
  python setup_langsmith_project.py --quick       # 快速创建 YiYu 项目
  python setup_langsmith_project.py --quick --project MyProject  # 创建指定项目
  python setup_langsmith_project.py --list       # 列出所有项目
        """
    )

    parser.add_argument("--quick", action="store_true",
                       help="快速创建默认项目 (YiYu)")
    parser.add_argument("--project", type=str, default="YiYu",
                       help="指定项目名称 (默认: YiYu)")
    parser.add_argument("--list", action="store_true",
                       help="列出所有可用项目")
    parser.add_argument("--quiet", action="store_true",
                       help="静默模式，减少输出")

    args = parser.parse_args()

    # 检查基本配置
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key and not args.list:
        print("❌ 请先在 .env 文件中配置 LANGCHAIN_API_KEY")
        sys.exit(1)

    try:
        if args.list:
            # 列出项目模式
            projects = list_projects()
            if not projects:
                print("📭 没有找到任何项目")
            else:
                print(f"📋 找到 {len(projects)} 个项目:")
                for i, project in enumerate(projects, 1):
                    print(f"  {i}. {project.name} (ID: {project.id[:8]}...)")

        elif args.quick:
            # 快速创建模式
            success = quick_setup(args.project)
            sys.exit(0 if success else 1)

        else:
            # 交互式模式
            interactive_mode()

    except KeyboardInterrupt:
        print("\n👋 操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()