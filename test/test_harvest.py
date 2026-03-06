"""Tests for the HERMES plugin metadata harvesting from this project."""

import pathlib
import pytest
import toml
from hermes_toml.harvest import TomlHarvestPlugin


# Path to this project's root directory
PROJECT_ROOT = pathlib.Path(__file__).parent.parent


class TestTomlHarvestFromProject:
    """Test that the HERMES toml harvest plugin can extract metadata from pyproject.toml."""

    def test_reads_project_name(self):
        data = TomlHarvestPlugin.read_from_toml(PROJECT_ROOT / "pyproject.toml")
        assert data["name"] == "hermes-plugin-test"

    def test_reads_project_version(self):
        data = TomlHarvestPlugin.read_from_toml(PROJECT_ROOT / "pyproject.toml")
        assert data["version"] == "0.1.0"

    def test_reads_project_description(self):
        data = TomlHarvestPlugin.read_from_toml(PROJECT_ROOT / "pyproject.toml")
        assert "description" in data
        assert len(data["description"]) > 0

    def test_reads_author(self):
        data = TomlHarvestPlugin.read_from_toml(PROJECT_ROOT / "pyproject.toml")
        assert "author" in data
        author = data["author"]
        assert author.get("@type") == "Person"
        assert "name" in author or ("givenName" in author or "lastName" in author)

    def test_reads_runtime_platform(self):
        data = TomlHarvestPlugin.read_from_toml(PROJECT_ROOT / "pyproject.toml")
        assert "runtimePlatform" in data
        assert data["runtimePlatform"].startswith("Python")

    def test_reads_keywords(self):
        data = TomlHarvestPlugin.read_from_toml(PROJECT_ROOT / "pyproject.toml")
        assert "keywords" in data
        assert "hermes" in data["keywords"]


class TestTomlHarvestWithCustomData:
    """Test the HERMES toml harvest plugin with custom TOML data."""

    @pytest.fixture()
    def toml_file(self, tmp_path):
        fn = tmp_path / "test.toml"
        return fn

    @pytest.mark.parametrize("in_data, expected_key, expected_value", [
        ({"project": {"name": "my-project"}}, "name", "my-project"),
        ({"project": {"version": "1.2.3"}}, "version", "1.2.3"),
        ({"project": {"description": "A test project"}}, "description", "A test project"),
        ({"project": {"requires-python": ">=3.10"}}, "runtimePlatform", "Python >=3.10"),
        ({"project": {"keywords": ["test", "hermes"]}}, "keywords", ["test", "hermes"]),
    ])
    def test_harvest_field(self, toml_file, in_data, expected_key, expected_value):
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump(in_data, f)
        result = TomlHarvestPlugin.read_from_toml(str(toml_file))
        assert result[expected_key] == expected_value

    def test_harvest_single_author_dict(self, toml_file):
        in_data = {"project": {"authors": {"givenName": "Jane", "lastName": "Doe"}}}
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump(in_data, f)
        result = TomlHarvestPlugin.read_from_toml(str(toml_file))
        assert result["author"]["@type"] == "Person"
        assert result["author"]["givenName"] == "Jane"

    def test_harvest_multiple_authors_list(self, toml_file):
        in_data = {"project": {"authors": [{"givenName": "Jane"}, {"givenName": "John"}]}}
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump(in_data, f)
        result = TomlHarvestPlugin.read_from_toml(str(toml_file))
        assert isinstance(result["author"], list)
        assert len(result["author"]) == 2
        assert all(p["@type"] == "Person" for p in result["author"])

    def test_harvest_author_from_string(self, toml_file):
        in_data = {"project": {"authors": ["Jane Doe <jane@example.com>"]}}
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump(in_data, f)
        result = TomlHarvestPlugin.read_from_toml(str(toml_file))
        assert result["author"]["name"] == "Jane Doe"
        assert result["author"]["email"] == "jane@example.com"

    def test_harvest_empty_toml(self, toml_file):
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump({}, f)
        result = TomlHarvestPlugin.read_from_toml(str(toml_file))
        assert result == {}

    def test_harvest_raises_when_both_tables_present(self, toml_file):
        in_data = {
            "project": {"name": "my-project"},
            "tool": {"poetry": {"name": "my-project"}},
        }
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump(in_data, f)
        with pytest.raises(ValueError):
            TomlHarvestPlugin.read_from_toml(str(toml_file))

    def test_harvest_poetry_table(self, toml_file):
        in_data = {"tool": {"poetry": {"name": "my-poetry-project", "version": "2.0.0"}}}
        with open(toml_file, "w", encoding="utf-8") as f:
            toml.dump(in_data, f)
        result = TomlHarvestPlugin.read_from_toml(str(toml_file))
        assert result["name"] == "my-poetry-project"
        assert result["version"] == "2.0.0"


class TestTomlHarvestPluginHelpers:
    """Test TomlHarvestPlugin helper class methods."""

    @pytest.mark.parametrize("in_data, expected", [
        ({"givenName": "Tom"}, {"givenName": "Tom"}),
        ({"a": "b"}, {}),
        ({"givenName": "Tom", "a": "b"}, {"givenName": "Tom"}),
        ({}, {}),
    ])
    def test_remove_forbidden_keys(self, in_data, expected):
        assert TomlHarvestPlugin.remove_forbidden_keys(in_data) == expected

    @pytest.mark.parametrize("in_data, expected", [
        ({"givenName": "Tom"}, {"givenName": "Tom", "@type": "Person"}),
        ({}, None),
        ([], None),
        ([{"givenName": "Tom"}], {"givenName": "Tom", "@type": "Person"}),
        (
            [{"givenName": "Tom"}, {"givenName": "Jane"}],
            [{"givenName": "Tom", "@type": "Person"}, {"givenName": "Jane", "@type": "Person"}],
        ),
    ])
    def test_handle_different_possibilities_for_persons(self, in_data, expected):
        assert TomlHarvestPlugin.handle_different_possibilities_for_persons(in_data) == expected

    @pytest.mark.parametrize("in_data", [15, None])
    def test_handle_person_in_unknown_format_raises(self, in_data):
        with pytest.raises(ValueError):
            TomlHarvestPlugin.handle_person_in_unknown_format(in_data)
