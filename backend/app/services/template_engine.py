"""Jinja2 模板引擎封装"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


class TemplateEngine:
    """加载和渲染 Jinja2 SQL 模板"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = str(Path(__file__).parent.parent / "templates")
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            keep_trailing_newline=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)