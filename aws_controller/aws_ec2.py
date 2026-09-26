from dataclasses import dataclass
from datetime import datetime

import boto3

import config


@dataclass
class Worker:
    instance_id: str
    state: str
    launched_at: datetime


def list_running_workers() -> list[Worker]:
    """查目前這個帳號裡，屬於這個專案、由 controller 自己開出來的 GPU
    worker instance 有哪些（running 或還在開機中的 pending）。

    只看 Project/Role 這兩個 tag（跟 terraform/ec2_worker.tf 打的 tag、
    terraform/iam.tf 裡 TerminateWorkers 權限限制用的是同一組值），不會
    誤動到帳號裡其他跟這個專案無關的 EC2。
    """
    ec2 = boto3.client("ec2", region_name=config.aws_region)

    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": [config.aws_project_tag]},
            {"Name": "tag:Role", "Values": [config.aws_worker_role_tag]},
            {"Name": "instance-state-name", "Values": ["running", "pending"]},
        ]
    )

    workers = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            workers.append(
                Worker(
                    instance_id=instance["InstanceId"],
                    state=instance["State"]["Name"],
                    launched_at=instance["LaunchTime"],
                )
            )
    return workers


if __name__ == "__main__":
    workers = list_running_workers()
    print(f"running workers = {len(workers)}")
    for worker in workers:
        print(f"  {worker.instance_id}  {worker.state}  launched_at={worker.launched_at}")
