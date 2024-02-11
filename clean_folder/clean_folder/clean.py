import sys
import shutil
import re
from pathlib import Path


UKRAINIAN_SYMBOLS = 'абвгдеєжзиіїйклмнопрстуфхцчшщьюя'
TRANSLATION = ("a", "b", "v", "g", "d", "e", "je", "zh", "z", "y", "i", "ji", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "ju", "ja")

TRANS = {}

for key, value in zip(UKRAINIAN_SYMBOLS, TRANSLATION):
    TRANS[ord(key)] = value
    TRANS[ord(key.upper())] = value.upper()

def normalize(name: str) -> str:
    name, *extension = name.split('.')
    new_name = name.translate(TRANS)
    new_name = re.sub(r'\W', '_', new_name)
    return f"{new_name}.{'.'.join(extension)}"


files_groups = {
    'images'    : ['JPEG', 'PNG', 'JPG', 'SVG'],
    'video'     : ['AVI', 'MP4', 'MOV', 'MKV'],
    'documents' : ['DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX'],
    'audio'     : ['MP3', 'OGG', 'WAV', 'AMR'],
    'archives'  : ['ZIP', 'GZ', 'TAR'],
    'other'     : []
    # 'folders'   : None
}

all_files_by_group = dict()
for file_group in files_groups.keys():
    all_files_by_group.update({file_group: list()})

extension_group = dict()
for group, extensions in files_groups.items():
    for extension in extensions:
        extension_group.update({extension: group})

folders = list()
unknown = set()
extensions = set()

def get_extensions(file_name):
    return Path(file_name).suffix[1:].upper()

def scan(folder):
    for item in folder.iterdir():
        if item.is_dir():
            if item.name not in list(files_groups.keys()):
                folders.append(item)
                scan(item)
            continue

        extension = get_extensions(file_name=item.name)
        new_name = folder/item.name
        if not extension:
            all_files_by_group['other'].append(new_name)
        else:
            try:
                container = all_files_by_group[extension_group[extension]]
                extensions.add(extension)
                container.append(new_name)
            except KeyError:
                unknown.add(extension)
                all_files_by_group['other'].append(new_name)


def handle_file(path, root_folder, dist):
    target_folder = root_folder/dist
    target_folder.mkdir(exist_ok=True)
    path.replace(target_folder/normalize(path.name))

def handle_archive(path, root_folder, dist):
    target_folder = root_folder / dist
    target_folder.mkdir(exist_ok=True)

    archives_extensions = files_groups['archives']
    archives_extensions = '|'.join(archives_extensions).lower()
    new_name = re.sub(rf'\.({archives_extensions})$', '', path.name)
    new_name = normalize(new_name)

    archive_folder = target_folder / new_name
    archive_folder.mkdir(exist_ok=True)

    try:
        shutil.unpack_archive(str(path.resolve()), str(archive_folder.resolve()))
    except shutil.ReadError:
        archive_folder.rmdir()
        return
    except FileNotFoundError:
        archive_folder.rmdir()
        return
    path.unlink()

def remove_empty_folders(path):
    for item in path.iterdir():
        if item.is_dir():
            remove_empty_folders(item)
            try:
                item.rmdir()
            except OSError:
                pass

def main(folder_path):
    scan(folder_path)

    for group in all_files_by_group.keys():
        for file in all_files_by_group[group]:
            if group == 'archives':
                handle_archive(file, folder_path, group)
            else:
                handle_file(file, folder_path, group)

    remove_empty_folders(folder_path)

    print('------------------------------------')
    for group, files in all_files_by_group.items():
        print(f'{group}:')
        for file in files:
            print(normalize(file.name))
        print('------------------------------------')
    
    print(f'All extensions: {extensions}')
    print('------------------------------------')
    print(f'Unknown extensions: {unknown}')
    print('------------------------------------')
    
    '''print('Folders:')
    for folder in folders:
        print(f'{folder.name}')
    print('------------------------------------')'''

if __name__ == '__main__':
    path = sys.argv[1]

    folder = Path(path)
    print(f'Start in \'{folder.resolve()}\'')
    main(folder.resolve())