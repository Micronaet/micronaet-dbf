# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import erppeek
import ConfigParser

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
col = 107
path = '/opt/odoo/.local/share/Odoo/mount/edison'
cfg_file = os.path.expanduser('../openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (
        server, port), 
    db=dbname,
    user=user,
    password=pwd,
    )
product_pool = odoo.model('product.product')

"""product_ids = product_pool.search([
    ('standard_price', '=', 0),
    ('lst_price', '>', 0),
    '|',
    ('default_code', '=ilike', '__-%'),
    ('default_code', '=ilike', '___-%'),
    ])

import pdb; pdb.set_trace()
print 'Totale prodotti', len(product_ids)
for product in product_pool.browse(product_ids):
    print 'Aggiorno: ', product.default_code, product.standard_price, product.lst_price
    product_pool.write(product.id, {
        'standard_price': product.lst_price,
        })
        
sys.exit()"""
not_found = []
for root, folders, files in os.walk(path):
    for f in files:
        filename = os.path.join(root, f)
        print 'Read:', filename
        if f[-3:].upper() == 'TXT':
             for row in open(filename):
                 #print '>> ANALIZZO: ', row
                 if len(row) != col:
                     print '[WARNING] Jumped not data line', row
                     continue
                 default_code = row[60:79].strip()
                 
                 if default_code[2:3] != '-' and default_code[3:4] != '-':
                     print '[WARNING] Jumped code not internal', row
                     continue

                 lst_price = float(
                    row[79:96].replace(' ', '').replace('.', '').replace(',', '.')[1:])

                 product_ids = product_pool.search([
                     ('default_code', '=', default_code),
                     ])

                 if not product_ids:
                    not_found.append(default_code)
                    print '[ERROR] Not found', row
                    continue

                 if lst_price <= 0.0:
                     print '[ERROR] Jumped no price', row
                     continue
                     
                 print '[INFO] Used', row
                 product_pool.write(product_ids, {
                     'lst_price': lst_price,
                     })
    break
print 'Non trovati', not_found
