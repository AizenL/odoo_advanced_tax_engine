# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014                                                          #
# David Arnold (El Aleman SAS), Hector Ivan Valencia, Juan Pablo Arias        #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

{
    'name': 'Account Fiscal Attribute & Fiscal Domain',
    'description': 'Adds fiscal attribute for partner and product (extendable)'
                   'to base tax allocation on those attributes.'
                   'Adds fiscal domain for clustering tax '
                   'calculation into smaller pieces '
                   '(exampla useage: clustering on per tax basis).',
    'category': 'Account/Fiscal',
    'license': 'AGPL-3',
    'author': 'Juan Pablo Arias',
    'website': '',
    'version': '0.1',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'data/account.fiscal.attribute.use.csv',
        'security/ir.model.access.csv', # debe ser aconditionado por un experto
        # 'views/partner_view.xml', - para depurar
        # 'views/product_view.xml', - sin contenido intelligente
        # 'views/account_fiscal_attribute_view.xml', - base para depurar
        # 'views/account_fiscal_domain_view.xml', - base para depurar
        'views/account_tax_view.xml' # base para depurar
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
