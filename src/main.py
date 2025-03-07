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
if g.DATASET_ID is not None:
    datasets = [g.DATASET_ID]
else:
    datasets = [d.id for d in g.api.dataset.get_list(g.PROJECT_ID)]

download_volume_project(
    api=g.api,
    project_id=g.PROJECT_ID,
    dest_dir=local_project_dir,
    dataset_ids=datasets if len(datasets) > 0 else None,
    download_volumes=True,
    log_progress=True,
)

if g.EXPORT_FORMAT != "sly":
    local_project_dir = f.convert_volume_project(local_project_dir)


dir_size = sly.fs.get_directory_size(local_project_dir)
progress = sly.tqdm_sly(
    desc=f"Uploading to {remote_project_path}",
    total=dir_size,
    unit="B",
    unit_scale=True,
)
res_path = g.api.storage.upload_directory(
    g.TEAM_ID, local_project_dir, remote_project_path, progress_size_cb=progress
)
sly.logger.info(f"Successfully uploaded to {res_path}")

sly.fs.remove_dir(g.STORAGE_DIR)
