"""
basic_task.py - 基础任务创建与执行示例
"""
import asyncio
import os
from honor_agent import HonorAgent
from honor_agent.models import TaskParams


async def main():
    api_key = os.getenv("HONOR_API_KEY", "your-api-key")
    base_url = os.getenv("HONOR_BASE_URL", "http://localhost:8000")
    
    client = HonorAgent(api_key=api_key, base_url=base_url)
    
    task = await client.tasks.create(
        name="数据分析任务",
        description="分析销售数据并生成周报",
        agents=["data_analyst"],
        params=TaskParams(
            data_source="sales_db",
            date_range="last_week"
        )
    )
    
    print(f"✓ 任务创建成功: {task.id}")
    
    result = await client.tasks.run(task_id=task.id)
    
    print(f"✓ 执行状态: {result.status}")
    if result.output:
        print(f"✓ 输出: {result.output}")
    
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
