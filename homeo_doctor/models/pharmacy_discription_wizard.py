from odoo import models, fields


class PharmacyDescriptionWizard(models.TransientModel):
    _name = 'pharmacy.description.wizard'
    _description = 'Pharmacy Description Wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)

    def action_generate_report(self):
        # Search records within the date range
        pharmacy_records = self.env['pharmacy.description'].search([
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date)
        ], order='date asc')

        report_data = []
        sl_no = 1

        for rec in pharmacy_records:
            report_data.append({
                'sl_no': sl_no,
                'receipt_no': rec.id,
                'date_time': rec.date.strftime('%Y-%m-%d %H:%M:%S') if rec.date else '',
                'name': rec.name,
                'uhid_id': rec.uhid_id.id,
                'payable_amount': rec.bill_amount,
                'paying_amount': rec.paid_amount,
                'balance_amount': rec.balance,
            })
            sl_no += 1
        data = {
            'from_date': self.from_date.strftime('%d-%m-%Y'),
            'to_date': self.to_date.strftime('%d-%m-%Y'),
            'report_data': report_data,
        }

        return self.env.ref('homeo_doctor.action_report_pharmacy_description').report_action(self, data={'data': data})