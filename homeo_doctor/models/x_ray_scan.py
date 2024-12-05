from odoo import api, fields, models, _

class X_RAY_Scan(models.Model):
    _name = 'scanning.x.ray'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one('patient.reg', string="Patient", required=True)
    age = fields.Integer(string='Age', required=True, related='patient_id.age')
    gender = fields.Selection(string='Gender', related='patient_id.gender')
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", required=True)
    scan_registered_date = fields.Date(string="Registered Date")
    scan_report_date = fields.Date(string="Report Date")
    file_report = fields.Binary(string="Result")
    file_report_name = fields.Char(string="Result")
    investigation = fields.Text(string="Investigation")
    details = fields.Text(string="Details")
    impression = fields.Text(string="Impression")