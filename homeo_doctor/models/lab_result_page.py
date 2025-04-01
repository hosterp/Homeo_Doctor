from odoo import api, fields, models, _




class LabResultPage(models.Model):
    _name='lab.result.page'


    bill_number=fields.Many2one('doctor.lab.report',string='Bill Number')
    patient_id=fields.Many2one(related='bill_number.user_ide',string='UHID')
    patient_name = fields.Char(related='bill_number.patient_name')
    doctor=fields.Many2one('doctor.profile',string='Doctor')
    sample_collected=fields.Datetime(string='Sample collection On')
    lab_collection=fields.Datetime(string='Lab Collection On')
    test_on=fields.Datetime(string='Test On')
