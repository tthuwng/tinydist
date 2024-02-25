import pytest
from click.testing import CliRunner

from tinydist.cli import cli  # Import your Click CLI group


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_upload(runner):
    result = runner.invoke(cli, ["upload", "./files/file.npz"])
    assert "uploaded successfully" in result.output
    assert result.exit_code == 0
