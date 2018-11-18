import click
from datetime import datetime
import psutil
import subprocess
import re
import sh
import psycopg2
from pathlib import Path
import os
import pyperclip
import shlex
import sys


COLORS = {
    'black': '#011627',
    'blue': '#05668d',
    'white': '#fdfffc',
    'green': '#2ec4b6',
    'red': '#e71d36',
    'yellow': '#ff9f1c',
    'grey': '#7c7c7c',
    'gold': '#efc88b'
}

SUPPORT_TOOLS_DIR = Path('/home/odoo/support/support-tools')
OE_SUPPORT = SUPPORT_TOOLS_DIR / "oe-support.py"
ENVS_DIR = Path('/home/odoo/miniconda3/envs')
DB_PREFIX = 'oe_support_'
VERSION_MAP = {
    8: ['8.0', 'saas-6'],
    9: ['9.0'] + ['saas-%s' % se for se in [7, 8, 9, 10, 11]],
    10: ['10.0'] + ['saas-%s' % se for se in [12, 13, 14, 15]],
    11: ['11.0'] + ['saas-%s' % se for se in [11.1, 11.2, 11.3, 11.4]],
    12: ['12.0'] + ['saas-%s' % se for se in [11.5]],
}
VERSION_MAP = {v: s for (s, vl) in VERSION_MAP.items() for v in vl}  # inverse the map for easier use

@click.group()
@click.pass_context
def cli(ctx):
    """
    My personal commands in the terminal.
    """
    pass

@cli.group()
def i3():
    pass

@cli.command("hello")
@click.option('--name', default="World")
def hello(name):
    click.echo(f"Hello {name}!")

@i3.command("date")
@click.option("--format", default="%Y-%m-%d (%A)")
def date(format):
    click.echo(datetime.now().strftime(format))

@i3.command("time")
@click.option("--format", default="%H:%M")
def time(format):
    click.echo(datetime.now().strftime(format))

@i3.command("mem")
def mem():
    percent=int(psutil.virtual_memory().percent)
    if percent > 80:
        color = COLORS.get('red')
    elif percent > 40:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('green')
    click.echo(f"<span color='{color}'>MEM</span><span color='{COLORS.get('white')}'>{percent:>3}%</span>")

@i3.command("cpu")
def cpu():
    percent=int(psutil.cpu_percent(interval=1))
    if percent > 80:
        color = COLORS.get('red')
    elif percent > 40:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('green')
    click.echo(f"<span color='{color}'>CPU</span><span color='{COLORS.get('white')}'>{percent:>3}%</span>")

@i3.command("volume")
def volume():
    master = subprocess.check_output(['amixer', 'get', 'Master'], universal_newlines=True)
    output = re.search('Mono: [A-z0-9\s]*\[([0-9]*)%\].*\[(on|off)\]', master)
    if output:
        status = output.group(2)
        vol = int(output.group(1))

    headphone = subprocess.check_output(['amixer', 'get', 'Headphone'], universal_newlines=True)
    headphone_status = re.search('Front Left: [A-z,0-9,\s]*\[([0-9]*)%\].*\[([a-z]*)\]', headphone).group(2)

    device = "HEADPHONE" if headphone_status == 'on' else "SPEAKER"
    if vol > 90:
        color = COLORS.get('red')
    elif vol > 50:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('green')
    
    if status == 'off' or vol == 0:
        color = COLORS.get('grey')

    click.echo(f"<span color='{color}'>{device}</span>{'' if status == 'off' else f'{vol:>3}%'}")

@i3.command("battery")
def battery():
    battery = subprocess.check_output(['acpi', '-b'], universal_newlines=True)
    pattern = "Battery 0: (?P<state>\w*), (?P<percent>\d*)%, (?P<hour>\d\d)\:(?P<min>\d\d)\:\d\d [\w\s]+"
    output = re.search(pattern, battery)
    percent = int(output.group('percent'))
    state = output.group('state')
    hour = output.group('hour')
    minute = output.group('min')

    if percent > 80:
        color = COLORS.get('green')
    elif percent > 20:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('red')

    if state != 'Discharging':
        color = COLORS.get('green')
        click.echo(f"<span color='{color}'>CHARGING</span>{percent:>3}% ({hour}:{minute})")
    else:
        click.echo(f"<span color='{color}'>BAT</span>{percent:>3}% ({hour}:{minute})")

@i3.command("disk_usage")
def disk_usage():
    disk = psutil.disk_usage('/')

    if disk.percent > 80:
        color = COLORS.get('red')
    elif disk.percent > 20:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('green')

    free_gb = int(disk.free / (1024 ** 3))
    total_gb = int(disk.total / (1024 ** 3))

    click.echo(f"<span color='{color}'>DISK</span>{int(disk.percent):>3}% ({free_gb}gb)")    

@i3.command("keyboard_layout")
def keyboard_layout():
    out = sh.setxkbmap('-query')
    layout = re.split("\s+", re.split("\n", out.strip())[-1])[-1]
    color = COLORS.get("green") if layout == "us" else COLORS.get("red")
    click.echo(f"<span color='{color}'>{layout}</span>")

@cli.command("change-lockscreen")
@click.option("-r", "--resolution", help="Resolution (3520x1080 default)")
@click.option("-d", "--wallpapers-dir")
def change_lockscreen(resolution, wallpapers_dir):
    if not wallpapers_dir:
        wallpapers_dir = "/home/odoo/Wallpapers"
    if not resolution:
        resolution = "3520x1080"
    cmd = f"betterlockscreen -u {wallpapers_dir} -r {resolution}"
    subprocess.check_call(shlex.split(cmd))

