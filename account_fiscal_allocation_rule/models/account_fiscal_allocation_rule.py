# -*- encoding: utf-8 -*-
###############################################################################
#
#   account_fiscal_allocation_rule for Odoo
#   Copyright (C) 2014-TODAY Odoo-Colombia <https://github.com/odoo-colombia>
#     @author David Arnold (El Aleman S.A.S) <david@elaleman.co>
#     @author Juan Pablo Aries (OpenZIX)
#   account_fiscal_allocation_rule for OpenERP
#   Copyright (C) 2009-TODAY Akretion <http://www.akretion.com>
#     @author Sébastien BEAU <sebastien.beau@akretion.com>
#     @author Renato Lima <renato.lima@akretion.com>
#   Copyright 2012 Camptocamp SA
#     @author: Guewen Baconnier
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

import time
from osv import fields, osv


class AccountFiscalAllocationRule(osv.Model):
    _name = "account.fiscal.allocation.rule"
    _order = 'sequence'
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.char('Description', size=128),
        # Set a fiscal domain for narrowing drop down menus later
        'fiscal_domain_id': fields.many2one('account.fiscal.domain.id', 'Fiscal Domain', required=True, select=True),
        'from_country': fields.many2one('res.country', 'Country From'),
        'from_state': fields.many2one(
            'res.country.state', 'State From',
            domain="[('country_id','=',from_country)]"),
        'to_invoice_country': fields.many2one(
            'res.country', 'Invoice Country'),
        'to_invoice_state': fields.many2one(
            'res.country.state', 'Invoice State',
            domain="[('country_id','=',to_invoice_country)]"),
        'to_shipping_country': fields.many2one(
            'res.country', 'Destination Country'),
        'to_shipping_state': fields.many2one(
            'res.country.state', 'Destination State',
            domain="[('country_id','=',to_shipping_country)]"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, select=True),
        'fiscal_allocation_id': fields.many2many(
            'account.fiscal.allocation',
            'account_fiscal_allocation_rel',
            'rule_id', 'allocation_id',
            'Fiscal Allocation Sets',
            domain="[('company_id','=',company_id)]", select=True),
        # Add available set of fiscal attributes of partners and products.
        # Attributes of Seller are the same as Attributes of Buyer (Attributes of Partner)
        # A distinction can be realized easily, if it might help reducing complexity
        'from_fiscal_attribute_id': fields.many2one(
            'account.fiscal.attribute', 'Fiscal Attribute Seller',
            domain="[('fiscal_domain_id','=',fiscal_domain_id),('attribute_use','=',partner)]", select=True),
        'to_fiscal_attribute_id': fields.many2one(
            'account.fiscal.attribute', 'Fiscal Attribute Buyer',
            domain="[('fiscal_domain_id','=',fiscal_domain_id),('attribute_use','=',partner)]", select=True),
        'product_fiscal_attribute_id': fields.many2one(
            'account.fiscal.attribute', 'Fiscal Attribute Product',
            domain="[('fiscal_domain_id','=',fiscal_domain_id),('attribute_use','=',product)]", select=True),
        # Add further custom defined use cases of account_fiscal_attributes
        'use_sale': fields.boolean('Use in sales order'),
        'use_invoice': fields.boolean('Use in Invoices'),
        'use_purchase': fields.boolean('Use in Purchases'),
        'use_picking': fields.boolean('Use in Picking'),
        'date_start': fields.date(
            'Start Date', help="Starting date for this rule to be valid."),
        'date_end': fields.date(
            'End Date', help="Ending date for this rule to be valid."),
        # Add optional account replacement on a per invoice line level
        'sequence': fields.integer(
            'Priority', required=True,
            help='Unused, unless you use account replacement. Within a sequence, the rule with '
                 'the highest sequence AND which has an account replacement defined, will apply '
                 'accross all fiscal domains will.'),
        'vat_rule': fields.selection(
            [('with', 'With VAT number'),
             ('both', 'With or Without VAT number'),
             ('without', 'Without VAT number')], "VAT Rule",
            help=("Choose if the customer need to have the"
                  " field VAT fill for using this fiscal position")),
    }
    _defaults = {
        'sequence': 10,
    }

    def _map_domain(self, cr, uid, partner, addrs, company, product,
                    context=None, **kwargs):
        if context is None:
            context = {}

        from_country = company.partner_id.country_id.id
        from_state = company.partner_id.state_id.id
        # Get values for additional attributes
        from_attribute = company.partner_id.fiscal_attribute_id.id
        product_attribute = product.fiscal_attribute_id.id

        document_date = context.get('date', time.strftime('%Y-%m-%d'))
        use_domain = context.get('use_domain', ('use_sale', '=', True))

        domain = ['&', ('company_id', '=', company.id), use_domain,
                  '|', ('from_country', '=', from_country),
                  ('from_country', '=', False),
                  '|', ('from_state', '=', from_state),
                  ('from_state', '=', False),
                  '|', ('date_start', '=', False),
                  ('date_start', '<=', document_date),
                  '|', ('date_end', '=', False),
                  ('date_end', '>=', document_date),
                  # Set more (custom) attributes here:
                  # TODO Tax Domain
                  '|', ('from_fiscal_attribute_id', '=', False),
                  ('from_fiscal_attribute_id', '=', from_attribute),
                  '|', ('product_fiscal_attribute_id', '=', False),
                  ('product_fiscal_attribute_id', '=', product_attribute),
                  ]
        if partner.vat:
            domain += [('vat_rule', 'in', ['with', 'both'])]
        else:
            domain += ['|', ('vat_rule', 'in', ['both', 'without']),
                       ('vat_rule', '=', False)]

        for address_type, address in addrs.items():
            key_country = 'to_%s_country' % address_type
            key_state = 'to_%s_state' % address_type
            key_attribute = 'to_%s_fiscal_attribute_id' % address_type
            to_country = address.country_id.id or False
            domain += ['|', (key_country, '=', to_country),
                       (key_country, '=', False)]
            to_state = address.state_id.id or False
            domain += ['|', (key_state, '=', to_state),
                       (key_state, '=', False)]
            to_attribute = address.fiscal_attribute_id.id or False
            domain += ['|', (key_attribute, '=', to_attribute),
                       (key_attribute, '=', False)]

        return domain

    def apply_fiscal_mapping(self, cr, uid, result, **kwargs):
        result['value'].update(self.fiscal_allocation_map(cr, uid, **kwargs))
        return result

    def fiscal_allocation_map(self, cr, uid, partner_id=None,
                              partner_invoice_id=None, partner_shipping_id=None,
                              company_id=None, product_id=None, context=None, **kwargs):

        result = {'fiscal_allocation': False}
        if not partner_id or not company_id:
            return result

        obj_fsc_rule = self.pool.get('account.fiscal.allocation.rule')
        obj_partner = self.pool.get("res.partner")
        obj_company = self.pool.get("res.company")
        # TODO onchange for product
        obj_product = self.pool.get("res.product")
        # TODO get current product_id here as it is not passed, or pass it from some superior call (eg onchange)
        partner = obj_partner.browse(cr, uid, partner_id, context=context)
        company = obj_company.browse(cr, uid, company_id, context=context)
        product = obj_product.browse(cr, uid, product_id, context=context)

        addrs = {}
        if partner_invoice_id:
            addrs['invoice'] = obj_partner.browse(
                cr, uid, partner_invoice_id, context=context)

        # In picking case the invoice_id can be empty but we need a
        # value I only see this case, maybe we can move this code in
        # fiscal_stock_rule
        else:
            partner_addr = partner.address_get(['invoice'])
            addr_id = partner_addr['invoice'] and partner_addr['invoice'] or None
            if addr_id:
                addrs['invoice'] = obj_partner.browse(
                    cr, uid, addr_id, context=context)
        if partner_shipping_id:
            addrs['shipping'] = obj_partner.browse(
                cr, uid, partner_shipping_id, context=context)

        #Rule based determination
        domain = self._map_domain(
            cr, uid, partner, addrs, company, product, context, **kwargs)

        fsc_alloc_id = self.search(cr, uid, domain, context=context)

        # TODO allow for multiple sets in the same domain to be allocated.
        if fsc_alloc_id:
            fsc_rule = obj_fsc_rule.browse(
                cr, uid, fsc_alloc_id, context=context)[0]
            result['fiscal_allocation'] = fsc_rule.fiscal_allocation_id.id

        return result

