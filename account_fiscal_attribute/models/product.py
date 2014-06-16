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


class ProductProduct(orm.Model):
    _inherit = "product.product"
    _column = {
        # TODO determine how to narrow down on fiscal_domain... Probably purely a view operation?
        # Or make it a many 2 one and somehow dynamically add colums?
        # Make sure there can be more than one property per domain -> update fiscal_allocation_rule
        'property_fiscal_attribute': fields.property(
            'account.fiscal.attribute',
            type='many2many',
            relation='account.fiscal.attribute',
            # TODO verify if relation table (many2many) must be specified in a property field as well.
            string="Fiscal Attribute",
            # TODO veify syntax and logic:
            # domain="[('account.fiscal.attribute.use.name', '=ilike', 'partner')]"
            view_load=True,
            help="Company wise (eg localizable) Fiscal Attribute"),
    }
