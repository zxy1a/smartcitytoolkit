from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_report_html(submission: dict, recommendation: dict, cases: list) -> str:
    template = env.get_template("report_template.html")

    html_content = template.render(
        submission=submission,
        recommendation=recommendation,
        cases=cases
    )
    return html_content

def save_html_report(html_str: str, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_str)
