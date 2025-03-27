from email.policy import default

from odoo import api, fields, models, _


class labResultantConfi(models.Model):
    _name = 'lab.resultant.confi'
    _description = 'Lab Resultant Configuration'
    # _rec_name = 'report_reference'
    # _order = 'date desc'

    test_name_bill_code = fields.Char(string='Select Test Name/Bil Code')
    main_group = fields.Char(String='Select Main Group')
    sub_group = fields.Char(string='Select Sub Group')
    test_name = fields.Char(string='Test Name')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    order = fields.Char(string='Order')
    age_from = fields.Integer(string='Age Group From')
    age_to = fields.Integer(string='Age Group To')
    type = fields.Selection([('year','Year'),('month','Month'),('day','Day'),('hour','Hour')],string='Type')
    unit = fields.Char(string='Unit')
    referral_range = fields.Char(string='Referral Range')
    min_val = fields.Char("Min Val")
    max_val = fields.Char("Max Val")
    remarks = fields.Text("Remarks")