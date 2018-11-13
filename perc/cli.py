import click
from datetime import datetime
import psutil
from subprocess import check_output
import re

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

@cli.command("hello")
@click.option('--name', default="World")
def hello(name):
    click.echo(f"Hello {name}!")

@cli.command("date")
@click.argument("format")
def date(format):
    click.echo(datetime.now().strftime(format))

@cli.command("time")
@click.argument('format')
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
    click.echo(f"<span color='{color}'>{device}</span>{' mute' if status == 'off' else f'{vol:>3}%'}")

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
    elif percent > 50:
        color = COLORS.get('gold')
    else:
        color = COLORS.get('red')

    if state != 'Discharging':
        color = COLORS.get('green')

    click.echo(f"<span color='{color}'>BAT</span>{percent:>3}% ({hour}:{minute})")

