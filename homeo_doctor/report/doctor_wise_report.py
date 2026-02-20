from odoo import models, fields
from datetime import datetime

class DoctorBillingReportWizard(models.TransientModel):
    _name = 'doctor.billing.report.wizard'
    _description = 'Doctor Billing Report Wizard'

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)

    def generate_report(self):
        return self.env.ref('homeo_doctor.action_doctor_billing_pdf_report').report_action(self, data={
            'from_date': self.from_date,
            'to_date': self.to_date,
        })

    def get_doctor_billing_summary(self, from_date, to_date):
        result = {}

        def set_result(doc, key, amount):
            result.setdefault(doc, {})
            result[doc][key] = result[doc].get(key, 0.0) + amount

        # 1. Consultation (patient.reg)
        consults = self.env['patient.reg'].search([
            ('time', '>=', from_date),
            ('time', '<=', to_date),
            ('status', '=', 'paid'),

        ])
        for rec in consults:
            doctor = rec.doc_name.name if rec.doc_name else 'Unknown'
            set_result(doctor, 'consultation_amount', rec.register_total_amount)

        # 2. Revisit (patient.appointment)
        revisits = self.env['patient.appointment'].search([
            ('appointment_date', '>=', from_date),
            ('appointment_date', '<=', to_date),
            ('status', '=', 'confirmed'),

        ])
        for rec in revisits:
            if rec.doctor_ids:
                for doctor in rec.doctor_ids:
                    fee = doctor.consultation_fee_doctor or 0.0
                    set_result(doctor.name, 'revisit_amount', fee)
            else:
                set_result('Unknown', 'revisit_amount', rec.register_total_amount)

        # for rec in revisits:
        #     doctor = rec.doctor_ids.name if rec.doctor_ids else 'Unknown'
        #     set_result(doctor, 'revisit_amount', rec.register_total_amount)

        # 3. General Billing
        generals = self.env['general.billing'].search([
            ('bill_date', '>=', from_date),
            ('bill_date', '<=', to_date),
            ('status', '=', 'paid')
        ])
        for rec in generals:
            doctor = rec.doctor.name if rec.doctor else 'Unknown'
            set_result(doctor, 'general_amount', rec.total_amount)

        # 4. Lab Billing
        discharge = self.env['discharged.patient.record'].search([
            ('discharge_date', '>=', from_date),
            ('discharge_date', '<=', to_date),


        ])
        for rec in discharge:
            doctor = rec.doctor.name if rec.doctor else 'Unknown'
            set_result(doctor, 'discharge_amount', rec.total_amount)

        labs = self.env['doctor.lab.report'].search([
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('status', '=', 'paid'),

        ])
        for rec in labs:
            doctor = rec.doctor_id.name if rec.doctor_id else 'Unknown'
            set_result(doctor, 'lab_amount', rec.total_bill_amount)

        # 5. Pharmacy Billing
        pharmacies = self.env['pharmacy.description'].search([
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('status', '=', 'paid'),
        ])
        for rec in pharmacies:
            doctor = rec.doctor_name.name if rec.doctor_name else 'Unknown'
            set_result(doctor, 'pharmacy_amount', rec.total_amount)
        ip_part = self.env['ip.part.billing'].search([
            ('bill_date', '>=', from_date),
            ('bill_date', '<=', to_date),
            ('status', '=', 'paid'),
        ])
        for rec in ip_part:
            doctor = rec.doctor.name if rec.doctor else 'Unknown'
            set_result(doctor, 'ip_part_amount', rec.total_amount)

        return result




class DoctorBillingReport(models.AbstractModel):
    _name = "report.homeo_doctor.doctor_billing_pdf_template"
    _description = 'Doctor Billing PDF Report'

    def _get_report_values(self, docids, data=None):
        # Get wizard record using context
        active_id = self.env.context.get('active_id')
        wizard = self.env['doctor.billing.report.wizard'].browse(active_id)

        from_date = data.get('from_date')
        to_date = data.get('to_date')

        report_data = wizard.get_doctor_billing_summary(from_date, to_date)

        total_row = {
            'consultation_amount': 0.0,
            'revisit_amount': 0.0,
            'general_amount': 0.0,
            'lab_amount': 0.0,
            'pharmacy_amount': 0.0,
            'ip_part_amount': 0.0,
            'discharge_amount': 0.0,
        }

        # Loop through each doctor's values and add to column totals
        for values in report_data.values():
            for key in total_row:
                total_row[key] += values.get(key, 0.0)

        # ✅ Now compute overall row_total (sum of all column totals)
        total_row['row_total'] = sum(total_row.values())

        return {
            'doc_ids': [wizard.id],
            'doc_model': 'doctor.billing.report.wizard',
            'data': data,
            'report_data': report_data,
            'total_row': total_row,
        }