class DBDoesntExistError(Exception):
    pass

def list_database():
    with psycopg2.connect("dbname=postgres").cursor() as cur:
        cur.execute("select datname from pg_database;")
        return [row[0] for row in cur.fetchall()]

def db_name(db):
    dbs = list_database()
    if db in dbs:
        return db
    elif f"oe_support_{db}" in dbs:
        return f"oe_support_{db}"
    raise DBDoesntExistError(f"{db}{f' and oe_support_{db}' if not db.startswith('oe_support') else ''} don't exist.")

def _get_logins(db, limit):
    query = "select login from res_users where active order by id"
    if limit:
        query += f" limit {limit}"
    db = db_name(db)
    with psycopg2.connect(f"dbname={db}").cursor() as cur:
        cur.execute(f"{query};")
        return [row[0] for row in cur.fetchall()]

def _get_admin(db):
    admin_id_query = "select res_id from ir_model_data where module = 'base' and name = 'user_admin';"
    root_id_query = "select res_id from ir_model_data where module = 'base' and name = 'user_root';"
    login_query = "select login from res_users where id = {}"
    db = db_name(db)
    with psycopg2.connect(f"dbname={db}").cursor() as cur:
        # TODO refactor by determining the db version
        cur.execute(admin_id_query)
        admin = cur.fetchall()
        if len(admin)==1:
            cur.execute(login_query.format(admin[0][0]))
            return cur.fetchall()[0][0]
        cur.execute(root_id_query)
        root = cur.fetchall()
        cur.execute(login_query.format(root[0][0]))
        return cur.fetchall()[0][0]

def get_version(db):
    """Return the version of the database in git compatible notation (i.e. 9.0, saas-11, etc.)."""
    query = "select replace((regexp_matches(latest_version, '^\d+\.0|^saas~\d+\.\d+|saas~\d+'))[1], '~', '-') from ir_module_module where name='base'"
    cmd = ['psql','-tAqX', '-d', '%s' % (db,), '-c', query]
    try:
        return subprocess.check_output(cmd).decode('utf-8').replace('\n','')
    except subprocess.CalledProcessError:
        logging.info("Database not present on system, how about you fetch it first, hum ?")
        sys.exit(0)

def db_exists(db):
    dbs = list_database()
    return f"oe_support_{db}" in dbs

@cli.command("support")
@click.argument('db', metavar='<db>')
@click.option('--get-logins', is_flag=True)
@click.option('--get-admin', is_flag=True)
@click.option('--update', '-u', is_flag=True, help="Updates the base module. Useful when custom modules' states are set to 'to remove'.")
@click.option('--vscode', '-v', is_flag=True, help="Debug using vscode. Don't forget to attach the process.")
@click.option('--silent', '-s', is_flag=True, help="Do not show INFO messages in the log.")
@click.option('--restore', '-r', is_flag=True, help="Restore the initial state of the <db>.")
@click.option('--dump', '-d', type=click.Path(), help="Restore a given downloaded [sh] database to the given <db>.")
@click.option('--info', '-i', is_flag=True, help="Shows the metadata of the <db>.")
@click.pass_context
def support(ctx, db, get_logins, get_admin, silent, restore, update, vscode, dump, info):
    if get_logins:
        show_logins(db, None)
        return
    if get_admin:
        show_admin(db)
        return
    if info:
        show_info(db) 
        return
    if dump:
        load_dump(db, dump)
    if not db_exists(db):
        fetch(db)
    start(db, silent, restore, update, vscode)

def load_dump(db, dump_relative_path):
    dump_path = Path.cwd() / dump_relative_path
    cmd = shlex.split(f"{OE_SUPPORT} restore-dump {db} {dump_path.absolute()} --no-start")
    try:
        subprocess.check_call(cmd)
    except Exception as err:
        click.echo(str(err), err=True)
    
def show_info(db):
    cmd = shlex.split(f"{OE_SUPPORT} info {db}")
    subprocess.check_call(cmd)

def fetch(db):
    cmd = shlex.split(f"{OE_SUPPORT} fetch {db} --no-start")
    subprocess.check_call(cmd)

def get_python(db):
    env = VERSION_MAP[get_version(f"{DB_PREFIX}{db}")]
    return ENVS_DIR / str(env) / 'bin/python'

def start(db, silent, restore, update, vscode):
    python = get_python(db)
    server_cmd = shlex.split(f"{OE_SUPPORT} {'restore' if restore else 'start'} {db} {'--update' if update else ''} {'--vscode' if vscode else ''} {'--debug' if silent else ''} --python {str(python)}")
    firefox_cmd = shlex.split(f"firefox http://localhost:8569/web?debug")
    get_admin_cmd = shlex.split(f"perc support {db} --get-admin")
    proc_list = [subprocess.Popen(cmd) for cmd in [server_cmd, firefox_cmd, get_admin_cmd]]
    for proc in proc_list:
        proc.wait()

def show_logins(db, limit):
    """This command prints the logins of <db>."""
    try:
        logins = _get_logins(db, limit)
        click.echo("\n".join(logins))
    except DBDoesntExistError as err:
        click.echo(str(err), err=True)        

def show_admin(db):
    """This command prints the login of the admin of <db>."""
    try:
        admin = _get_admin(db)
        pyperclip.copy(admin)
        click.echo(f"{admin}")
    except DBDoesntExistError as err:
        click.echo(str(err), err=True)
