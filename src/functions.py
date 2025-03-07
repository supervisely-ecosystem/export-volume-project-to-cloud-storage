import os
from pathlib import Path

import numpy as np

import src.globals as g
import supervisely as sly
from supervisely.convert.volume.nii.nii_volume_helper import PlanePrefix


def validate_remote_storage_path(api: sly.Api, project_name: str) -> str:
    remote_path = api.remote_storage.get_remote_path(
        provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=""
    )
    remote_paths = api.storage.list(
        g.TEAM_ID, path=remote_path, recursive=False, include_files=False, include_folders=True
    )
    remote_folders = [item.name for item in remote_paths if item.is_dir]
    res_project_name = project_name
    while res_project_name in remote_folders:
        res_project_name = sly.generate_free_name(
            used_names=remote_folders, possible_name=project_name
        )
    if res_project_name != project_name:
        sly.logger.warning(
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
            team_id=g.TEAM_ID,
        )
        progress.iter_done_report()

    remote_project_dir = api.remote_storage.get_remote_path(
        g.PROVIDER, g.BUCKET_NAME, remote_project_name
    )
    sly.logger.info(f"✅Project has been successfully exported to {remote_project_dir}")


def convert_nrrd_to_nifti(nrrd_path: str, nifti_path: str) -> None:
    """
    Convert a NRRD volume to NIfTI format.
    Preserve the original header information.

    Args:
        nrrd_path (str): Path to the input NRRD file.
        nifti_path (str): Path to the output NIfTI file.
    """

    import SimpleITK as sitk

    img = sitk.ReadImage(nrrd_path)
    sitk.WriteImage(img, nifti_path)


