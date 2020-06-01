odoo.define('Invoice.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'account.move': {
                template: 'invoice.advanced_search'
            }
        })
    });
});
