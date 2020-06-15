odoo.define('Quotation.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'sale.order': {
                'sale.order.custom.tree': {template: 'quotation.advanced_search'},
                'quotation_confirm': {template: 'quotation_confirm.advanced_search'}
            }
        })
    });
});
