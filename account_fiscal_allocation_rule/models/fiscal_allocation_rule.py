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
from openerp.osv import fields, orm
from itertools import chain

ATTR_USE_DOM_COMPANY = 'company'
ATTR_USE_DOM_PINVOICE = 'partner_invoice'
ATTR_USE_DOM_PSHIPPER = 'partner_shipper'
ATTR_USE_DOM_PRODUCT = 'product'

ACC_FISC_ALLOC_RULE_COLS_TMPL = {

    # Note: This are template style fields.
    # For nontemplate fields you might add aditional constraints to specific nontemplate fields (eg. company_id).
    # The chain method from itertools updates fields. Consider using this from within the nontemplate class when adding
    # new fields.

    # --- GENERAL SECTION ---

    'name': fields.char('Name', size=64, required=True),
    'description': fields.char('Description', size=128),
    # This fiscal domain will narrow down the available fiscal attributes / fiscal allocations.
    # It should help clustering and reducing complexity. Rules are applied *additionally*
    # preserving the result (reed: taxes applied) of previous iterations.
    # However it is optional. You can construct more complex "cross-domain" rules leaving it empty.
    'fiscal_domain_id': fields.many2one('account.fiscal.domain', 'Fiscal Domain', required=True, select=True),

    # --- CRITERION SECTION ---

    'from_country': fields.many2one('res.country', 'Country From'),
    'from_state': fields.many2one(
        'res.country.state', 'State From',
        domain="[('country_id','=',from_country)]"),
    'to_%s_country': fields.many2one(
        'res.country', 'Invoice Country') % ATTR_USE_DOM_PINVOICE,
    'to_&s_state': fields.many2one(
        'res.country.state', 'Invoice State',
        domain="[('country_id','=',to_invoice_country)]") % ATTR_USE_DOM_PINVOICE,
    'to_&s_country': fields.many2one(
        'res.country', 'Destination Country') % ATTR_USE_DOM_PSHIPPER,
    'to_%s_state': fields.many2one(
        'res.country.state', 'Destination State',
        domain="[('country_id','=',to_shipping_country)]") % ATTR_USE_DOM_PSHIPPER,
    # These are the Fiscal Attributes which are checked at runtime on the invoice-line level. As a many2many you can
    # select a custom number out of the Fiscal Attributes Table. Typicaly you might want to constrain the choice to
    # an above set Fiscal Domain (optional). Typically when parametrizing you might filter by Attribute Use (eg.
    # 'partner' or 'product' cases for convenience. (planned partner specific roles: 'seller' 'invoiced partner'
    # 'shipped partner'
    'fiscal_attribute_id': fields.many2many(
        'account.fiscal.attribute', 'Fiscal Attributes',
        # TODO this probably might result in problems as templates do not have field company_id
        domain="[('company_id','=',company_id),('fiscal_domain_id','=',fiscal_domain_id)]"),
    'use_sale': fields.boolean('Use in sales order'),
    'use_invoice': fields.boolean('Use in Invoices'),
    'use_purchase': fields.boolean('Use in Purchases'),
    'use_picking': fields.boolean('Use in Picking'),
    'date_start': fields.date(
        'Start Date', help="Starting date for this rule to be valid."),
    'date_end': fields.date(
        'End Date', help="Ending date for this rule to be valid."),
    'vat_rule': fields.selection(
        [('with', 'With VAT number'),
         ('both', 'With or Without VAT number'),
         ('without', 'Without VAT number')], "VAT Rule",
        help=("Choose if the customer need to have the"
              " field VAT fill for using this fiscal position")),
    'sequence': fields.integer(
        'Priority', required=True,
        help='Unused, unless you use account replacement. Within a sequence, the rule with '
             'the highest sequence AND which has an account replacement defined, will apply '
             'accross all fiscal domains will.'),

    # --- APPLICATION SECTION ---

    # Theese ar "Tax Culsters" applied with some extra magic. They can contain one ore various (many2many) clusters
    # and typically require to be clustered around several (or one) Fiscal Domains.
    'fiscal_allocation_id': fields.many2many(
        'account.fiscal.allocation',
        'account_fiscal_allocation_rel',
        'rule_id', 'allocation_id',
        'Fiscal Allocation Sets',
        # TODO this probably might result in problems as templates do not have field company_id
        domain="[('company_id','=',company_id),('fiscal_domain_id','=',fiscal_domain_id)]", select=True),
    'account_invoice_id': fields.many2ome('account.account', 'Account Replacement on Sales'),
    'account_purchase_id': fields.many2ome('account.account', 'Account Replacement on Purchases')
}

