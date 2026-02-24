"""Report service."""


class ReportService:
    def __init__(self, api_client):
        self.client = api_client

    def get_report(self, report_id):
        return self.client.get(f"/reports/{report_id}")

    def generate_report(self, params):
        return self.client.post("/reports/generate", data=params)
