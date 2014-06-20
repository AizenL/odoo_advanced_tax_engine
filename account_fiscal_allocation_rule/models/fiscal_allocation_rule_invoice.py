# -*- encoding: utf-8 -*-
###############################################################################
#
#   account_fiscal_allocation_rule for OpenERP
#   Copyright (C) 2009-TODAY Akretion <http://www.akretion.com>
#     @author Sébastien BEAU <sebastien.beau@akretion.com>
#     @author Renato Lima <renato.lima@akretion.com>
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm


class AccountInvoiceLine (orm.Model):
    _inherit = 'account.invoice.line'

    # Local method to pass the calling module. (here: Invoice, more specifically: account.inoivce.line)
    # Note: Fiscal Allocation Rules can be setup to be applied depending on from where they are called.
    def _fiscal_allocation_map(self, cr, uid, result, context=None, **kwargs):

        if not kwargs.get('context', False):
            kwargs['context'] = {}

        # Clarify that account.fiscal.allocation.rule will be called from the line of an *invoice* (use_invoice=True)
        kwargs['context'].update({'use_domain': ('use_invoice', '=', True)})

        # Return the result of calling the apply_fiscal_mapping method of Fiscal Allocation Rule on itself.
        return self.pool.get('account.fiscal.allocation.rule').apply_fiscal_mapping(cr, uid, result, **kwargs)

    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', prd_type='out_invoice',
                          partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
                          context=None, company_id=None):
        # We do also want the results of the product_id_change of the inherited class.
        result = super(AccountInvoiceLine, self).product_id_change(
            cr, uid, ids, product, uom_id, qty, name, prd_type,
            partner_id, fposition_id, price_unit, currency_id,
            context, company_id
        )
        # If not all (partner, company, product) are set, we nothing special happens.
        if not partner_id or not company_id or not product:
            return result

        # We take the result of the method of the inherited class, define some mandatory arguments and pass it to the
        # preparatory function above.
        return self._fiscal_allocation_map(
            cr, uid, result, partner_id=partner_id, partner_invoice_id=partner_id,
            company_id=company_id, product_id=product
        )

    # --- Methods that where originally inherited from account.invoice ---
    #
    # TODO : Make onchange mehtods for partner / company to be aware of the product of aacount.invoice.line

    # def onchange_partner_id(self, cr, uid, ids, p_type, partner_id,
    #                         date_invoice=False, payment_term=False,
    #                         partner_bank_id=False, company_id=False):
    #
    #     result = super(AccountInvoice, self).onchange_partner_id(
    #         cr, uid, ids, p_type, partner_id, date_invoice, payment_term, partner_bank_id, company_id
    #     )
    #
    #     if not partner_id or not company_id:
    #         return result
    #
    #     return self._fiscal_allocation_map(
    #         cr, uid, result, partner_id=partner_id, partner_invoice_id=partner_id, company_id=company_id
    #     )

    # def onchange_company_id(self, cr, uid, ids, company_id, partner_id, c_type,
    #                         invoice_line, currency_id, context=None):
    #     result = super(AccountInvoice, self).onchange_company_id(
    #         self, cr, uid, ids, company_id, partner_id, c_type, invoice_line, currency_id, context=None
    #     )
    #
    #     if not partner_id or not company_id:
    #         return result
    #
    #     return self._fiscal_allocation_map(
    #         cr, uid, result, partner_id=partner_id, partner_invoice_id=partner_id, company_id=company_id
    #     )
