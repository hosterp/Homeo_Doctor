from odoo import models, fields, api
from odoo.http import request


class DoctorLabReportWizard(models.TransientModel):
    _name = 'doctor.lab.report.wizard'
    _description = 'Doctor Lab Report Wizard'

    from_date = fields.Date(string="From Date", required=True,default=fields.Date.today)
    to_date = fields.Date(string="To Date", required=True,default=fields.Date.today)
    mode_pay = fields.Selection([('cash', 'Cash'),
                                 ('credit', 'Credit'),
                                 ('card', 'Card'),
                                 ('cheque', 'Cheque'),
                                 ('upi', 'UPI'), ], string='Payment Method')
    bill_type = fields.Selection([
        ('op', 'OP'), ('admitted', 'Admitted Patient'), ('others', 'Others')], string="Bill Type")

    def action_generate_report(self):
        domain = [
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
        ]

        # Add optional filters if values are set
        if self.mode_pay:
            domain.append(('mode_of_payment', '=', self.mode_pay))

        if self.bill_type:
            domain.append(('bill_type', '=', self.bill_type))

        # Search using the dynamic domain
        lab_reports = self.env['doctor.lab.report'].search(domain)

        # Prepare data for the report
        report_data = []
        for report in lab_reports:
            report_data.append({
                'sl_no': report.id,
                'patient_name': report.patient_name,
                'mrd_op_no': report.user_ide.display_name,
                'total_bill_amount': report.total_bill_amount,
                # 'ip_no': report.patient_id.id  # Assuming patient_id is the IP No.
            })

        # Generate the PDF report using the updated method
        return self._generate_pdf_report(report_data)

    def _generate_pdf_report(self, report_data):
        # Use the QWeb report template to render the data
        return self.env.ref('homeo_doctor.report_doctor_lab_report_pdf').report_action(self, data={
            'report_data': report_data})

    def action_download_excel(self):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/doctor_lab_report/download_excel?from_date={self.from_date}&to_date={self.to_date}',
            'target': 'self',
        }
