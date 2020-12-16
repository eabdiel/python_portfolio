# Prog to check if a process is currently running on computer
import subprocess

is_running = False


def process_exists(process_name):
    call = 'TASKLIST', '/FI', f'imagename eq {process_name}'
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())


is_running = process_exists('pycharm64.exe')
if is_running is True:
    print('Process is active')
else:
    print('Process not running')

# Alternatively we can use a dictionary to list all of the running tasks
output = subprocess.check_output(('TASKLIST', '/FO', 'CSV')).decode()
# get rid of extra " and split into lines
output = output.replace('"', '').split('\r\n')
keys = output[0].split(',')
proc_list = [i.split(',') for i in output[1:] if i]
# make dict with proc names as keys and dicts with the extra nfo as values
proc_dict = dict((i[0], dict(zip(keys[1:], i[1:]))) for i in proc_list)
for name, values in sorted(proc_dict.items(), key=lambda x: x[0].lower()):
    print(f'{name}: {values}')
