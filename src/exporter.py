import json

class Exporter:
    """
    Exporter provides static methods to export data to CSV and JSON formats.
    Methods
    -------
    export_to_csv(data, output_path):
        Exports the provided data to a CSV file at the specified output path.
        Parameters:
            data (list[dict] or pandas.DataFrame): The data to export.
            output_path (str): The file path where the CSV will be saved.
    export_to_json(data, output_path):
        Exports the provided data to a JSON file at the specified output path.
        Parameters:
            data (list[dict] or dict): The data to export.
            output_path (str): The file path where the JSON will be saved.
    """
    @staticmethod
    def export_to_csv(data, output_path):
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)

    @staticmethod
    def export_to_json(data, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
