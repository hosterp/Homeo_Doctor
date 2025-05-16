from odoo import models, fields

class BillingReportWizard(models.TransientModel):
    _name = 'billing.report.wizard'
    _description = 'Billing Report Wizard'

    date_from = fields.Date(string='From Date', required=True,default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=True,default=fields.Date.today)

    def action_generate_pdf_report(self):
        records = self.env['general.billing'].search([
            ('bill_date', '>=', self.date_from),
            ('bill_date', '<=', self.date_to),
        ])

        billing_data = []
        for rec in records:
            billing_data.append({
                'bill_number': rec.bill_number,
                'bill_date': rec.bill_date.strftime('%d-%m-%Y %H:%M'),
                'bill_type': rec.bill_type.display_name if rec.bill_type else '',
                'department': rec.department.display_name if rec.department else '',
                'op_category': rec.op_category.display_name if rec.op_category else '',
                'mrd_no': rec.mrd_no.display_name if rec.mrd_no else '',
                'patient_name': rec.patient_name,
                'gender': rec.gender,
                'doctor': rec.doctor.display_name if rec.doctor else '',
                'total_amount': rec.total_amount if rec.total_amount else '',
            })
        data = {
            'date_from': self.date_from.strftime('%d-%m-%Y'),
            'date_to': self.date_to.strftime('%d-%m-%Y'),
            'billing_records': billing_data,
        }
        print(data)  # This will help you debug the structure
        return self.env.ref('homeo_doctor.billing_report_action').report_action(self, data={'data': data})

    def action_generate_excel_report(self):
        base_url = '/general_billing_excel/download'
        url = f"{base_url}?date_from={self.date_from.strftime('%Y-%m-%d %H:%M:%S')}&date_to={self.date_to.strftime('%Y-%m-%d %H:%M:%S')}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

