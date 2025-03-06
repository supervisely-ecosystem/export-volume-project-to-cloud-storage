import os
from dotenv import load_dotenv

import supervisely as sly

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()

TASK_ID = sly.env.task_id()
TEAM_ID = sly.env.team_id()
PROJECT_ID = sly.env.project_id()

PROJECT = api.project.get_info_by_id(PROJECT_ID)
PROJECT_NAME = PROJECT.name

PROVIDER = os.getenv("modal.state.provider")
BUCKET_NAME = os.getenv("modal.state.bucketName")
if BUCKET_NAME == "" or BUCKET_NAME is None:
    raise ValueError("Bucket name is undefined")

EXPORT_FORMAT = os.getenv("modal.state.format", "sly")
SEGMENTATION_TYPE = os.getenv("modal.state.segmentation", "instance")

DATA_DIR_NAME = os.getenv("SLY_APP_DATA_DIR")
STORAGE_DIR = sly.app.get_data_dir()
