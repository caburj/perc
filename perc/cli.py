import click
from datetime import datetime
import psutil
import subprocess
import re
import sh
import psycopg2

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

@click.group()
def cli():
    """
    My personal commands in the terminal.
    """
    pass

@cli.command("hello")
@click.option('--name', default="World")
def hello(name):
    click.echo(f"Hello {name}!")

@cli.command("date")
@click.option("--format", default="%Y-%m-%d (%A)")
def date(format):
    click.echo(datetime.now().strftime(format))

@cli.command("time")
@click.option("--format", default="%H:%M")
def time(format):
    click.echo(datetime.now().strftime(format))

@cli.command("mem")
def mem():
    percent=int(psutil.virtual_memory().percent)
    if percent > 80:
        color = COLORS.get('red')
    elif percent > 40:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('green')
    click.echo(f"<span color='{color}'>MEM</span><span color='{COLORS.get('white')}'>{percent:>3}%</span>")

@cli.command("cpu")
def cpu():
    percent=int(psutil.cpu_percent(interval=1))
    if percent > 80:
        color = COLORS.get('red')
    elif percent > 40:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('green')
    click.echo(f"<span color='{color}'>CPU</span><span color='{COLORS.get('white')}'>{percent:>3}%</span>")

@cli.command("volume")
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

@cli.command("battery")
def battery():
    battery = subprocess.check_output(['acpi', '-b'], universal_newlines=True)
    pattern = "Battery 0: (?P<state>\w*), (?P<percent>\d*)%, (?P<hour>\d\d)\:(?P<min>\d\d)\:\d\d remaining"
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

    click.echo(f"<span color='{color}'>BAT</span>{percent:>3}% ({hour}:{minute})")

@cli.command("disk_usage")
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

@cli.command("keyboard_layout")
def keyboard_layout():
    out = sh.setxkbmap('-query')
    layout = re.split("\s+", re.split("\n", out.strip())[-1])[-1]
    color = COLORS.get("green") if layout == "us" else COLORS.get("red")
    click.echo(f"<span color='{color}'>{layout}</span>")

class GetLoginsError(Exception):
    pass

def list_database(db):
    with psycopg2.connect("dbname=postgres").cursor() as cur:
        cur.execute("select datname from pg_database;")
        return [row[0] for row in cur.fetchall()]

def _get_logins(db, limit):
    query = "select login from res_users order by id"
    if limit:
        query += f" limit {limit}"
    dbs = list_database(db)
    if db in dbs:
        db = db
    elif f"oe_support_{db}" in dbs:
        db = f"oe_support_{db}"
    else:
        raise GetLoginsError(f"{db}{f' and oe_support_{db}' if not db.startswith('oe_support') else ''} don't exist.")
    with psycopg2.connect(f"dbname={db}").cursor() as cur:
        cur.execute(f"{query};")
        return [row[0] for row in cur.fetchall()]

@cli.command('get-logins')
@click.argument('db', metavar='<db>')
@click.option('--limit', '-l', default=None, help="Limit to one if necessary.")
def get_logins(db, limit):
    """This command prints the logins of <db>."""
    try:
        logins = _get_logins(db, limit)
        click.echo("\n".join(logins))
    except GetLoginsError as err:
        click.echo(str(err), err=True)        

@cli.command('get-admin')
@click.argument('db', metavar='<db>')
def get_admin(db):
    """This command prints the login of the admin of <db>."""
    try:
        admin = _get_logins(db, limit=1)[0]
        click.echo(f"{admin}")
    except GetLoginsError as err:
        click.echo(str(err), err=True) 