import os

import supervisely as sly
from supervisely.project.volume_project import download_volume_project

import src.functions as f
import src.globals as g


local_project_dir = os.path.join(g.STORAGE_DIR, g.PROJECT_NAME)

if g.DATASET_ID is not None:
    datasets = [g.DATASET_ID]
    dataset_info = g.api.dataset.get_info_by_id(g.DATASET_ID)
    dataset_name = dataset_info.name

    if g.EXPORT_FORMAT == "nifti" and g.CREATE_PROJECT_FOLDER:
        # Export to <bucket>/<project_name>/<dataset_name>
        remote_dataset_name = f.validate_remote_dataset_path(
            api=g.api, 
            dataset_name=dataset_name, 
            project_name=g.PROJECT_NAME
        )
        remote_path = g.api.remote_storage.get_remote_path(provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=remote_dataset_name)
        remote_base_path = remote_dataset_name
    else:
        # Export to <bucket>/<dataset_name>
        remote_dataset_name = f.validate_remote_dataset_path(
            api=g.api, 
            dataset_name=dataset_name, 
            project_name=None
        )
        remote_path = g.api.remote_storage.get_remote_path(provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=remote_dataset_name)
        remote_base_path = remote_dataset_name
else:
    datasets = [d.id for d in g.api.dataset.get_list(g.PROJECT_ID)]
    remote_project_name = f.validate_remote_storage_path(api=g.api, project_name=g.PROJECT_NAME)
    remote_path = g.api.remote_storage.get_remote_path(provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=remote_project_name)
    remote_base_path = remote_project_name


download_volume_project(
    api=g.api,
    project_id=g.PROJECT_ID,
    dest_dir=local_project_dir,
    dataset_ids=datasets if len(datasets) > 0 else None,
    download_volumes=True,
    log_progress=True,
)

if g.EXPORT_FORMAT != "sly":
    local_project_dir = f.convert_volume_project(local_project_dir, remote_base_path)

if g.DATASET_ID is not None and g.EXPORT_FORMAT == "nifti":
    dataset_folder = os.path.join(local_project_dir, dataset_name)
    if os.path.exists(dataset_folder):
        upload_dir = dataset_folder
    else:
        upload_dir = local_project_dir
else:
    upload_dir = local_project_dir

dir_size = sly.fs.get_directory_size(upload_dir)
progress = sly.tqdm_sly(
    desc=f"Uploading to {remote_path}",
    total=dir_size,
    unit="B",
    unit_scale=True,
)
res_path = g.api.storage.upload_directory(
    g.TEAM_ID, upload_dir, remote_path, progress_size_cb=progress
)

if g.DATASET_ID is not None and g.EXPORT_FORMAT == "nifti":
    f.upload_color_map(local_project_dir, remote_dataset_name)

sly.logger.info(f"Successfully uploaded to {res_path}")

sly.fs.remove_dir(g.STORAGE_DIR)
