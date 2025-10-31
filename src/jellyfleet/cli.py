import asyncio
import logging
import sys
from pathlib import Path

import click

from jellyfleet.config.loader import load_config
from jellyfleet.db.base import create_database_engine, create_session_factory
from jellyfleet.db.repository import SyncRepository
from jellyfleet.jellyfin.client import JellyfinClient
from jellyfleet.scheduler import Scheduler
from jellyfleet.sync.orchestrator import SyncOrchestrator


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set logging level",
)
@click.pass_context
def cli(ctx: click.Context, config: Path | None, log_level: str) -> None:
    ctx.ensure_object(dict)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    ctx.obj["config_path"] = config
    ctx.obj["log_level"] = log_level


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    default=True,
    help="Perform a dry run without making changes (default: True)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Execute actual changes (overrides --dry-run)",
)
@click.option(
    "--combination",
    "-n",
    help="Specific combination name to sync (default: all)",
)
@click.pass_context
def sync(
    ctx: click.Context, dry_run: bool, force: bool, combination: str | None
) -> None:
    """Run synchronization between Jellyfin instances"""

    if force:
        dry_run = False

    config_path = ctx.obj["config_path"]
    if not config_path:
        click.echo("Error: Configuration file is required", err=True)
        sys.exit(1)

    async def _run_sync():
        engine = None
        try:
            config = await load_config(str(config_path))

            engine = create_database_engine("jellyfleet.db")
            session_factory = create_session_factory(engine)

            with session_factory() as session:
                repository = SyncRepository(session)

                if combination:
                    combinations = [
                        c for c in config.combinations if c.name == combination
                    ]
                    if not combinations:
                        click.echo(
                            f"Error: Combination '{combination}' not found", err=True
                        )
                        sys.exit(1)
                else:
                    combinations = config.combinations

                total_actions = 0
                total_errors = 0

                for combo in combinations:
                    father_server = config.servers[combo.father]

                    for child_config in combo.children:
                        child_server = config.servers[child_config.server]

                        click.echo(f"\nSyncing combination: {combo.name}")
                        click.echo(f"Father: {father_server.url}")
                        click.echo(f"Child: {child_server.url}")
                        click.echo(f"Domains: {', '.join(child_config.domains)}")
                        click.echo(f"Dry run: {dry_run}")
                        click.echo("-" * 50)

                        try:
                            father_client = JellyfinClient(
                                url=str(father_server.url),
                                token=father_server.token,
                            )

                            child_client = JellyfinClient(
                                url=str(child_server.url),
                                token=child_server.token,
                            )

                            orchestrator = SyncOrchestrator(
                                father_client=father_client,
                                child_client=child_client,
                                repository=repository,
                                combination_name=f"{combo.name}-{child_config.server}",
                                domains=[
                                    domain.value for domain in child_config.domains
                                ],
                            )

                            sync_run = await orchestrator.run_sync(dry_run=dry_run)

                            click.echo(f"Status: {sync_run.status}")
                            click.echo(f"Actions: {sync_run.actions_count}")
                            if sync_run.details:
                                click.echo(f"Details: {sync_run.details}")
                            if sync_run.error_message:
                                click.echo(f"Error: {sync_run.error_message}")

                            total_actions += sync_run.actions_count
                            if sync_run.status == "failed":
                                total_errors += 1

                        except Exception as err:
                            click.echo(
                                f"Failed to sync {combo.name}-{child_config.server}: {err}",
                                err=True,
                            )
                            total_errors += 1

                click.echo(f"\n{'=' * 50}")
                click.echo(f"Summary: {total_actions} actions, {total_errors} errors")

                if total_errors > 0:
                    sys.exit(1)

        except Exception as err:
            click.echo(f"Error: {err}", err=True)
            sys.exit(1)
        finally:
            if engine is not None:
                engine.dispose()

    asyncio.run(_run_sync())


@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate configuration file"""

    config_path = ctx.obj["config_path"]
    if not config_path:
        click.echo("Error: Configuration file is required", err=True)
        sys.exit(1)

    try:

        async def _validate():
            config = await load_config(str(config_path))
            click.echo("✓ Configuration file is valid")
            click.echo(f"✓ Found {len(config.combinations)} combination(s)")

            for combo in config.combinations:
                total_domains = sum(len(child.domains) for child in combo.children)
                click.echo(
                    f"  - {combo.name}: {total_domains} domain(s) across {len(combo.children)} child/children"
                )

        asyncio.run(_validate())

    except Exception as err:
        click.echo(f"✗ Configuration validation failed: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--limit",
    "-l",
    default=10,
    type=int,
    help="Number of recent sync runs to show",
)
@click.pass_context
def status(ctx: click.Context, limit: int) -> None:
    """Show sync status and recent runs"""

    config_path = ctx.obj["config_path"]
    if not config_path:
        click.echo("Error: Configuration file is required", err=True)
        sys.exit(1)

    try:

        async def _status():
            engine = create_database_engine("jellyfleet.db")
            session_factory = create_session_factory(engine)

            try:
                with session_factory() as session:
                    repository = SyncRepository(session)
                    recent_runs = repository.get_recent_sync_runs(limit)

                    if not recent_runs:
                        click.echo("No sync runs found")
                        return

                    click.echo(f"Recent {len(recent_runs)} sync runs:")
                    click.echo("-" * 80)

                    for run in recent_runs:
                        status_icon = "✓" if run.status == "completed" else "✗"
                        click.echo(
                            f"{status_icon} {run.started_at} | {run.combination_name} | "
                            f"{run.status} | {run.actions_count} actions"
                        )
                        if run.error_message:
                            click.echo(f"  Error: {run.error_message}")
            finally:
                engine.dispose()

        asyncio.run(_status())

    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--interval",
    "-i",
    default="6h",
    help="Sync interval (cron format, e.g., '6h', '0 */6 * * *')",
)
@click.pass_context
def schedule(ctx: click.Context, interval: str) -> None:
    """Start the scheduler for automatic sync runs"""

    config_path = ctx.obj["config_path"]
    if not config_path:
        click.echo("Error: Configuration file is required", err=True)
        sys.exit(1)

    async def _run_scheduler():
        scheduler = Scheduler(str(config_path), interval)

        try:
            await scheduler.start()
            click.echo(f"Scheduler started with interval: {interval}")
            click.echo("Press Ctrl+C to stop")

            while scheduler.is_running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            click.echo("\nStopping scheduler...")
        finally:
            await scheduler.stop()
            click.echo("Scheduler stopped")

    try:
        asyncio.run(_run_scheduler())
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()
