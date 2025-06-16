import json

class Exporter:
    @staticmethod
    def export_to_csv(data, output_path):
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)

    @staticmethod
    def export_to_json(data, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
