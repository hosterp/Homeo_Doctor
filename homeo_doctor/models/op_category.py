from odoo import api, fields, models



class OpCategory(models.Model):
    _name = 'op.category'
    _rec_name = 'category_name'



    category_name = fields.Char(string='Category Name')
    code = fields.Char(string='Code')
    parent_category = fields.Char(string='Parent Category')
    ip_link=fields.Selection([('yes','YES'),('no','No')],string='Ip Link')
    have_reg_fee=fields.Selection([('yes','YES'),('no','No')],string='Have Registration Fee?')
    reg_fee=fields.Integer(string='Registration Fee')
    reg_validity=fields.Integer(string='Registration Validity')
    mode_of_pay = fields.Selection([('cash','Cash'),('credit','Credit'),('card','Card'),('free','Free'),('cheque','Cheque'),('upi','UPI')])
