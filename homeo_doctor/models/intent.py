from odoo import models, fields,api


class intent(models.Model):
    _name = 'intent.record'
    _rec_name = 'doctor_name'

    date = fields.Date(default=fields.Date.context_today, readonly=True)
    doctor_name = fields.Many2one('doctor.profile','Doctor Name')
    medicine = fields.Char("Medicine")
    quantity = fields.Integer('Required Quantity')
    urgent = fields.Boolean('Urgent')
    very_urgent = fields.Boolean('Very Urgent')
    normal = fields.Boolean('Normal')
    current_stock = fields.Integer(store=True)

