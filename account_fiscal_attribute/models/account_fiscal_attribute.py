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


class FiscalAttributeUse(orm.Model):
    # TODO check, if this naming style is like contenion or attribute_use (as before)
    _name = "account.fiscal.attribute.use"

    _columns = {
        'name': fields.char('name', size=25, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'note': fields.text('note'),
        'active': fields.boolean('active'),
    }


class AccountFiscalAttribute(orm.Model):
    _name = 'account.fiscal.attribute'

    _columns = {
        'name': fields.char('name', size=25, required=True),
        'description': fields.char('description', size=50, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'note': fields.text('note'),
        'active': fields.boolean('active'),
        'attribute_use_id': fields.many2one(
            'account.fiscal.attribute.use',
            'Attribute Use'),
        'fiscal_domain_id': fields.many2one(
            'account.fiscal.domain',
            'Fiscal Domain'),
    }

# TODO Tampleate & Wizard for FiscalDomain / FiscalAttributeUse / AccountFiscalAttribute

"""
# Moved to account_fiscal_allocation in /account_fiscal_rule
class AccountFiscalAllocationSet(orm.Model):
    _name = 'account.fiscal.allocation.set'

    _columns = {
        'code': fields.char('code', size=25, required=True),
        'name': fields.char('code', size=50, required=True),
        'note': fields.text('note'),
        'active': fields.boolean('active'),
        'fiscal_domain_id': fields.many2one(
            'account.fiscal.domain',
            'Fiscal Domain'),
        'account_tax_id': fields.many2one(
            'account.tax',
            'Tax'),
    }
"""

# ---------------------------
# Templates & Wizards Section
# ---------------------------
