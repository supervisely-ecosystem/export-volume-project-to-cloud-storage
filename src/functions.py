import os

import supervisely as sly
import src.globals as g


def validate_remote_storage_path(api, project_name):
    remote_path = api.remote_storage.get_remote_path(
        provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=""
    )
    remote_paths = api.remote_storage.list(
        path=remote_path, recursive=False, files=False, folders=True
    )
    remote_folders = [item.get("name") for item in remote_paths]
    res_project_name = project_name
    while res_project_name in remote_folders:
        res_project_name = sly._utils.generate_free_name(
            used_names=remote_folders, possible_name=project_name
        )
    if res_project_name != project_name:
        sly.logger.warn(
            f"Project with name: {project_name} already exists in bucket, project has been renamed to {res_project_name}"
        )
    return res_project_name


def upload_volume_project_to_storage(
    api, local_project_dir, remote_project_path, remote_project_name
):
    local_project_paths = []
    remote_project_paths = []
    for dirpath, _, filenames in os.walk(local_project_dir):
        for filename in filenames:
            local_path = os.path.join(dirpath, filename)
            local_project_paths.append(local_path)

            remote_dir_name = dirpath
            if remote_dir_name.startswith(g.DATA_DIR_NAME):
                remote_dir_name = "".join(remote_dir_name.split(f"{g.DATA_DIR_NAME}/", 1))
            if remote_dir_name == g.PROJECT_NAME:
                remote_dir_name = ""
            elif remote_dir_name.startswith(g.PROJECT_NAME):
                remote_dir_name = "".join(remote_dir_name.split(f"{g.PROJECT_NAME}/", 1))

            remote_path = os.path.join(remote_project_path, remote_dir_name, filename)
            remote_project_paths.append(remote_path)

    progress = sly.Progress(
        message=f'Uploading to "{g.PROVIDER}://{g.BUCKET_NAME}/{remote_project_name}"',
        total_cnt=len(local_project_paths),
    )
    for local_path, remote_path in zip(local_project_paths, remote_project_paths):
        api.remote_storage.upload_path(
            local_path=local_path,
            remote_path=remote_path,
        )
        progress.iter_done_report()

    remote_project_dir = api.remote_storage.get_remote_path(
        g.PROVIDER, g.BUCKET_NAME, remote_project_name
    )
    sly.logger.info(f"✅Project has been successfully exported to {remote_project_dir}")
