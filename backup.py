""" Simple backup script which just creates the root structure in an other
folder and syncs everything which recursevely lies within one of the source
folders. For files bigger than a threshold they are first gziped."""

import argparse
import gzip
import os
import shutil
import sys
import threading
from datetime import datetime
import zipfile
import time

now = datetime.now()

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))


def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('-target', nargs=1, required=True,
                        help='Target Backup folder')
    parser.add_argument('-source', nargs='+', required=True,
                        help='Source Files to be added')
    parser.add_argument('-compress', nargs=1,  type=int,
                        help='Gzip threshold in bytes', default=[100000])

    parser.add_argument('-ignore', nargs='+', help='Files and folders to ignore')

    # no input means show me the help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    return parser.parse_args()

def transfer_file(source, target):
    """ Either copy or compress and copies the file """

    try:
        shutil.copy2(source, target)
        print('Copy {}'.format(source))
    except IOError:
        os.makedirs(os.path.dirname(target))
        transfer_file(source, target)


def check_existing_backups(target):
    for path, _, files in os.walk(target):
        n_backup = 0
        for source in files:
            if 'backup' in source:
                n_backup += 1

        if n_backup >= 5:
            times = {}
            for source in files:
                if 'backup' in source:
                    times[os.path.getctime(path+'/'+source)] = path+'/'+source

            os.remove(sorted(times.items())[0][1])
            print(sorted(times.items())[0][1], "deleted")


def sync_root(root, target, ignore):
    for path, _, files in os.walk(root):
        for source in files:
            source = path + '/' + source

            if True not in [True for folder in ignore if folder in source]:
                transfer_file(source, target + '/' + source)



if __name__ == '__main__':
    arg = parse_input()
    print('### Start copy ####')
    target = arg.target[0]+'/backup_'+now.strftime("%m%d%Y")
    ignore = arg.ignore

    start_time = time.time()

    for root in arg.source:
        sync_root(root, target, ignore)

    end_time = time.time()
    print("Execution time :", end_time - start_time)


    if arg.compress[0]:
        print('Compress {}'.format(target))
        zipf = zipfile.ZipFile(target + '.zip', 'w', zipfile.ZIP_DEFLATED)
        zipdir(target, zipf)
        zipf.close()
        shutil.rmtree(target)

    check_existing_backups(arg.target[0])

    print('### Done ###')



