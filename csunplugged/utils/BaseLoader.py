"""Base loader used to create custom loaders for content."""

import yaml
import mdx_math
import abc
import sys
import re
import os.path
from os import listdir
from verto import Verto
from verto.errors.Error import Error as VertoError
from django.conf import settings
from django.utils.translation import to_locale
from .check_required_files import check_converter_required_files
from .check_glossary_links import check_converter_glossary_links
from utils.errors.CouldNotFindMarkdownFileError import CouldNotFindMarkdownFileError
from utils.errors.VertoConversionError import VertoConversionError
from utils.errors.EmptyMarkdownFileError import EmptyMarkdownFileError
from utils.errors.EmptyYAMLFileError import EmptyYAMLFileError
from utils.errors.InvalidYAMLFileError import InvalidYAMLFileError
from utils.errors.NoHeadingFoundInMarkdownFileError import NoHeadingFoundInMarkdownFileError
from utils.errors.CouldNotFindYAMLFileError import CouldNotFindYAMLFileError


class BaseLoader():
    """Base loader class for individual loaders."""

    def __init__(self, base_path="", structure_dir="structure", content_path="",
                 structure_filename="", lite_loader=False):
        """Create a BaseLoader object.

        Args:
            base_path (str): path to content_root, eg. "topics/content/".
            structure_dir (str): name of directory under base_path storing structure files.
            content_path (str): path within locale/structure dir to content directory, eg. "binary-numbers/unit-plan".
            structure_filename (str): name of yaml file, eg. "unit-plan.yaml".
            lite_loader (bool): Boolean to state whether loader should only
                be loading key content and perform minimal checks."
        """
        self.base_path = base_path
        self.structure_dir = structure_dir
        self.content_path = content_path
        self.structure_filename = structure_filename
        self.lite_loader = lite_loader
        self.setup_md_to_html_converter()

    def get_localised_file(self, language, filename):
        """Get full path to localised version of given file.

        Args:
            language: language code, matching a directory in self.base_path (str).
            filename: path to file from the content directory of the loader (str).

        Returns:
            full path to localised version of given file (str).
        """
        return os.path.join(
            self.get_localised_dir(language),
            filename
        )

    def get_localised_dir(self, language):
        """Return full path to the localised content directory of the loader.

        Args:
            language: language code, matching a directory in self.base_path (str).

        Returns:
            full path to the localised content directory (str).
        """
        return os.path.join(
            self.base_path,
            to_locale(language),
            self.content_path
        )

    @property
    def structure_file_path(self):
        """Return full path to structure yaml file of the loader.

        This assumes that the structure file is located in the same directory
        as self.content_path, but inside the special 'structure' directory
        instead of a language directory.
        """
        return os.path.join(
            self.base_path,
            self.structure_dir,
            self.content_path,
            self.structure_filename
        )

    def setup_md_to_html_converter(self):
        """Create Markdown converter.

        The converter is created with custom processors, html templates,
        and extensions.
        """
        templates = self.load_template_files()
        extensions = [
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.sane_lists",
            "markdown.extensions.tables",
            mdx_math.MathExtension()
        ]
        self.converter = Verto(html_templates=templates, extensions=extensions)

    def convert_md_file(self, md_file_path, config_file_path, heading_required=True, remove_title=True):
        """Return the Verto object for a given Markdown file.

        Args:
            md_file_path: Location of Markdown file to convert (str).
            config_file_path: Path to related the config file (str).
            heading_required: Boolean if the file requires a heading (bool).
            remove_title: Boolean if the file's first heading should be removed (bool).

        Returns:
            VertoResult object

        Raises:
            CouldNotFindMarkdownFileError: when a given Markdown file cannot be found.
            NoHeadingFoundInMarkdownFileError: when no heading can be found in a given
                Markdown file.
            EmptyMarkdownFileError: when no content can be found in a given Markdown
                file.
            VertoConversionError: when a verto StyleError is thrown.
        """
        try:
            # Check file exists
            content = open(md_file_path, encoding="UTF-8").read()
        except FileNotFoundError:
            raise CouldNotFindMarkdownFileError(md_file_path, config_file_path)

        """ Below is a hack to make the image-inline tag not require alt text to be
            given when the language is not in English.
            TODO: Remove this hack once translations are complete.
        """
        directories = md_file_path.split('/')
        if 'en' not in directories:
            processor_argument_overrides = {
                "image-container": {
                    "alt": False
                },
                "image-inline": {
                    "alt": False
                },
                "image-tag": {
                    "alt": False
                }
            }
        else:
            processor_argument_overrides = {
                "image-container": {
                    "alt": True
                },
                "image-inline": {
                    "alt": True
                },
                "image-tag": {
                    "alt": True
                }
            }
        """ End of hack. """

        custom_processors = self.converter.processor_defaults()
        if remove_title:
            custom_processors.add("remove-title")
        settings = {
            "processor_argument_overrides": processor_argument_overrides,
        }
        templates = self.load_template_files()
        extensions = [
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.sane_lists",
            "markdown.extensions.tables",
            mdx_math.MathExtension()
        ]
        self.converter = Verto(
            html_templates=templates,
            extensions=extensions,
            settings=settings,
            processors=custom_processors
        )
        result = None
        try:
            result = self.converter.convert(content)
        except VertoError as e:
            raise VertoConversionError(md_file_path, e) from e

        if heading_required:
            if result.title is None:
                raise NoHeadingFoundInMarkdownFileError(md_file_path)

        if len(result.html_string) == 0:
            raise EmptyMarkdownFileError(md_file_path)

        if not self.lite_loader:
            check_converter_required_files(result.required_files, md_file_path)
            check_converter_glossary_links(result.required_glossary_terms, md_file_path)
        return result

    def log(self, message, indent_amount=0):
        """Output the log message to the load log.

        Args:
            message: Text to display (str).
            indent_amount: Amount of indentation required (int).
        """
        indent = "  " * indent_amount
        text = "{indent}{text}\n".format(indent=indent, text=message)
        sys.stdout.write(text)

    def load_yaml_file(self, yaml_file_path):
        """Load and read given YAML file.

        Args:
            file_path: location of yaml file to read (str).

        Returns:
            Either list or string, depending on structure of given yaml file

        Raises:
            CouldNotFindYAMLFileError: when a given config file cannot be found.
            InvalidYAMLFileError: when a given config file is incorrectly formatted.
            EmptyYAMLFileError: when a give config file is empty.
        """
        try:
            yaml_file = open(yaml_file_path, encoding="UTF-8").read()
        except FileNotFoundError:
            raise CouldNotFindYAMLFileError(yaml_file_path)

        try:
            yaml_contents = yaml.full_load(yaml_file)
        except yaml.YAMLError:
            raise InvalidYAMLFileError(yaml_file_path)

        if yaml_contents is None:
            raise EmptyYAMLFileError(yaml_file_path)

        if isinstance(yaml_contents, (list, dict)) is False:
            raise InvalidYAMLFileError(yaml_file_path)

        return yaml_contents

    def load_template_files(self):
        """Load custom HTML templates for converter.

        Returns:
            templates: dictionary of html templates
        """
        templates = dict()
        template_path = settings.CUSTOM_VERTO_TEMPLATES
        for file in listdir(template_path):
            template_file = re.search(r"(.*?).html$", file)
            if template_file:
                template_name = template_file.groups()[0]
                templates[template_name] = open(template_path + file).read()
        return templates

    @abc.abstractmethod
    def load(self):
        """Abstract method to be implemented by subclasses.

        Raise:
            NotImplementedError: when a user attempts to run the load() method of the
                BaseLoader class.
        """
        raise NotImplementedError("Subclass does not implement this method")  # pragma: no cover
