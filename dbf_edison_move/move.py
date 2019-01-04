# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from dbfread import DBF
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class DbfStockCause(orm.Model):
    """ Model name: Dbf Stock picking
    """
    
    _name = 'dbf.stock.cause'
    _description = 'DBF Stock Cause'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'code': fields.char('Code', size=64, required=True),
        'name': fields.char('Name', size=64, required=True),
        }

class DbfStockPicking(orm.Model):
    """ Model name: Dbf Stock picking
    """
    
    _name = 'dbf.stock.picking'
    _description = 'DBF Stock Picking'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'document_date': fields.date('Document date'),
        'insert_date': fields.date('Insert date'),
        'partner_id': fields.many2one(
            'res.partner', 'Supplier'),
        }

class DbfStockMove(orm.Model):
    """ Model name: Dbf Stock Move
    """
    
    _name = 'dbf.stock.move'
    _description = 'DBF Stock Move'
    _rec_name = 'product_id'
    
    _columns = {
        # Foreign keys:
        'cause_id': fields.many2one(
            'dbf.stock.cause', 'Cause'),
        'product_id': fields.many2one(
            'product.product', 'Product'),
        'account_id': fields.many2one(
            'account.analytic.account', 'Analytic account'),
        'supplier_id': fields.many2one(
            'res.partner', 'Supplier'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner'),
        'picking_id': fields.many2one(
            'dbf.stock.picking', 'Picking'),

        # Foreing name (used to create external ID):
        'cause_name': fields.char('Cause code', size=6),
        'metel_code': fields.char('Metel code', size=6),
        'account_name': fields.char('Account name', size=6),
        'pickin_name': fields.char('Account name', size=6),

        # Mode data:
        'document_date': fields.date('Document date'),
        'product_qty': fields.float('Qty', digits=(16, 2)),
        'standard_price': fields.float('Price', digits=(16, 2)),
        'listprice': fields.float('List Price', digits=(16, 2)),
        'supplier_code': fields.char('Supplier code', size=6),
        'uom': fields.char('UOM', size=6),
        'note': fields.text('Note'),
        }

    def schedule_dbf_edison_move_import(self, cr, uid, 
            verbose_log_count=100, log_name='move.log',
            context=None):
        ''' Import stock move from external DBF
        '''
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        # Pool used:
        company_pool = self.pool.get('res.company')
        cause_pool = self.pool.get('dbf.stock.cause')
        product_pool = self.pool.get('product.product')
        analytic_pool = self.pool.get('account.analytic.account')
        partner_pool = self.pool.get('res.partner')
        picking_pool = self.pool.get('dbf.stock.picking')
        
        # Log:
        log_file = company_pool.get_dbf_logfile(
            cr, uid, log_name, context=context)
        log = company_pool.get_dbf_logevent
        log(log_file, _('Start import product'), mode='INFO')

        # ---------------------------------------------------------------------
        # Mapping:
        # ---------------------------------------------------------------------
        db_name = 'TBDEBO.DBF'

        i = 0
        # Error database:
        history_db = {
            'product': {},
            'analytic': {},
            'supplier': {},
            'partner': {},
            'picking': {},         
            }

        # Clean all previous database:
        _logger.info('Delete all movement:')
        cr.execute('DELETE from dbf_stock_move;')
        
        # TODO manage last price update   
        for record in company_pool.get_dbf_table(
                cr, uid, db_name, context=context):
            i += 1

            # -----------------------------------------------------------------    
            # Field:
            # -----------------------------------------------------------------    
            document_date = record['DDATDOCU'] #, datetime.date(2007, 9, 7)), 
            default_code = record['CCODARTI'] #, u'3FF11746'), 
            supplier_code = record['CCODFORN'] #, u'000001'), 
            picking_name = record['CRIFDOCU'] #, u'882909'), 
            cause_name = record['CCODCATR'] #, u'10'), 
            uom = record['CCODUNMI'] #, u'NR'), 
            product_qty = record['NQTAARTI'] #, 2.0), 
            pricelist = record['NPREZZO'] #, 0.0), 
            standard_price = record['NPREZZOCS'] #, 66.38), 
            supplier_code_2 = record['CCODFOR2'] #, u'000761'), 
            account_name = record['CCODCANT']
            note = record['MMEMO']
            
            # -----------------------------------------------------------------
            # Check foreing elements:    
            # -----------------------------------------------------------------
            # TODO Product reference:
            product_id = False

            # TODO Supplier reference:
            supplier_id = False

            # TODO Partner reference:
            partner_id = False

            # TODO Account reference:
            account_id = False

            # TODO If picking_name: create picking document:
            picking_id = False
            if picking_name:
                #if (supplier_code, picking_code) 
                # TODO picking_id
                pass
                
            # TODO Cause reference:
            if cause_name and cause_name not in history_db['cause']:
                history_db['cause'][cause_name] = cause_pool.create(cr, uid, {
                    'code': cause_name,
                    'name': cause_name,
                    }, context=context)
            cause_id = history_db['cause'].get(cause_name, False)
            
                
            # -----------------------------------------------------------------
            # Primary record:
            # -----------------------------------------------------------------
            data = {
                # Foreign reference:
                'cause_id': cause_id,
                'product_id': product_id,
                'supplier_id': supplier_id,
                'partner_id': partner_id,
                'account_id': account_id,
                'picking_id': picking_id,
                
                'document_date': document_date,
                'metel_code': default_code,
                'supplier_code': supplier_code,
                'picking_name': picking_name,
                'cause_name': cause_name,
                'uom': uom,
                'product_qty': product_qty,
                'pricelist': pricelist,
                'standard_price': standard_price,
                #'supplier_code_2': supplier_code_2,
                'account_name': account_name,
                'note': note,
                }
            self.create(cr, uid, data, context=context)
            print data # TODO remove

            #record['CANNBOLL']
            #record['CNBOLLET']
            #record['CNUMBOLL']
            #record['DDATCOMA'] #, datetime.date(2007, 9, 7)), 
            #record['CFSCARTI']#, u'S'), 
            #record['CCODPROG']
            #record['CCODORDI']
            #record['CCODCECO']
            #record['CCODSOFA']
            #record['CRIFPREV']
            #record['CTLIARTI']
            #record['CFASCIA']
            #record['CRIFFATT']
            #record['CRIFRAPP']
            #record['CRIFORCL']
            #record['LPRZSCON']#, False), 
            #record['CCODPERS']
            #record['CCONTORI']
            #record['CCODSOCO']
            #record['CCODPROGC']
            #record['NRICARIC']#, 0.0), 
            #record['NPREZZOL']#, 0.0), 
            #record['CTIPPREZ']
            #record['CFILLER']
            #record['CFILLER1']
            #record['CLOTFABB']]
            #record['NPREZZOV']#, 0.0), 
            #record['CCODPRODFO']
            #record['NPROVVIG']#, 0.0), 
            #record['CCODCLAS']
            #record['CCODARCO']
            #record['CCODDEPO']
            #record['CTIPVEND']
            #record['NQTAPEZZ']#, 0.0), 
            #record['DDATOPER']#, None), 
            #record['CORAOPER']
            #record['CCODUTEN']
            #record['CCODOPER']
            #record['NSTSINCR']#, 0), 
            #record['CFILEPDF']
            #record['CCANTCOR']
            #record['MNOTEMAN']#, None)])
            
            '''
            # Metel producer code information:
            if metel_producer_code not in producer_db:
                producer_db[metel_producer_code] = \
                    category_pool.get_create_producer_group(
                        cr, uid, metel_producer_code, metel_producer_code,
                        context=context)

            if verbose_log_count and i % verbose_log_count == 0:
                _logger.info(_('Import product #: %s') % i)
            
            # Search product code:
            product_ids = self.search(cr, uid, [
                ('default_code', '=', default_code),
                ('metel_producer_code', '=', metel_producer_code),
                ], context=context)
            if len(product_ids) > 1:
                log(
                    log_file, 
                    _('More than one product: %s (take last)') % default_code, 
                    mode='ERROR',
                    )
                product_ids = [product_ids[0]]

            if product_ids:
                try:
                    self.write(cr, uid, product_ids, data, context=context)
                except:
                    del(data['ean13'])   
                    log(
                        log_file, _('Error EAN number: %s') % ean13, 
                        mode='ERROR',
                        )
                    self.write(cr, uid, product_ids, data, context=context)
            else:
                try:
                    self.create(cr, uid, data, context=context)
                except:
                    del(data['ean13'])    
                    log(
                        log_file, _('Error EAN number: %s') % ean13, 
                        mode='ERROR',
                        )
                    self.create(cr, uid, data, context=context)'''
        log(
            log_file, 
            _('End import. Tot: %s\n') % i,
            mode='INFO',
            )
        
        try:
            log_file.close()
        except:
            return False    
        return True        
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
