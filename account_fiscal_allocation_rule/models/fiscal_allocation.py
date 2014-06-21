# -*- encoding: utf-8 -*-
###############################################################################
#
#   account_fiscal_allocation_rule for Odoo
#   Copyright (C) 2014-TODAY Odoo-Colombia <https://github.com/odoo-colombia>
#     @author David Arnold (El Aleman S.A.S) <david@elaleman.co>
#     @author Juan Pablo Aries (OpenZIX)
#   Copyright (C) 2010-TODAY Akretion <http://www.akretion.com>
#     @author Renato Lima <renato.lima@akretion.com>
#     @author Raphaël Valyi <rvalyi@akretion.com>
#   Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, orm
from itertools import chain

ACC_FISC_ALLOC_COLS_TMPL = {
    'name': fields.char('Fiscal Allocation', size=64, required=True),
    'description': fields.char('Description', size=64),
    'fiscal_domain_id': fields.many2one('account.fiscal.domain', 'Fiscal Domain', required=True, select=True),
    'sale_tax_ids': fields.many2many(
        'account.tax', 'fiscal_allocation_sale_tax_rel',
        'fiscal_allocation_id', 'tax_id', 'Applicable Sale Taxes',
        domain="[('type_tax_use', '!=', 'purchase'),('fiscal_domain_id', '=', fiscal_domain_id)]"),
    'purchase_tax_ids': fields.many2many(
        'account.tax', 'fiscal_allocation_purchase_tax_rel',
        'fiscal_allocation_id', 'tax_id', 'Applicable Purchase Taxes',
        domain="[('type_tax_use', '!=', 'sale'),('fiscal_domain_id', '=', fiscal_domain_id)]"),
    'note': fields.text('Notes'),
}

ACC_FISC_ALLOC_DEFS_TMPL = {

}

class AccountFiscalAllocation(orm.Model):
    _name = 'account.fiscal.allocation'
    _description = 'Fiscal Allocation Set'

    nontmpl_update_cols = {
        'active': fields.boolean('active'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, select=True),
    }

    nontmpl_update_defs = {
        'active': True,
        'company_id': lambda s, cr, uid, c: s.pool.get(
            'res.company')._company_default_get(cr, uid, 'account.fiscal.allocation.rule', context=c),
    }

    _columns = dict(chain(ACC_FISC_ALLOC_COLS_TMPL.items(), nontmpl_update_cols.items()))
    _defaults = dict(chain(ACC_FISC_ALLOC_DEFS_TMPL.items(), nontmpl_update_defs.items()))

    def map_tax(self, cr, uid, frules, taxes, inv_type, context=None):

        # 'set()' filters duplicates. 'taxes' are product's default coded taxes, there is no conflict with the
        # traditional paradigm of allocating default taxes to products. They have been passed and will be retained:
        result = set(taxes)

        # CASE: Outgoing Invoice or a refund of such.
        if inv_type in ('out_invoice','out_refund'):
            # Iterate all applicable Fiscal Allocation Rules, that have been passed.
            for f in frules:
                # Iterate all Fiscal Allocations of each Fiscal Allocation Rule
                for a in fiscal_allocation_id:
                    # Iterate Sales Taxes of each Fiscal Allocation
                    for t in self.sale_tax_ids:
                        # Add Tax to result (evitating duplicates, as 'result' is a python 'set()')
                        result.add(t.id)

        # CASE: Incoming Invoice or a refund of such.
        if inv_type in ('in_invoice', 'in_refund'):
            for f in frules:
                for a in fiscal_allocation_id:
                    for t in self.purchase_tax_ids:
                        result.add(t.id)

        return list(result)

# ---------------------------
# Templates & Wizards Section
# ---------------------------


class AccountFiscalAllocationTemplate(orm.Model):
    _name = 'account.fiscal.allocation.template'
    _description = 'Fiscal Allocation Set Template'
    _columns = ACC_FISC_ALLOC_COLS_TMPL
    _defaults = ACC_FISC_ALLOC_DEFS_TMPL

# Is this for pure convenience? Look at views of fiscal_classification to identify use.
    def name_search(self, cr, user, name='', args=None, operator='ilike',
                    context=None, limit=80):

        if not args:
            args = []

        if not context:
            context = {}

        if name:
            ids = self.search(cr, user, [('name', '=', name)] + args,
                              limit=limit, context=context)
            if not len(ids):
                ids = self.search(
                    cr, user, [('description', '=', name)] + args,
                    limit=limit, context=context)
            if not len(ids):
                ids = self.search(cr, user, [('name', operator, name)] + args,
                                  limit=limit, context=context)
                ids += self.search(
                    cr, user, [('description', operator, name)] + args,
                    limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)

        return self.name_get(cr, user, ids, context)


class WizardAccountFiscalAllocation(orm.TransientModel):
    _name = 'wizard.account.fiscal.allocation'
    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, c:
        self.pool.get('res.users').browse(cr, uid, [uid], c)[0].company_id.id,
    }

    def action_create(self, cr, uid, ids, context=None):
        obj_wizard = self.browse(cr, uid, ids[0])
        obj_tax = self.pool.get('account.tax')
        obj_tax_template = self.pool.get('account.tax.template')
        obj_fa = self.pool.get('account.fiscal.allocation')
        obj_fa_template = self.pool.get(
            'account.fiscal.allocation.template')

        company_id = obj_wizard.company_id.id
        tax_template_ref = {}

        tax_ids = obj_tax.search(
            cr, uid, [('company_id', '=', company_id)], context=context)

        for tax in obj_tax.browse(cr, uid, tax_ids, context=context):
            tax_template = obj_tax_template.search(
                cr, uid, [('name', '=', tax.name)], context=context)[0]

            if tax_template:
                tax_template_ref[tax_template] = tax.id

        fclass_ids_template = obj_fa_template.search(
            cr, uid, [], context=context)

        for fclass_template in obj_fa_template.browse(
                cr, uid, fclass_ids_template, context=context):

            fclass_id = obj_fa.search(
                cr, uid, [('name', '=', fclass_template.name)],
                context=context)

            if not fclass_id:
                t_sale_tax_ids = []
                for tax in fclass_template.sale_tax_ids:
                    t_sale_tax_ids.append(tax_template_ref[tax.id])

                t_purchase_tax_ids = []
                for tax in fclass_template.purchase_tax_ids:
                    t_purchase_tax_ids.append(tax_template_ref[tax.id])

                vals = {
                    'name': fclass_template.name,
                    'description': fclass_template.description,
                    'company_id': company_id,
                    'sale_tax_ids': [(6, 0, t_sale_tax_ids)],
                    'purchase_tax_ids': [(6, 0, t_purchase_tax_ids)]
                }
                obj_fa.create(cr, uid, vals, context)

        return {}
