#!/usr/bin/env python3
"""
Setup script for local Qdrant installation and configuration.
Supports both Docker and native installation methods.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_docker():
    """Check if Docker is available."""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_qdrant_docker():
    """Setup Qdrant using Docker."""
    print("🐳 设置 Qdrant (Docker 方式)")

    # Docker run command
    cmd = [
        "docker", "run", "-d",
        "--name", "qdrant-memory-agent",
        "-p", "6333:6333",  # HTTP API
        "-p", "6334:6334",  # gRPC API
        "-v", f"{Path.cwd()}/qdrant_storage:/qdrant/storage",
        "qdrant/qdrant:latest"
    ]

    try:
        # Check if container already exists
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=qdrant-memory-agent"],
            capture_output=True, text=True
        )

        if "qdrant-memory-agent" in result.stdout:
            print("✅ Qdrant 容器已存在")
            # Start existing container
            subprocess.run(["docker", "start", "qdrant-memory-agent"], check=True)
        else:
            print("🚀 启动新的 Qdrant 容器...")
            subprocess.run(cmd, check=True)

        print("✅ Qdrant Docker 容器启动成功!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Docker 设置失败: {e}")
        return False

def setup_qdrant_native():
    """Setup Qdrant using native installation."""
    print("🔧 设置 Qdrant (本地安装方式)")

    # For simplicity, we'll provide instructions for manual installation
    print("\n请手动安装 Qdrant:")
    print("1. 访问: https://qdrant.tech/documentation/quick-start/")
    print("2. 下载适用于您系统的 Qdrant 二进制文件")
    print("3. 启动命令: ./qdrant --storage-path ./qdrant_storage")
    print("\n或者使用 pip 安装:")
    print("pip install qdrant-client[fastembed]")

    return False

def wait_for_qdrant(max_retries=30, delay=2):
    """Wait for Qdrant to be ready."""
    print("⏳ 等待 Qdrant 服务启动...")

    url = "http://localhost:6333/health"

    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Qdrant 服务已就绪!")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"   尝试 {i+1}/{max_retries}...")
        time.sleep(delay)

    print("❌ Qdrant 服务启动超时")
    return False

def create_qdrant_collection():
    """Create the conversation memories collection."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams

        client = QdrantClient(url="http://localhost:6333")
        collection_name = "conversation_memories"

        # Check if collection exists
        collections = client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            print(f"✅ Collection '{collection_name}' 已存在")
            return True

        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )

        print(f"✅ 成功创建 Collection: {collection_name}")
        return True

    except Exception as e:
        print(f"❌ 创建 Collection 失败: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Qdrant 本地部署设置")
    print("=" * 40)

    # Check if Qdrant is already running
    try:
        response = requests.get("http://localhost:6333/health", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant 已在运行!")
            create_qdrant_collection()
            return
    except requests.exceptions.RequestException:
        pass

    # Check Docker availability
    if check_docker():
        success = setup_qdrant_docker()
    else:
        print("❌ Docker 未安装或不可用")
        success = setup_qdrant_native()

    if success:
        # Wait for service to be ready
        if wait_for_qdrant():
            # Create collection
            create_qdrant_collection()
            print("\n🎉 Qdrant 设置完成!")
            print("📍 服务地址: http://localhost:6333")
            print("📊 管理界面: http://localhost:6333/dashboard")
        else:
            print("\n❌ Qdrant 服务启动失败，请检查日志")
    else:
        print("\n❌ Qdrant 设置失败，请手动安装")

if __name__ == "__main__":
    main()