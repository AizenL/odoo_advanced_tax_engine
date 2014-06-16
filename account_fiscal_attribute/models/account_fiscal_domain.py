# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2004-2009 Tiny SPRL
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp.osv import orm, fields


class FiscalDomain(orm.Model):
    # TODO check, if this naming style is like contenion or fiscal_domain (as before)
    _name = "account.fiscal.domain"

    _columns = {
        'name': fields.char('name', size=25, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'note': fields.text('note'),
        'active': fields.boolean('active'),
        # TODO account_fiscal_allocation_set_id = fields.many2many
    }

# ---------------------------
# Templates & Wizards Section
# ---------------------------
