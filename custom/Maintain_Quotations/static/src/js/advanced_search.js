odoo.define('Quotation.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'sale.order': {
                template: 'quotation.advanced_search'
            }
        })
    });
});