ACC_FISC_ALLOC_RULE_DEFS_TMPL = {
    'sequence': 10,
    'vat_rule': 'both'
}


class AccountFiscalAllocationRule(orm.Model):
    _name = "account.fiscal.allocation.rule"
    _order = 'sequence'

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

    _columns = dict(chain(ACC_FISC_ALLOC_RULE_COLS_TMPL.items(), nontmpl_update_cols.items))
    _defaults = dict(chain(ACC_FISC_ALLOC_RULE_DEFS_TMPL.items(), nontmpl_update_defs.items))

    def _map_domain(self, cr, uid, partner, addrs, company, product=None,
                    context=None, **kwargs):
        if context is None:
            context = {}

        from_country = company.partner_id.country_id.id
        from_state = company.partner_id.state_id.id

        # ##### Get all Fiscal Attributes from recieved arguments

        # Collects all Fiscal Attributes to construct a concurrent match-againt-list.
        # LOGIC: If the Fiscal Attribute of a Fiscal Rule are an entire subset of this list, the rule will match.
        attributes_all = []
        # Return list of the company Fiscal Attributes
        attributes_all += company.partner_id.property_fiscal_attribute.search(
            cr, uid, ('name','=', ATTR_USE_DOM_COMPANY), context=None
        )
        # Return list of the product Fiscal Attributes
        # Search domain in product is optional unless the proudct would be coded to receive more AttributUse Domains.
        # It is assured at the view level, that we don't have a rule that want's to alter an account, but has product
        # attributes defined. (This rule would fail, as product is only passed form account.invoice.line,
        # so the following matching list cannot be constructed on calls from account.invoice.
        # Account alteration however takes place at the account.invoice level. We still want to write all rules into
        # a single table. That's why the disctinction has to be made in a "soft" manner at the view lavel)
        if product:
            attributes_all += product.property_fiscal_attribute.search(
                cr, uid, ('name','=', ATTR_USE_DOM_PRODUCT), context=None
        )
        # Collect all attributes of the corresponding invoice & shipper partners resepectively.
        for attr_dom_use, address in addrs.items():
            attributes_all += address.fiscal_attribute_id.search(
                cr, uid, ('name','=', attr_dom_use), context=None
            )

        # ##### Finished / "Get all Fiscal Attributes from recieved arguments

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
                  # TODO fiscal_attribute_id (as a many2many) must be somehow flattened out/iterated:
                  '|', ('fiscal_attribute_id', '=', False),
                  ('fiscal_attribute_id', 'in', attribute_all),
                  ]
        if partner.vat:
            domain += [('vat_rule', 'in', ['with', 'both'])]
        else:
            domain += ['|', ('vat_rule', 'in', ['both', 'without']),
                       ('vat_rule', '=', False)]

        for attr_dom_use, address in addrs.items():
            key_country = 'to_%s_country' % attr_dom_use
            key_state = 'to_%s_state' % attr_dom_use

            to_country = address.country_id.id or False
            to_state = address.state_id.id or False


            domain += ['|', (key_country, '=', to_country),
                       (key_country, '=', False)]

            domain += ['|', (key_state, '=', to_state),
                       (key_state, '=', False)]

        return domain

    def apply_fiscal_mapping(self, cr, uid, result, **kwargs):
        taxes = result['value']['invoice_line_tax_id']
        result['value'].update(self.fiscal_allocation_map(cr, uid, taxes, **kwargs))
        return result

    def fiscal_allocation_map(self, cr, uid, partner_id=None,
                              partner_invoice_id=None, partner_shipping_id=None,
                              company_id=None, product_id=None, account_id=None, context=None, **kwargs):

        # TODO Maybe some update instead, to preserve product default taxes
        result = {'invoice_line_tax_id': False, 'account_id': False}
        if not partner_id or not company_id:
            return result

        # ##### Construct dictionary objects to be passed to the _map_domain method

        obj_partner = self.pool.get("res.partner")
        obj_company = self.pool.get("res.company")
        obj_product = self.pool.get("product.product")
        partner = obj_partner.browse(cr, uid, partner_id, context=context)
        company = obj_company.browse(cr, uid, company_id, context=context)
        product = obj_product.browse(cr, uid, product_id, context=context)

        addrs = {}
        addrs[ATTR_USE_DOM_PINVOICE] = partner_invoice_id and obj_partner.browse(
                cr, uid, partner_invoice_id, context=context)
        addrs[ATTR_USE_DOM_PSHIPPER] = partner_shipping_id and obj_partner.browse(
                cr, uid, partner_shipping_id, context=context)

        # ##### Finished / Construct dictionary objects to be passed to the _map_domain method

        # Construct a domain attribute within the _map_domain method
        domain = self._map_domain(cr, uid, partner, addrs, company, product, context, **kwargs)

        frule_obj = self.pool.get('account.fiscal.allocation.rule')
        # Return a list with ids of all matching Fiscal Allocation Rules
        frule_ids = self.search(cr, uid, domain, context=context)
        # Return a dictionary containing all applicable Fiscall Allocation Rule
        frules = frule_ids and frule_obj.browse(cr, uid, frule_ids, context=context) or False
        # Pass applicable Fiscal Allocation Rules to the Fiscal Allocation mapa_tax method.
        # Return an updated output dictionary with taxes stored in invoice_line_tax_id.
        # See 'product_id_change' method in 'account.inovice.line' model in 'accont_invoice.py' of core account addon.
        # TODO restrict search according to case for better performance, if possible.
        # CASE: Called from the Invoice Line ('account.invoice.line')
        if product_id:
            falloc_obj =  self.pool.get('account.fiscal.allocation')
            # This .update() is kind of a double floor, as existing taxes are also preserved in the map_tax method.
            updated_taxes = frules and t['invoice_line_tax_id'].update(
                falloc_obj.map_tax(cr, uid, frules, taxes, inv_type, context)
                # TODO as date is probably not passed in context, load invoice date into the present context
            ) or False
            return updated_taxes
        # CASE: Called from the Invoice itself ('account.invoice')
        if account_id:
            updated_account = frules and t['account_id'] = self._map_account(
                cr, uid, frules, account_id, inv_type, context
                # TODO as date is probably not passed in context, load invoice date into the present context
            ) or False
            return updated_account

        return False


    def _map_account(self, cr, uid, frules, account_id, inv_type, context=None):

        # Some ugly hack to get the corresponding rule with the highest sequence number only.
        # TODO rise alert if sequence number is ambigous. -> adapt rules sequence numbers manually.
        f_valid_sales_id = frules.search(
            cr, uid, ('account_invoice_id', '!=', None) , offset=0, limit=1, order=sequence, context=context)
        f_valid_purchase_id = frules.search(
            cr, uid, ('account_purchase_id', '!=', None) , offset=0, limit=1, order=sequence, context=context)
        # Get it as a dict, in order to access the account fields.
        f_valid_sales  = frules.browse(cr, uid, f_valid_sales_id, context=context)
        f_valid_purchase  = frules.browse(cr, uid, f_valid_purchase_id, context=context)

        # CASE: Outgoing Invoice or a refund of such.
        if inv_type in ('out_invoice','out_refund'):
            account_id = f_valid_sales_id and f_valid_sales.account_invoice_id or False

        # CASE: Incoming Invoice or a refund of such.
        if inv_type in ('in_invoice', 'in_refund'):
            account_id = f_valid_purchase_id and f_valid_purchase.account_purchase_id or False

        return account_id

# ---------------------------
# Templates & Wizards Section
# ---------------------------


class AccountFiscalAllocationRuleTemplate(orm.Model):
    _name = "account.fiscal.allocation.rule.template"
    _columns = ACC_FISC_ALLOC_RULE_COLS_TMPL
    _defaults = ACC_FISC_ALLOC_RULE_DEFS_TMPL


class WizardAccountFiscalAllocationRule(orm.TransientModel):
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
