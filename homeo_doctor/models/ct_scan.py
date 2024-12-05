from odoo import api, fields, models, _

class CT_Scan(models.Model):
    _name = 'scanning.ct'

    patient_id = fields.Many2one('patient.reg', string="Patient", required=True)
    age = fields.Integer(string='Age', required=True, related='patient_id.age')
    gender = fields.Selection(string='Gender', related='patient_id.gender')
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", required=True)
    scan_registered_date = fields.Date(string="Registered Date")
    scan_report_date = fields.Date(string="Report Date")
    investigation = fields.Text(string="Investigation")
    details = fields.Text(string="Details")
    impression = fields.Text(string="Impression")