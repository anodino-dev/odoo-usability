# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrHolidaysPost(models.TransientModel):
    _name = 'hr.holidays.post'
    _description = 'Wizard for post holidays'

    before_date = fields.Date(
        string='Select Leave Requests That Ended Before', required=True,
        default=fields.Date.context_today,
        help="The wizard will select the validated holidays "
        "that ended before that date (including holidays that "
        "ended on that date).")
    holidays_to_post_ids = fields.Many2many(
        'hr.holidays', string='Leave Requests to Post',
        domain=[
            ('type', '=', 'remove'),
            ('holiday_type', '=', 'employee'),
            ('state', '=', 'validate'),
            ('posted_date', '=', False),
            ])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='State', readonly=True, default='draft')

    @api.multi
    def select_date(self):
        self.ensure_one()
        hols = self.env['hr.holidays'].search([
            ('type', '=', 'remove'),
            ('holiday_type', '=', 'employee'),
            ('state', '=', 'validate'),
            ('posted_date', '=', False),
            ('vacation_date_to', '<=', self.before_date),
            ])
        self.write({
            'state': 'done',
            'holidays_to_post_ids': [(6, 0, hols.ids)],
            })
        action = self.env['ir.actions.act_window'].for_xml_id(
            'hr_holidays_usability', 'hr_holidays_post_action')
        action['res_id'] = self.id
        return action

    @api.multi
    def run(self):
        self.ensure_one()
        # I have to make a copy of self.holidays_to_post_ids in a variable
        # because, after the write, it doesn't have a value any more !!!
        holidays_to_post = self.holidays_to_post_ids
        today = fields.Date.context_today(self)
        if not self.holidays_to_post_ids:
            raise UserError(_('No leave request to post.'))
        self.holidays_to_post_ids.write({'posted_date': today})
        view_id = self.env.ref('hr_holidays_usability.hr_holiday_pivot').id
        action = {
            'name': _('Leave Requests'),
            'res_model': 'hr.holidays',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', holidays_to_post.ids)],
            'view_mode': 'pivot',
            'view_id': view_id,
            }
        return action
