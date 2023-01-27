import os

import supervisely as sly
from supervisely.project.volume_project import download_volume_project

import src.functions as f
import src.globals as g


local_project_dir = os.path.join(g.STORAGE_DIR, g.PROJECT_NAME)
remote_project_name = f.validate_remote_storage_path(api=g.api, project_name=g.PROJECT_NAME)

remote_project_path = g.api.remote_storage.get_remote_path(
    provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=remote_project_name
)

datasets = list(g.api.dataset.get_list(g.PROJECT_ID))

download_volume_project(
    api=g.api,
    project_id=g.PROJECT_ID,
    dest_dir=local_project_dir,
    dataset_ids=[dataset.id for dataset in datasets] if len(datasets) > 0 else None,
    download_volumes=True,
    log_progress=True,
)


f.upload_volume_project_to_storage(g.api, local_project_dir, remote_project_path, remote_project_name)

sly.fs.remove_dir(g.STORAGE_DIR)
