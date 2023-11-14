from odoo import api, fields, models, tools
import odoo.addons

class PatientRegistration(models.Model):
    _name = 'patient.registration'
    _description = 'Patient Registration'

    patient_id = fields.Char(required=True, string="Name")
    address = fields.Char(required=True, string="Address")
    age = fields.Integer(required=True, string="Age")
    phone_number = fields.Char(string="Phone No:",size=12)
    symptoms = fields.Char(required=True, string="Symptom")