def convert_volume_project(local_project_dir: str) -> str:
    """
    Convert a volume project to NIfTI format.

    Args:
        local_project_dir (str): Path to the local project directory.

    Returns:
        str: Path to the converted project directory.
    """

    # nifti structure type 1:
    #  📂 'dataset 2025-03-05 12:17:16'
    #   ├── 📂 CTChest
    #   │   ├── 🩻 lung.nii.gz
    #   │   └── 🩻 tumor.nii.gz
    #   ├── 🩻 CTChest.nii.gz
    #   └── 🩻 Spine.nii.gz
    # nifti structure type 2 (special case):
    # 📂 'dataset 2025-03-05 12:17:16'
    # ├── 🩻 axl_anatomic_1.nii
    # ├── 🩻 axl_inference_1.nii
    # ├── 🩻 cor_anatomic_1.nii
    # ├── 🩻 cor_inference_1.nii
    # ├── 🩻 sag_anatomic_1.nii
    # └── 🩻 sag_inference_1.nii

    import nibabel as nib

    project_fs = sly.VolumeProject(local_project_dir, mode=sly.OpenMode.READ)
    new_suffix = "_nifti" if g.EXPORT_FORMAT == "nifti" else "_nrrd"
    new_name = f"{project_fs.name}{new_suffix}"
    new_project_dir = Path(local_project_dir).parent / new_name
    new_project_dir.mkdir(parents=True, exist_ok=True)

    meta = project_fs.meta
    color_map = {o.name: [i, o.color] for i, o in enumerate(meta.obj_classes, 1)}

    color_map_to_txt = []
    for name, (idx, color) in color_map.items():
        color_map_to_txt.append(f"{idx} {name} {' '.join(map(str, color))}")
    color_map_txt_path = new_project_dir / "color_map.txt"



    ds_infos = g.api.dataset.get_list(g.PROJECT_ID, recursive=True)

    for ds in project_fs.datasets:
        ds: sly.VolumeDataset

        ds_name = ds.name
        if "/" in ds_name:
            ds_name = ds.name.split("/")[-1]
        curr_ds_info = next(info for info in ds_infos if info.name == ds_name)

        ds_path = new_project_dir / ds.name
        ds_path.mkdir(parents=True, exist_ok=True)

        ds_structure_type = 1
        prefixes = [PlanePrefix.AXIAL, PlanePrefix.CORONAL, PlanePrefix.SAGITTAL]
        if all(name[:3] in prefixes for name in ds.get_items_names()):
            ds_structure_type = 2

        if ds_structure_type == 2:
            if not sly.fs.file_exists(color_map_txt_path):
                with open(color_map_txt_path, "w") as f:
                    f.write("\n".join(color_map_to_txt))
                sly.logger.info(f"Color map saved to {color_map_txt_path}")

        for name in ds.get_items_names():
            volume_path = ds.get_item_path(name)
            ann_path = ds.get_ann_path(name)
            ann_json = sly.json.load_json_file(ann_path)
            ann = sly.VolumeAnnotation.from_json(ann_json, meta)

            short_name = name if not name.endswith(".nrrd") else name[:-5]
            ext = ".nii.gz" if g.EXPORT_FORMAT == "nifti" else ".nrrd"
            res_name = short_name + ext
            res_path = ds_path / res_name

            volume_info = g.api.volume.get_info_by_name(curr_ds_info.id, name)
            use_remote_link = volume_info.meta is not None and "remote_path" in volume_info.meta
            if use_remote_link:
                remote_path = volume_info.meta["remote_path"]
                if g.EXPORT_FORMAT == "nifti" and Path(remote_path).suffix not in [".nii", ".gz"]:
                    use_remote_link = False
                if g.EXPORT_FORMAT == "nrrd" and Path(remote_path).suffix != ".nrrd":
                    use_remote_link = False
            if use_remote_link:
                sly.logger.info(f"Found remote path for {name}")
                sly.logger.info(f"Downloading from remote storage: {remote_path}")

                remote_ext = Path(remote_path).suffixes
                if remote_ext != res_path.suffixes:
                    remote_ext = "".join(Path(remote_path).suffixes)
                    res_path = Path(str(res_path)[: -len(ext)]).with_suffix(remote_ext)
                g.api.storage.download(g.TEAM_ID, remote_path, res_path)
            else:
                sly.logger.info(f"Converting {name} to {g.EXPORT_FORMAT}")
                if g.EXPORT_FORMAT == "nifti":
                    convert_nrrd_to_nifti(volume_path, res_path)
                else:
                    sly.fs.copy_file(volume_path, res_path)

            if len(ann.objects) > 0:
                volume_np, volume_meta = sly.volume.read_nrrd_serie_volume_np(volume_path)

                semantic = np.zeros(volume_np.shape, dtype=np.uint8)
                instances = {}
                cls_to_npy = {
                    obj.obj_class.name: np.zeros(volume_np.shape, dtype=np.uint8)
                    for obj in ann.objects
                }

                mask_dir = ds.get_mask_dir(name)
                geometries_dict = {}

                if mask_dir is not None and sly.fs.dir_exists(mask_dir):
                    mask_paths = sly.fs.list_files(mask_dir, valid_extensions=[".nrrd"])
                    geometries_dict.update(sly.Mask3D._bytes_from_nrrd_batch(mask_paths))

                for sf in ann.spatial_figures:
                    try:
                        geometry_bytes = geometries_dict[sf.key().hex]
                        mask3d = sly.Mask3D.from_bytes(geometry_bytes)
                    except Exception as e:
                        sly.logger.warning(
                            f"Skipping spatial figure for class '{sf.volume_object.obj_class.name}': {str(e)}"
                        )
                        continue

                    if ds_structure_type == 2:
                        if g.SEGMENTATION_TYPE == "semantic":
                            cls_id = color_map[sf.volume_object.obj_class.name][0]
                            semantic[mask3d.data] = cls_id
                        else:
                            cls_id = color_map[sf.volume_object.obj_class.name][0]
                            if cls_id not in instances.keys():
                                instances[cls_id] = np.zeros(volume_np.shape, dtype=np.uint8)
                            idx = instances[cls_id].max() + 1
                            instances[cls_id][mask3d.data] = idx
                    else:
                        val = 1
                        if g.SEGMENTATION_TYPE != "semantic":
                            val = cls_to_npy[sf.volume_object.obj_class.name].max() + 1
                        cls_to_npy[sf.volume_object.obj_class.name][mask3d.data] = val

                def _get_label_path(entity_name, ext):
                    if ds_structure_type == 1:
                        labels_dir = ds_path / short_name
                        labels_dir.mkdir(parents=True, exist_ok=True)
                        label_path = labels_dir / f"{entity_name}{ext}"
                    else:
                        prefix = PlanePrefix(short_name[:3])
                        idx = 1
                        label_path = ds_path / f"{prefix}_inference_{idx}{ext}"
                        while label_path.exists():
                            idx += 1
                            label_path = ds_path / f"{prefix}_inference_{idx}{ext}"

                    return label_path

                def _save_ann(ent_to_npy, ext, volume_meta, affine=None):
                    for entity_name, npy in ent_to_npy.items():
                        label_path = _get_label_path(entity_name, ext)
                        if g.EXPORT_FORMAT == "nifti":
                            label_nifti = nib.Nifti1Image(npy, affine)
                            nib.save(label_nifti, label_path)
                        else:
                            volume_bytes = sly.volume.encode(volume_np=npy, volume_meta=volume_meta)
                            with open(label_path, "wb") as file:
                                file.write(volume_bytes)

                affine = None
                if g.EXPORT_FORMAT == "nifti":
                    nifti = nib.load(res_path)
                    reordered_to_ras_nifti = nib.as_closest_canonical(nifti)
                    affine = reordered_to_ras_nifti.affine

                if ds_structure_type == 1:
                    _save_ann(cls_to_npy, ext, volume_meta, affine)
                else:
                    if g.SEGMENTATION_TYPE == "semantic":
                        _save_ann({ds.name: semantic}, ext, volume_meta, affine)
                    else:
                        _save_ann(instances, ext, volume_meta, affine)

    sly.logger.info(f"Converted project to {g.EXPORT_FORMAT}")

    return str(new_project_dir)
