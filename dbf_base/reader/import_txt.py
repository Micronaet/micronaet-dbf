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
col = 5 
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

for root, folders, files in os.walk(path):
    for f in files:
        filename = os.path.join(root, f)
        print 'Read:', filename
        if f[-3:].upper() == 'TXT':
             for row in open(filename):
                 line = row.split(' ') 
                 print '>> ANALIZZO: ', line
                 import pdb; pdb.set_trace()
                 if len(line) != col:
                     print '   Jumped', row
                     continue
                 default_code = line[4] # XXX
                 lst_price = line[5]
                 
                 if default_code[2:3] != '-' and default_code[3:4] != '-':
                     print '   Jumped', row
                     continue
                 print 'Used', row
                 product_ids = product_pool.search([
                     ('default_code', '=', default_code),
                     ])
                 product_pool.write(product_ids, {
                     'lst_price': lst_price,
                     })
    break
