from odoo import models, fields

class OTManagement(models.Model):
    _name = 'hospital.ot'
    _description = 'Operation Theatre Management'

    patient_id = fields.Many2one('patient.reg', string='Patient', required=True)
    operation_type = fields.Selection([
        ('minor', 'Minor Surgery'),
        ('major', 'Major Surgery')],
        string='Operation Type', required=True)
    doctor_name = fields.Many2one('doctor.profile',string='Doctor Name', required=True)
    operation_date = fields.Datetime(string='Operation Date & Time', required=True)
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')],
        string='Status', default='scheduled')
    remarks = fields.Text(string='Remarks')
