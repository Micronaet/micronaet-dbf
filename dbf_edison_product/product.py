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


class ProductProduct(orm.Model):
    """ Model name: Product product
    """
    
    _inherit = 'product.product'
    
    def schedule_dbf_edison_product_import(self, cr, uid, 
            verbose_log_count=100, log_name='product.log', mode='product',
            context=None):
        ''' Import product from external DBF
            mode: product (only product.product), mirror (only mirror), 
                  all (both)
        '''
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        # Browse company: 
        company_pool = self.pool.get('res.company')
        category_pool = self.pool.get('product.category')
        mirror_pool = self.pool.get('dbf.product.product')
        
        # Log:
        log_file = company_pool.get_dbf_logfile(
            cr, uid, log_name, context=context)
        log = company_pool.get_dbf_logevent
        log(log_file, _('Start import product'), mode='INFO')

        # ---------------------------------------------------------------------
        # Mapping:
        # ---------------------------------------------------------------------
        db_name = 'ARTICO.DBF'
        
        i = 0
        producer_db = {}
        for record in company_pool.get_dbf_table(
                cr, uid, db_name, context=context):
            i += 1

            # -----------------------------------------------------------------    
            # Field:
            # -----------------------------------------------------------------    
            metel_producer_code = record['CCODPROD']
            default_code = record['CCODARTI']
            name = record['CDESARTI']
            ean13 = record['CCODARPR']            

            if verbose_log_count and i % verbose_log_count == 0:
                _logger.info(_('Import product #: %s') % i)
                
            # -----------------------------------------------------------------
            # Update mirror table:
            # -----------------------------------------------------------------
            if mode in ('mirror' or 'all'):
                mirror_ids = mirror_pool.search(cr, uid, [
                    ('default_code', '=', default_code),
                    ], context=context)
                mirror_data = {
                    'default_code': default_code,
                    'name': name,
                    'standard_price': record['NPREZZOP'],
                    'description': record['MMEMO'],
                    'metel_producer_code': metel_producer_code,
                    #'product_id': False, # TODO
                    }    
                if mirror_ids:
                    mirror_pool.write(
                        cr, uid, mirror_ids, mirror_data, context=context)
                else:    
                    mirror_pool.create(
                        cr, uid, mirror_data, context=context)
                        
            if mode == 'mirror':
                continue # no more update!
            # -----------------------------------------------------------------
            
            # Metel producer code information:
            metel_producer_code = '%s-' % metel_producer_code
            if metel_producer_code not in producer_db:
                producer_db[metel_producer_code] = \
                    category_pool.get_create_producer_group(
                        cr, uid, metel_producer_code, metel_producer_code,
                        context=context)
                        
            if len(metel_producer_code or '') >=3 or default_code[2:3] != '-':
                continue

            # Mapping fields:
            data = {
                'dbf_import': True,
                'default_code': default_code,
                'name': name,
                #'CCODFORN' #'CCODPROD'
                'ean13': ean13,
                #'CCODCLAS' #'CCODCLA2'
                # record['NPREZZO1'],
                #'NPREZZO2' 'NPREZZO3' 'NPREZZO4' 'NPREZZOX' 
                'lst_price': record['NPREZZOP'],
                #'LARTPROD' #'CPREZZO1' #'CPREZZO2' 'CPREZZO3' 'CPREZZO4'
                # PCE 'CCODUNMI' # 22 'CCODCIVA'
                #'NMINFORF' #'NMINCALC' #'NPREZZOM' #'NMINFASA' #'NMINFASB' 
                #'CPRSCONT' #'CPREXTRA'
                #'NQTACONF' #'CSTATO' #'NDISPO' #'DDATUACQ' #'NRAPCONV' 
                #'CORDFORN' #'CCODCAVE'
                #'CCODALTE' #'CCODPREL' #'NQTASCMI' #'NQTASCMA' #'NQTALORI' 
                #'LFORNAB'
                #'CCODSERI' #'LARBSMAX' #'CCODCLIE' #'CMODELLO' #'CSOTTOTI' 
                #'CCODLAVO' #'CCODPREV'
                'description': record['MMEMO'],
                
                #'metel_electrocod':
                'metel_producer_code': metel_producer_code,
                'metel_producer_id': producer_db[metel_producer_code],
                }
                
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
                    self.create(cr, uid, data, context=context)
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
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
