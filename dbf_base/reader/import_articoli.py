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
import xlrd

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('../openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

def clean(value, length=False):
    if not value:
        return ''
        
    res = ''
    for c in '%s' % value:
        if ord(c) < 127:
            res += c
        else:
            res += '#'
    if length:
        return res[:length]        
    return res

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
partner_pool = odoo.model('res.partner')


# -----------------------------------------------------------------------------
#                                 COMPARE DATA:
# -----------------------------------------------------------------------------
for mode in start:
    # Case 1: ODOO customer/supplier VS Mexal customer:                
    for sql_code in odoo[mode]:
        sql_name = odoo[mode][sql_code].name
        if sql_code in mexal[mode]:
            mexal_name = mexal[mode][sql_code]
            if sql_name != mexal_name:
                #new_odoo['error'].append(
                print u'%s. %s > ODOO: %s <> DA MEXAL %s' % (
                    mode, sql_code, sql_name, mexal_name)
        else:
            new_odoo[mode][sql_code] = sql_name

    # Case 2: Mexal customer/supplier VS ODOO customer:                
    for mexal_code in mexal[mode]:
        mexal_name = mexal[mode][mexal_code]
        if mexal_code in odoo[mode]:
            sql_name = odoo[mode][mexal_code].name
            if mexal_name != sql_name:
                #new_mexal['error'].append(
                print u'%s. %s > MEXAL: %s <> DA ODOO %s' % (
                    mode, mexal_code, mexal_name, sql_name)
        else:
            new_mexal[mode][mexal_code] = mexal_name

# -----------------------------------------------------------------------------
# Output CSV: 
# -----------------------------------------------------------------------------
#print 'ERRORI ODOO:'
#print new_odoo['error']

#print '\n\nERRORI MEXAL:'
#print new_mexal['error']

print u'\n\nNew customer ODOO VS MEXAL', len(new_odoo['customer'])
print u'New supplier ODOO VS MEXAL', len(new_odoo['supplier'])
print u'Error ODOO VS MEXAL', len(new_odoo['error'])

print u'\n\nNew customer MEXAL VS ODOO', len(new_mexal['customer'])
print u'New supplier MEXAL VS ODOO', len(new_mexal['supplier'])
print u'Error MEXAL VS ODOO', len(new_mexal['error'])

mask = '%-8s%-70s%-30s%-90s%-30s%-29s%-24s%-17s%-52s%-5s%-26s%-20s' + \
    '%-25s%-10s%-16s%-30s%-4s%-2s%-20s%-80s%-6s%-1s%-2s%s'

for mode in start:
    out_file = open('./new_%s.csv' % mode, 'w')
    for sql_code in new_odoo[mode]:
        partner = new_odoo[mode][sql_code].name
        #sql_name = new_odoo[mode][sql_code].name
        #row = '%s;%s\n' % (sql_code, sql_name.encode('UTF-8'))
        
        expense = '' # TODO        
        payment = '' # TODO record['CCODCOPA']

        row = mask % (
            clean(sql_code, 8),
            clean(partner.name, 70),
            clean(partner.phone, 30),
            clean(partner.email, 90),
            clean('', 30), # TODO fax
            clean('', 29), # TODO reference
            clean(partner.vat, 24), # vat
            clean(partner.fiscalcode, 17), # fiscalcode
            clean(partner.street, 52),
            clean(partner.zip, 5),
            clean(partner.city, 26), # city
            clean('', 20), # TODO partner.provice

            clean('', 25), # TODO payment payment_db.get(payment, '')
            clean('', 10), # agent code # record['CCODAGEN']
            clean('', 16), #record['NSCOFATT'], # discount
            clean('', 30), # cod. bank record['CCODBANC']
            '22', 
            clean('', 2), # TODO Country record['CNAZIONE']
            clean('', 20), # TODO CC record['CCONTCORR']
            clean(partner.website, 80), # Web
            clean(expense, 6), # TODO Expense
            clean('', 1), # TODO Cinn record['CCODCINN']
            clean('', 2), # # Cine record['CCODCINE']
            eol,
            )
        out_file.write(row)
        #print row
    out_file.close()

for mode in start:
    out_file = open('./decidere_%s.csv' % mode, 'w')
    for mexal_code in new_mexal[mode]:
        mexal_name = new_mexal[mode][mexal_code]
        row = '%s;%s\n' % (mexal_code, mexal_name.encode('UTF-8'))
        out_file.write(row)
    out_file.close()
