import click
import json

from cap2geojson import __version__, transform as transform_to_geojson


@click.group()
@click.version_option(version=__version__)
def cli():
    """cap2geojson"""

    pass


@click.command()
@click.pass_context
@click.argument("cap_xml", type=click.File(mode="r", errors="ignore"))
def transform(ctx, cap_xml) -> None:
    """Convert a CAP alert to GeoJSON"""
    cap = cap_xml.read()

    try:
        result = transform_to_geojson(cap)
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}")
        ctx.exit(1)


cli.add_command(transform)
