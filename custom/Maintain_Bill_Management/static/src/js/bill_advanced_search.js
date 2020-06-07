odoo.define('bill.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'res.partner': {
                template: 'bill.advanced_search'
            }
        })
    });
});