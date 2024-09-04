import click

from cap2geojson import __version__, transform as transform_to_geojson


@click.group()
@click.version_option(version=__version__)
def cli():
    """cap2geojson: the tool to convert CAP alerts to GeoJSON"""

    pass


@click.command()
@click.pass_context
@click.argument("cap_xml", type=click.File(mode="r", errors="ignore"))
def transform(ctx, cap_xml) -> None:
    """Convert a CAP alert XML file to GeoJSON"""
    cap = cap_xml.read()
    filename = cap_xml.name.split(".")[0] + ".geojson"

    try:
        result = transform_to_geojson(cap)
        # Write the contents to a file
        with open(filename, "w") as f:
            f.write(result)
        click.echo(f"GeoJSON file written to {filename}")
    except Exception as e:
        click.echo(f"Error: {e}")
        ctx.exit(1)


cli.add_command(transform)
