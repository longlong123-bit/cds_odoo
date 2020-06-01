odoo.define('Invoice.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        _advancedSearch: {
            template: 'invoice.advanced_search',
            model: 'account.move'
        }
    });
});
