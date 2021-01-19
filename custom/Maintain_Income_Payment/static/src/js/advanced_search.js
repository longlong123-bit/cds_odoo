odoo.define('Income_Payment.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'account.payment': {
                'account.payment.custom.tree.in.payment': {template: 'Income_Payment.advanced_search'},
                template: 'dialog.advanced_search',
            },
            'many.payment': {
                template: 'many_payment.advanced_search'
            }

//            'sale.order': {
//                'sale.order.custom.tree': {template: 'quotation.advanced_search'},
//                'quotation_confirm': {template: 'quotation_confirm.advanced_search'}
//            }
        })
    });
});