AccountFiscalAllocationRule()


class AccountFiscalAllocationRuleTemplate(osv.osv):
    _name = "account.fiscal.allocation.rule.template"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.char('Description', size=128),
        'from_country': fields.many2one('res.country', 'Country Form'),
        'from_state': fields.many2one(
            'res.country.state', 'State From',
            domain="[('country_id','=',from_country)]"),
        'to_invoice_country': fields.many2one('res.country', 'Country To'),
        'to_invoice_state': fields.many2one(
            'res.country.state', 'State To',
            domain="[('country_id','=',to_invoice_country)]"),
        'to_shipping_country': fields.many2one(
            'res.country', 'Destination Country'),
        'to_shipping_state': fields.many2one(
            'res.country.state', 'Destination State',
            domain="[('country_id','=',to_shipping_country)]"),
        'fiscal_allocation_id': fields.many2many(
            'account.fiscal.allocation',
            'account_fiscal_allocation_rel',
            'rule_id', 'allocation_id',
            'Fiscal Allocation Sets'),
        # See above for comments
        'from_fiscal_attribute_id': fields.many2one(
            'account.fiscal.attribute', 'Fiscal Attribute Seller',
            domain="[('fiscal_domain_id','=',fiscal_domain_id),('attribute_use','=',partner)]", select=True),
        'to_fiscal_attribute_id': fields.many2one(
            'account.fiscal.attribute', 'Fiscal Attribute Buyer',
            domain="[('fiscal_domain_id','=',fiscal_domain_id),('attribute_use','=',partner)]", select=True),
        'product_fiscal_attribute_id': fields.many2one(
            'account.fiscal.attribute', 'Fiscal Attribute Product',
            domain="[('fiscal_domain_id','=',fiscal_domain_id),('attribute_use','=',product)]", select=True),
        # Add further custom defined use cases of account_fiscal_attributes
        'use_sale': fields.boolean('Use in sales order'),
        'use_invoice': fields.boolean('Use in Invoices'),
        'use_purchase': fields.boolean('Use in Purchases'),
        'use_picking': fields.boolean('Use in Picking'),
        'date_start': fields.date(
            'Start Date', help="Starting date for this rule to be valid."),
        'date_end': fields.date(
            'End Date', help="Ending date for this rule to be valid."),
        'sequence': fields.integer(
            'Priority', required=True,
            help='The lowest number will be applied.'),
        'vat_rule': fields.selection(
            [('with', 'With VAT number'),
             ('both', 'With or Without VAT number'),
             ('without', 'Without VAT number')],
            "VAT Rule",
        help=("Choose if the customer need to have the"
        " field VAT fill for using this fiscal position")),
    }
    _defaults = {
        'sequence': 10,
        'vat_rule': 'both'
    }


