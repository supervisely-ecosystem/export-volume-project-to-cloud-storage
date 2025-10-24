import os
from pathlib import Path

import numpy as np
import nrrd

import src.globals as g
import supervisely as sly
from supervisely.convert.volume.nii import nii_volume_helper as helper
from collections import defaultdict

plane_map = {
    helper.PlanePrefix.AXIAL: "0-0-1",
    helper.PlanePrefix.CORONAL: "0-1-0",
    helper.PlanePrefix.SAGITTAL: "1-0-0",
}
prefixes = [helper.PlanePrefix.AXIAL, helper.PlanePrefix.CORONAL, helper.PlanePrefix.SAGITTAL]


def validate_remote_storage_path(api: sly.Api, folder_name: str) -> str:
    remote_path = api.remote_storage.get_remote_path(
        provider=g.PROVIDER, bucket=g.BUCKET_NAME, path_in_bucket=""
    )
    remote_paths = api.storage.list(
        g.TEAM_ID, path=remote_path, recursive=False, include_files=False, include_folders=True
    )
    remote_folders = [item.name for item in remote_paths if item.is_dir]
    res_folder_name = folder_name
    while res_folder_name in remote_folders:
        res_folder_name = sly.generate_free_name(
            used_names=remote_folders, possible_name=folder_name
        )
    if res_folder_name != folder_name:
        sly.logger.warning(
            f"Folder with name: {folder_name} already exists in bucket, folder has been renamed to {res_folder_name}"
        )
    return res_folder_name


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

    segmentation_type = g.SEGMENTATION_TYPE

    meta = project_fs.meta

    def _find_pixel_values(descr: str) -> int:
        """
        Find the pixel value in the description string.
        """
        lines = descr.split("\n")
        for line in lines:
            if line.strip().startswith(helper.MASK_PIXEL_VALUE):
                try:
                    value_part = line.strip().split(helper.MASK_PIXEL_VALUE)[1]
                    return int(value_part.strip())
                except (IndexError, ValueError):
                    continue
        return None

    mask_pixel_values = {
        obj_class.name: _find_pixel_values(obj_class.description) for obj_class in meta.obj_classes
    }

    color_map = {}
    used_indices = set()

    # First assign original pixel_values (if they exist)
    for obj_class in meta.obj_classes:
        original_pixel_value = mask_pixel_values.get(obj_class.name)
        if original_pixel_value is not None:
            color_map[obj_class.name] = [original_pixel_value, obj_class.color]
            used_indices.add(original_pixel_value)

    # Then assign free indices to classes without original pixel_values
    next_available_idx = 1
    for obj_class in meta.obj_classes:
        if obj_class.name not in color_map:
            # Find the next available index
            while next_available_idx in used_indices:
                next_available_idx += 1

            color_map[obj_class.name] = [next_available_idx, obj_class.color]
            used_indices.add(next_available_idx)
            next_available_idx += 1

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

        if g.EXPORT_FORMAT == "nifti":
            ds_structure_type = 2
            for item_name in ds.get_items_names():
                if not any(prefix in item_name for prefix in prefixes):
                    ds_structure_type = 1
                    break
        else:
            ds_structure_type = 1

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
                direction = np.array(volume_meta["directions"]).reshape(3, 3)
                spacing = np.array(volume_meta["spacing"])
                space_directions = (direction.T * spacing[:, None]).tolist()
                volume_header = {
                    "space": "right-anterior-superior",
                    "space directions": space_directions,
                    "space origin": volume_meta.get("origin", None),
                }
                semantic = np.zeros(volume_np.shape, dtype=np.uint8)
                instances = {}
                cls_to_npy = {
                    obj.obj_class.name: np.zeros(volume_np.shape, dtype=np.uint8)
                    for obj in ann.objects
                }

                custom_data = defaultdict(lambda: defaultdict(float))

                if ds_structure_type == 2:
                    used_labels = set()
                    for fig in ann.figures + ann.spatial_figures:
                        if fig.custom_data:
                            plane = None
                            for key in prefixes:
                                if key in short_name:
                                    plane = key
                                    break
                            plane = plane_map.get(plane, "0-0-1")
                            if plane is not None and plane in fig.custom_data:
                                label_index = color_map[fig.volume_object.obj_class.name][0]
                                for _frame_idx, _data in fig.custom_data[plane].items():
                                    if "score" in _data:
                                        custom_data[_frame_idx][f"Label-{label_index}"] = _data[
                                            "score"
                                        ]
                                        used_labels.add(fig.volume_object.obj_class.name)

                mask_dir = ds.get_mask_dir(name)

                if mask_dir is not None and sly.fs.dir_exists(mask_dir):
                    mask_paths = sly.fs.list_files(mask_dir, valid_extensions=[".nrrd"])
                    nrrd_data_dict = {}
                    for mask_path in mask_paths:
                        key = os.path.basename(mask_path).replace(".nrrd", "")
                        data, _ = nrrd.read(mask_path)
                        nrrd_data_dict[key] = data
                for sf in ann.spatial_figures:
                    class_name = sf.volume_object.obj_class.name

                    try:
                        mask_data = nrrd_data_dict[sf.key().hex]
                        mask3d = sly.Mask3D(mask_data, volume_header=volume_header)
                    except Exception as e:
                        sly.logger.warning(
                            f"Skipping spatial figure {sf.key().hex} for class '{class_name}': {str(e)}"
                        )
                        continue

                    if ds_structure_type == 2:
                        pixel_value = color_map[class_name][0]
                        if segmentation_type == "semantic":
                            semantic[mask3d.data] = pixel_value
                        else:  # instance segmentation
                            if pixel_value not in instances.keys():
                                instances[pixel_value] = np.zeros(volume_np.shape, dtype=np.uint8)
                            idx = instances[pixel_value].max() + 1
                            instances[pixel_value][mask3d.data] = idx
                    else:  # ds_structure_type == 1
                        val = 1
                        if segmentation_type != "semantic":
                            val = cls_to_npy[class_name].max() + 1
                        cls_to_npy[class_name][mask3d.data] = val

                def _get_label_path(entity_name, ext):
                    if ds_structure_type == 1:
                        labels_dir = ds_path / short_name
                        labels_dir.mkdir(parents=True, exist_ok=True)
                        label_path = labels_dir / f"{entity_name}{ext}"
                    else:
                        idx = 1
                        label_path = ds_path / (short_name.replace("anatomic", "inference") + ext)
                        while label_path.exists():
                            idx += 1
                            label_path = ds_path / (
                                short_name.replace("anatomic", "inference") + f"_{idx}" + ext
                            )

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

                volume_affine = nib.as_closest_canonical(nib.load(res_path)).affine

                if ds_structure_type == 1:
                    mapping = cls_to_npy
                else:
                    mapping = instances if segmentation_type != "semantic" else {ds.name: semantic}

                _save_ann(mapping, ext, volume_meta, volume_affine)

                if (
                    ds_structure_type == 2
                    and segmentation_type == "semantic"
                    and len(custom_data) > 0
                ):
                    csv_path = ds_path / f"{short_name}.csv"
                    if "anatomic" in short_name:
                        csv_path = ds_path / f"{short_name.replace('anatomic', 'score')}.csv"
                    with open(csv_path, "w") as f:
                        col_names = [f"Label-{color_map[name][0]}" for name in used_labels]
                        col_names = sorted(col_names, key=lambda x: int(x.split("-")[1]))
                        f.write(",".join(["Layer"] + col_names) + "\n")
                        for layer, scores in custom_data.items():
                            scores_str = [str(scores.get(name, 0.0)) for name in col_names]
                            f.write(",".join([str(layer)] + scores_str) + "\n")

    sly.logger.info(f"Converted project to {g.EXPORT_FORMAT}")
    if g.EXPORT_FORMAT == "nifti":
        sly.fs.remove_dir(local_project_dir)
        os.rename(str(new_project_dir), local_project_dir)
        return local_project_dir
    return str(new_project_dir)


def upload_color_map_txt(local_project_dir: str, remote_project_path: str):
    local_dir = os.path.dirname(local_project_dir)
    local_color_map_path = os.path.join(local_dir, "color_map.txt")
    local_color_map_exists = sly.fs.file_exists(local_color_map_path)
    if not local_color_map_exists:
        sly.logger.warning(f"color_map.txt not found in local path: {local_project_dir}")
        return

    remote_dir = os.path.dirname(remote_project_path)
    remote_color_map_path = os.path.join(remote_dir, "color_map.txt")
    remote_color_map_exists = g.api.storage.exists(g.TEAM_ID, remote_color_map_path)
    if not remote_color_map_exists:
        g.api.storage.upload(g.TEAM_ID, local_color_map_path, remote_color_map_path)
        sly.logger.info(f"Successfully uploaded color_map.txt to {remote_color_map_path}")
    else:
        sly.logger.info(f"color_map.txt already exists: {remote_color_map_path}")
