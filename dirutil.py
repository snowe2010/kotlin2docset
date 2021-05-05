import os
import shutil


def setup_docset_directories(local_path: str):
    if os.path.exists(local_path):
        print(f'==> Removing file tree in {local_path}')
        shutil.rmtree(local_path, ignore_errors=True)
    print(f'==> Remaking web directories in {local_path}')
    os.makedirs(local_path)


def copy_icon(source_icon_path: str, local_path: str):
    if os.path.exists(source_icon_path):
        print(f'==> Copying icon file from {source_icon_path} to {local_path}')
        shutil.copy(source_icon_path, local_path)
    else:
        print(f'==> Icon file {source_icon_path} does not exist')


def copy_plist(source_plist_path: str, local_path: str):
    if os.path.exists(source_plist_path):
        print(f'==> Copying plist file from {source_plist_path} to {local_path}')
        shutil.copy(source_plist_path, local_path)
    else:
        print(f'==> Plist file {source_plist_path} does not exist')