class WizardAccountFiscalAllocationRule(osv.TransientModel):
    _name = 'wizard.account.fiscal.allocation.rule'
    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    defaults = {
        'company_id': lambda self, cr, uid, c:
        self.pool.get('res.users').browse(cr, uid, [uid], c)[0].company_id.id,
    }

    def _template_vals(self, cr, uid, template, company_id,
                       fiscal_allocation_ids, context=None):
        return {'name': template.name,
                'description': template.description,
                'from_country': template.from_country.id,
                'from_state': template.from_state.id,
                'to_invoice_country': template.to_invoice_country.id,
                'to_invoice_state': template.to_invoice_state.id,
                'to_shipping_country': template.to_shipping_country.id,
                'to_shipping_state': template.to_shipping_state.id,
                'company_id': company_id,
                'fiscal_allocation_id': fiscal_allocation_ids and fiscal_allocation_ids[0],
                # Add further template attributes here
                'from_fiscal_attribute_id': template.from_fiscal_attribute_id.id,
                'to_fiscal_attribute_id': template.to_fiscal_attribute_id.id,
                'product_fiscal_attribute_id': template.product_fiscal_attribute_id.id,
                'use_sale': template.use_sale,
                'use_invoice': template.use_invoice,
                'use_purchase': template.use_purchase,
                'use_picking': template.use_picking,
                'date_start': template.date_start,
                'date_end': template.date_end,
                'sequence': template.sequence,
                'vat_rule': template.vat_rule,
                }

    def action_create(self, cr, uid, ids, context=None):

        obj_wizard = self.browse(cr, uid, ids[0], context=context)

        obj_far = self.pool.get('account.fiscal.allocation.rule')
        obj_far_temp = self.pool.get('account.fiscal.allocation.rule.template')
        obj_fa = self.pool.get('account.fiscal.allocation')

        company_id = obj_wizard.company_id.id

        far_ids = obj_far_temp.search(cr, uid, [], context=context)

        # TODO fix me doesn't work multi template that have empty fiscal
        # position maybe we should link the rule with the account template
        for far_template in obj_far_temp.browse(
                cr, uid, far_ids, context=context):
            fa_ids = False
            if far_template.fiscal_allocation_id:

                fa_ids = obj_fa.search(
                    cr, uid,
                    [('name', '=', far_template.fiscal_allocation_id.name)],
                    context=context)

                if not fa_ids:
                    continue

            vals = self._template_vals(
                cr, uid, far_template, company_id, fa_ids, context=context)
            obj_far.create(
                cr, uid, vals, context=context)

        return {}