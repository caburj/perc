import click
from datetime import datetime
import psutil
from subprocess import check_output
import re
import sh

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
    master = check_output(['amixer', 'get', 'Master'], universal_newlines=True)
    output = re.search('Mono: [A-z0-9\s]*\[([0-9]*)%\].*\[(on|off)\]', master)
    if output:
        status = output.group(2)
        vol = int(output.group(1))

    headphone = check_output(['amixer', 'get', 'Headphone'], universal_newlines=True)
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
    battery = check_output(['acpi', '-b'], universal_newlines=True)
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

class GetLoginError(Exception):
    pass

def _get_logins(db, limit):
    query = "select login from res_users order by id"
    if limit:
        query += f" limit {limit}" 
    dbout = sh.psql("-l")
    dbs = [re.split("\s*\|\s*", line.strip())[0] for line in re.split("\n", dbout.strip())[4:-6]]
    if db in dbs:
        result = sh.psql("-d", db, "-c", query)
    elif f"oe_support_{db}" in dbs:
        result = sh.psql("-d", f"oe_support_{db}", "-c", query)
    else:
        raise GetLoginError
    return re.split("\n", result.strip())[2:-1]

@cli.command('get-logins')
@click.argument('db', metavar='<db>')
@click.option('--limit', '-l', default=None, help="Limit to one if necessary.")
def get_logins(db, limit):
    """This command prints the logins of <db>."""
    try:
        logins = _get_logins(db, limit)
        click.echo("\n".join(logins))
    except GetLoginError:
        click.echo(f"{db}{f' or oe_support_{db} ' if not db.startswith('oe_support') else ' '}doesn't exist.", err=True)        

@cli.command('get-admin')
@click.argument('db', metavar='<db>')
def get_admin(db):
    """This command prints the login of the admin of <db>."""
    try:
        admin = _get_logins(db, limit=1)[0]
        click.echo(f"{admin}")
    except GetLoginError:
        click.echo(f"{db}{f' or oe_support_{db} ' if not db.startswith('oe_support') else ' '}doesn't exist.", err=True) 