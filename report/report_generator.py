import os
import logging
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

# Настройка логирования
DEFAULT_LOG_LEVEL = logging.INFO
logging.basicConfig(level=DEFAULT_LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_report(inactive_items, output_filename="tripster_report.pdf"):
    """
    Generates a PDF report of inactive Tripster widgets and deeplinks using WeasyPrint.

    Args:
        inactive_items (list): A list of dictionaries, where each dictionary
                               represents an inactive widget or deeplink.
        output_filename (str): The name of the output PDF file.
    Returns:
        str: The path to the generated PDF file.
    """
    try:
        logging.info(f"Генерация отчета с использованием WeasyPrint: {output_filename}")

        # Configure Jinja2 environment
        template_dir = os.path.dirname(os.path.abspath(__file__))  # Use the directory of the script
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('report_template.html')

        # Prepare data for the template
        report_data = {
            'total_analyzed': len(inactive_items),
            'total_inactive': len(inactive_items),
            'inactive_items': inactive_items
        }

        # Render the HTML template with the data
        html_content = template.render(report_data)

        # Convert the HTML content to PDF using WeasyPrint
        HTML(string=html_content, base_url=template_dir).write_pdf(output_filename)

        logging.info(f"Отчет успешно сгенерирован: {output_filename}")
        return output_filename  # Return the report path

    except Exception as e:
        logging.error(f"Ошибка при генерации отчета: {e}")
        return None  # Return None in case of an error


if __name__ == '__main__':
    # Example usage:
    inactive_items = [
        {'post_title': 'My Trip to Paris', 'link_type': 'widget', 'exp_id': '123', 'exp_title': 'Eiffel Tower Tour', 'link_status': 'inactive', 'inactivity_reason': 'Deleted from Tripster'},
        {'post_title': 'Best Restaurants in Rome', 'link_type': 'deeplink', 'exp_id': None, 'anchor': 'Best Restaurants', 'link_status': 'inactive', 'inactivity_reason': '404 Error'}
    ]
    report_path = generate_report(inactive_items)
    if report_path:
        print(f"Report generated at: {report_path}")
    else:
        print("Report generation failed.")